"""Navegador → API FastAPI → funciones PostgreSQL reales, sin cuentas ni BD remotas.

La frontera Auth y transporte REST se sustituye por un adaptador LOCAL de pruebas.
No afirma probar el servicio PostgREST remoto. Requiere Vite en 127.0.0.1:5173.
"""
import json
import os
import sys
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
import psycopg
from psycopg.types.json import Jsonb
from psycopg import sql
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
os.environ['DEBUG']='true'
from fastapi import Depends, HTTPException
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, security
from app.core.config import settings
from app.core.supabase_rest import supabase_rest as rest
from app.services.access_service import access_service

cfg=json.loads((ROOT/'tmp/commerce-test-db.json').read_text(encoding='utf-8-sig'))
assert Path(cfg['folder']).resolve().is_relative_to((ROOT/'tmp').resolve())
c=psycopg.connect(host='127.0.0.1',port=cfg['port'],user='postgres',dbname='postgres',autocommit=True)
users={role:str(uuid4()) for role in ['admin','owner','courier']}
for role,uid in users.items():
    c.execute("insert into auth.users(id,email,raw_user_meta_data) values(%s,%s,%s)",(uid,role+'@example.test',Jsonb({'full_name':role,'phone':'3001234567'})))
    if role!='owner':c.execute('update public.profiles set role=%s where id=%s',('mensajeria' if role=='courier' else role,uid))


def as_dict(row):return json.loads(json.dumps(row,default=str))


def rpc_sync(name,args):
    parameters=[Jsonb(v) if isinstance(v,(dict,list)) else v for v in args.values()]
    query=sql.SQL('select public.{}({})').format(sql.Identifier(name),sql.SQL(',').join(sql.Placeholder() for _ in parameters))
    try:return c.execute(query,parameters).fetchone()[0]
    except psycopg.Error as error:
        raise HTTPException(status_code={'42501':403,'P0002':404,'P0001':409,'23505':409}.get(error.sqlstate,422),detail=error.diag.message_primary) from None


async def rpc(name,**kwargs):return rpc_sync(name,kwargs)


async def rows(resource,params=None):
    params=params or {}
    if resource=='products':
        records=c.execute("select to_jsonb(p)||jsonb_build_object('categories',jsonb_build_object('name',g.name,'slug',g.slug,'is_active',g.is_active)) from public.products p join public.categories g on g.id=p.category_id order by p.created_at desc").fetchall()
    else:
        records=c.execute(sql.SQL('select to_jsonb(t) from public.{} t').format(sql.Identifier(resource))).fetchall()
    result=[as_dict(row[0]) for row in records]
    for key,value in params.items():
        if key in ('select','order','limit','offset'):continue
        if isinstance(value,str) and value.startswith('eq.'):
            desired=value[3:]
            def match(row):
                actual=row.get(key) if '.' not in key else row.get(key.split('.')[0],{}).get(key.split('.')[1])
                return str(actual).lower()==desired.lower()
            result=[row for row in result if match(row)]
    return result


async def rest_request(method, resource, *, params=None, data=None, headers=None):
    assert resource in ('profiles', 'customer_addresses', 'notifications'), resource
    if method == 'GET': return (await rows(resource, params))[:int((params or {}).get('limit', 1000))]
    clauses=[]; values=[]
    for key, value in (params or {}).items():
        if value.startswith('eq.'):
            clauses.append(sql.SQL('{}=%s').format(sql.Identifier(key))); values.append(value[3:])
        elif value == 'is.null': clauses.append(sql.SQL('{} is null').format(sql.Identifier(key)))
    if method == 'POST':
        fields=list(data)
        query=sql.SQL('insert into public.{} ({}) values ({}) returning to_jsonb({}.*)').format(sql.Identifier(resource),sql.SQL(',').join(map(sql.Identifier,fields)),sql.SQL(',').join(sql.Placeholder() for _ in fields),sql.Identifier(resource))
        return [as_dict(c.execute(query,list(data.values())).fetchone()[0])]
    if method == 'PATCH':
        fields=list(data)
        query=sql.SQL('update public.{} set {} where {} returning to_jsonb({}.*)').format(sql.Identifier(resource),sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(key)) for key in fields),sql.SQL(' and ').join(clauses),sql.Identifier(resource))
        return [as_dict(row[0]) for row in c.execute(query,list(data.values())+values).fetchall()]
    raise AssertionError(method)


async def permissions(role):
    if role=='admin':return [row[0] for row in c.execute('select code from public.permissions')]
    return [row[0] for row in c.execute('select permission_code from public.role_permissions where role=%s',(role,))]


async def current_user(credentials=Depends(security)):
    role=credentials.credentials if credentials else 'owner'
    uid=users.get(role,users['owner'])
    row=c.execute('select full_name,role from public.profiles where id=%s',(uid,)).fetchone()
    return {'id':uid,'full_name':row[0],'role':row[1],'email':role+'@example.test','phone':'3001234567','permissions':await permissions(row[1])}


mock="""
export const isSupabaseConfigured=true;export const recoveryLinkHasError=false;export const passwordRecovery=null;
const who=sessionStorage.getItem('test-role')||'admin';
const ids=__IDS__;const session={user:{id:ids[who],email:who+'@example.test'},access_token:who};
export const supabase={auth:{getSession:async()=>({data:{session},error:null}),onAuthStateChange:cb=>({data:{subscription:{unsubscribe(){}}}})}};
""".replace('__IDS__',json.dumps(users))

settings.SUPABASE_URL='https://local-test.invalid';settings.SUPABASE_SERVICE_ROLE_KEY='local-only';settings.RBAC_DATABASE_ENABLED=True
app.dependency_overrides[get_current_user]=current_user
product_name='Producto navegador '+str(uuid4())[:8]
with patch.object(rest,'rpc',rpc),patch.object(rest,'rows',rows),patch.object(rest,'request',rest_request),patch.object(access_service,'permissions_for_role',permissions),sync_playwright() as p:
    client=TestClient(app)
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    page.route('**/src/services/supabaseClient.js*',lambda route:route.fulfill(content_type='application/javascript',body=mock))
    def bridge(route):
        request=route.request;path='/api/v1/'+request.url.split('/api/v1/',1)[1]
        response=client.request(request.method,path,content=request.post_data,headers={'Authorization':request.headers.get('authorization',''),'Content-Type':'application/json'})
        route.fulfill(status=response.status_code,content_type='application/json',body=response.content)
    page.route('**/api/v1/**',bridge)
    page.goto('http://127.0.0.1:5173/admin/productos/nuevo')
    page.get_by_label('Nombre',exact=True).fill(product_name)
    page.get_by_label('Precio COP',exact=True).fill('10000')
    page.get_by_label('Stock',exact=True).fill('10')
    page.get_by_label('Imagen',exact=True).fill('/images/postre-maracuya.png')
    page.get_by_role('button',name='Guardar producto',exact=True).click()
    page.wait_for_url('**/admin?modulo=productos')
    page.get_by_text(product_name,exact=True).wait_for()
    pid=c.execute('select id from public.products where name=%s',(product_name,)).fetchone()[0]
    page.evaluate("sessionStorage.setItem('test-role','owner')")
    page.goto('http://127.0.0.1:5173/mi-cuenta')
    page.get_by_label('Nombre completo',exact=True).fill('Cliente actualizado')
    page.get_by_label('Teléfono',exact=True).fill('3009876543')
    page.get_by_role('button',name='Guardar perfil',exact=True).click()
    page.get_by_text('Perfil guardado.',exact=True).wait_for()
    assert c.execute('select full_name from public.profiles where id=%s',(users['owner'],)).fetchone()[0]=='Cliente actualizado'
    for label,value in [('Nombre de la dirección','Casa'),('Persona que recibe','Cliente actualizado'),('Teléfono de contacto','3009876543'),('Dirección completa','Calle 10 # 20-30'),('Ciudad','Medellín')]:
        page.get_by_label(label,exact=True).fill(value)
    page.get_by_role('button',name='Guardar dirección',exact=True).click()
    page.get_by_text('Dirección guardada.',exact=True).wait_for()
    page.goto('http://127.0.0.1:5173/cotizador')
    page.get_by_role('button',name='Agregar '+product_name+' a la cotización',exact=True).click()
    for key,value in [('customer_name','Cliente navegador'),('customer_phone','3001234567'),('customer_email','owner@example.test')]:
        page.locator('input[name='+key+']').fill(value)
    page.get_by_role('button',name='Solicitar cotización',exact=True).click()
    page.get_by_role('heading',name='¡Cotización enviada!',exact=True).wait_for()
    quote=c.execute('select id,quote_number from public.quotes where user_id=%s order by created_at desc limit 1',(users['owner'],)).fetchone()
    page.goto('http://127.0.0.1:5173/catalogo')
    page.get_by_role('button',name='Agregar '+product_name+' al carrito',exact=True).click()
    page.goto('http://127.0.0.1:5173/checkout')
    page.locator('input[name=full_name]').fill('Cliente navegador')
    page.locator('input[name=phone]').fill('3001234567')
    page.locator('textarea[name=address]').fill('Direccion de prueba del navegador')
    page.get_by_role('button',name='Confirmar pedido',exact=True).click()
    page.get_by_role('heading',name='¡Pedido creado!',exact=True).wait_for()
    order=c.execute('select id,order_number,total,payment_status from public.orders where user_id=%s order by created_at desc limit 1',(users['owner'],)).fetchone()
    assert order[2]==15000 and order[3]=='pendiente'
    assert c.execute('select stock from public.products where id=%s',(pid,)).fetchone()[0]==9
    page.get_by_role('link',name='Rastrear pedido',exact=True).click()
    page.get_by_role('heading',name=order[1],exact=True).wait_for()
    page.reload();page.get_by_role('heading',name=order[1],exact=True).wait_for()
    page.evaluate("sessionStorage.setItem('test-role','admin')")
    page.goto('http://127.0.0.1:5173/admin?modulo=cotizaciones')
    page.locator('.card-cream').filter(has_text=quote[1]).wait_for()
    page.get_by_label('Estado de '+quote[1],exact=True).select_option('respondida')
    page.wait_for_timeout(150)
    assert c.execute('select status from public.quotes where id=%s',(quote[0],)).fetchone()[0]=='respondida'
    quote_card=page.locator('.card-cream').filter(has_text=quote[1])
    quote_card.get_by_label('Total final COP (incluye domicilio e impuestos aplicables)',exact=True).fill('20000')
    quote_card.get_by_label('Condiciones, entrega y forma de pago',exact=True).fill('Incluye entrega coordinada y pago contraentrega.')
    quote_card.get_by_label('Oferta válida hasta',exact=True).fill('2030-12-31T18:00')
    quote_card.get_by_role('button',name='Guardar y avisar al cliente',exact=True).click()
    quote_card.get_by_text('Oferta:',exact=False).wait_for()
    page.goto('http://127.0.0.1:5173/admin?modulo=pedidos')
    card=page.locator('.card-cream').filter(has_text=order[1])
    card.get_by_label('Mensajero asignado').select_option(users['courier'])
    page.wait_for_timeout(150)
    assert str(c.execute('select assigned_delivery_user_id from public.orders where id=%s',(order[0],)).fetchone()[0])==users['courier']
    page.screenshot(path=str(ROOT/'tmp/commerce-persistente.png'),full_page=True)
    assert not errors,errors
    browser.close()
app.dependency_overrides.clear();c.close()
print('OK navegador + API + PostgreSQL local: producto, cotización, pedido, precio real, stock, rastreo tras recarga, estado y asignación.')
