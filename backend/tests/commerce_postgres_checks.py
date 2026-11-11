"""Integración SQL real en un PostgreSQL LOCAL aislado; no usa .env ni Supabase remoto.

uv run --no-project --with 'psycopg[binary]' python backend/tests/commerce_postgres_checks.py
El archivo tmp/commerce-test-db.json debe apuntar a una instancia temporal de pruebas.
"""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import psycopg
from psycopg.types.json import Jsonb

ROOT=Path(__file__).resolve().parents[2]
config=json.loads((ROOT/'tmp/commerce-test-db.json').read_text(encoding='utf-8-sig'))
if not str(Path(config['folder']).resolve()).startswith(str((ROOT/'tmp').resolve())):
    raise RuntimeError('Solo se permiten instancias temporales dentro de tmp')
CONN=dict(host='127.0.0.1',port=config['port'],user='postgres',dbname='postgres')

bootstrap="""
create role anon nologin;
create role authenticated nologin;
create role service_role nologin bypassrls;
create schema auth;
create schema storage;
create table auth.users(id uuid primary key,email text,raw_user_meta_data jsonb default '{}'::jsonb);
create function auth.uid() returns uuid language sql stable as $$
 select (nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'sub')::uuid;
$$;
grant usage on schema auth to anon,authenticated,service_role;
grant execute on function auth.uid() to anon,authenticated,service_role;
create table storage.buckets(id text primary key,name text,public boolean,file_size_limit bigint,allowed_mime_types text[]);
create table storage.objects(id uuid primary key default gen_random_uuid(),bucket_id text references storage.buckets(id),name text not null);
create function storage.foldername(name text) returns text[] language sql immutable as $$
 select case when array_length(string_to_array(name,'/'),1)>1
   then (string_to_array(name,'/'))[1:array_length(string_to_array(name,'/'),1)-1]
   else array[]::text[] end;
$$;
"""


def rpc(connection,name,*args):
    placeholders=','.join(['%s']*len(args))
    return connection.execute('select public.'+name+'('+placeholders+')',args).fetchone()[0]


def check_error(connection,code,fn):
    try:
        with connection.transaction():fn()
    except psycopg.Error as error:
        assert error.sqlstate==code,(error.sqlstate,str(error))
    else:raise AssertionError('Se esperaba rechazo '+code)


with psycopg.connect(**CONN,autocommit=True) as c:
    if not c.execute("select to_regclass('auth.users')").fetchone()[0]:
        c.execute(bootstrap)
        c.execute((ROOT/'supabase/neifit_completo_base_nueva.sql').read_text(encoding='utf-8'))
    c.execute((ROOT/'supabase/migrations/0005_servicios_comerciales.sql').read_text(encoding='utf-8'))
    # La migración también debe poder aplicarse por segunda vez sin cambiar datos.
    c.execute((ROOT/'supabase/migrations/0005_servicios_comerciales.sql').read_text(encoding='utf-8'))
    c.execute((ROOT/'supabase/migrations/0007_cotizaciones_avisos_cobros.sql').read_text(encoding='utf-8'))
    admin,owner,other,courier=[uuid4() for _ in range(4)]
    for uid in [admin,owner,other,courier]:
        c.execute('insert into auth.users(id,email) values(%s,%s)',(uid,str(uid)+'@example.test'))
    c.execute("update public.profiles set role='admin' where id=%s",(admin,))
    c.execute("update public.profiles set role='mensajeria' where id=%s",(courier,))
    cat=c.execute("select id from public.categories where slug='postres'").fetchone()[0]
    product=rpc(c,'neifit_save_product',admin,Jsonb({'name':'Producto de integración','slug':'prueba-'+str(uuid4()),'category_id':str(cat),'price':12500,'stock':5,'featured':True}),None)
    pid=product['id']
    data={'customer_name':'Cliente prueba','customer_phone':'3001234567','customer_email':'test@example.test',
          'address':'Direccion de prueba','payment_method':'contraentrega','subtotal':1,'shipping_cost':0,'total':1,
          'items':[{'product_id':pid,'quantity':2,'unit_price':1,'subtotal':1}]}
    request=uuid4()
    order=rpc(c,'neifit_create_document',owner,'order',request,Jsonb(data))
    assert order['subtotal']==25000 and order['total']==30000 and order['shipping_cost']==5000
    assert order['payment_status']=='pendiente'
    assert c.execute('select stock from public.products where id=%s',(pid,)).fetchone()[0]==3
    assert rpc(c,'neifit_create_document',owner,'order',request,Jsonb(data))['id']==order['id']
    assert c.execute('select stock from public.products where id=%s',(pid,)).fetchone()[0]==3
    assert len(rpc(c,'neifit_read_orders',admin,None,None))>=1
    assert rpc(c,'neifit_read_orders',other,None,order['order_number'])==[]
    assert rpc(c,'neifit_read_orders',owner,None,order['order_number'])[0]['id']==order['id']
    check_error(c,'23505',lambda:rpc(c,'neifit_create_document',owner,'order',request,Jsonb({**data,'notes':'Otro contenido'})))
    original_count=c.execute('select count(*) from public.orders').fetchone()[0]
    check_error(c,'P0001',lambda:rpc(c,'neifit_create_document',owner,'order',uuid4(),Jsonb({**data,'items':[{'product_id':pid,'quantity':4}]})))
    assert c.execute('select count(*) from public.orders').fetchone()[0]==original_count
    assert c.execute('select stock from public.products where id=%s',(pid,)).fetchone()[0]==3
    quote=rpc(c,'neifit_create_document',owner,'quote',uuid4(),Jsonb(data))
    assert quote['items'][0]['reference_price']==12500
    assert any(q['id']==quote['id'] for q in rpc(c,'neifit_read_quotes',admin))
    assert rpc(c,'neifit_read_quotes',other)==[]
    assert c.execute('select stock from public.products where id=%s',(pid,)).fetchone()[0]==3
    quote=rpc(c,'neifit_update_quote',admin,quote['id'],'respondida')
    assert quote['status']=='respondida'
    check_error(c,'42501',lambda:rpc(c,'neifit_respond_quote',other,quote['id'],Decimal('30000'),'Incluye domicilio y entrega coordinada',datetime.now(timezone.utc)+timedelta(days=2)))
    offered=rpc(c,'neifit_respond_quote',admin,quote['id'],Decimal('30000'),'Incluye domicilio y entrega coordinada',datetime.now(timezone.utc)+timedelta(days=2))
    assert offered['offered_total']==30000 and offered['offer_conditions']=='Incluye domicilio y entrega coordinada'
    check_error(c,'42501',lambda:rpc(c,'neifit_update_quote',owner,quote['id'],'aceptada'))
    # Una actualización de stock desde un formulario obsoleto se rechaza.
    check_error(c,'P0001',lambda:rpc(c,'neifit_save_product',admin,Jsonb({'stock':99,'expected_updated_at':product['updated_at']}),pid))
    # Cancelar devuelve unidades exactamente una vez.
    rpc(c,'neifit_update_order',admin,order['id'],'cancelado','Cancelación de prueba')
    rpc(c,'neifit_update_order',admin,order['id'],'cancelado','Reintento')
    assert c.execute('select stock from public.products where id=%s',(pid,)).fetchone()[0]==5
    # Otro pedido recorre la entrega con autorización, estados y trazabilidad.
    delivery=rpc(c,'neifit_create_document',owner,'order',uuid4(),Jsonb(data))
    check_error(c,'P0002',lambda:rpc(c,'neifit_update_order',courier,delivery['id'],'en_ruta',''))
    rpc(c,'neifit_assign_delivery',admin,delivery['id'],courier)
    rpc(c,'neifit_update_order',admin,delivery['id'],'en_preparacion','')
    for state in ['en_ruta','entregado']:
        result=rpc(c,'neifit_update_order',courier,delivery['id'],state,'')
    assert result['order_status']=='entregado' and len(result['tracking_history'])==5
    # Cobro contraentrega: exclusivo del administrador, importe exacto, una sola vez.
    cash_amount=Decimal(str(delivery['total']))
    check_error(c,'42501',lambda:rpc(c,'neifit_confirm_cash',courier,delivery['id'],cash_amount,'REC-001'))
    check_error(c,'22023',lambda:rpc(c,'neifit_confirm_cash',admin,delivery['id'],1,'REC-001'))
    paid=rpc(c,'neifit_confirm_cash',admin,delivery['id'],cash_amount,'REC-001')
    assert paid['payment_status']=='aprobado'
    assert paid['is_simulated'] is False
    rpc(c,'neifit_confirm_cash',admin,delivery['id'],cash_amount,'REC-001')
    assert c.execute("select count(*) from public.payment_transactions where order_id=%s and provider='contraentrega_manual'",(delivery['id'],)).fetchone()[0]==1
    # Avisos ligados a la transacción y aislamiento de direcciones/avisos.
    assert c.execute('select count(*) from public.notifications where user_id=%s',(owner,)).fetchone()[0]>0
    address_id=c.execute("insert into public.customer_addresses(user_id,label,address,city,recipient,phone) values(%s,'Casa','Calle 10 # 20-30','Medellín','Cliente','3000000000') returning id",(owner,)).fetchone()[0]
    c.execute('set role authenticated')
    c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':str(other),'role':'authenticated'}),))
    assert c.execute('select count(*) from public.customer_addresses').fetchone()[0]==0
    assert c.execute('select count(*) from public.notifications').fetchone()[0]==0
    c.execute('reset role')
    check_error(c,'P0001',lambda:rpc(c,'neifit_update_order',admin,delivery['id'],'cancelado',''))
    # Dos compras concurrentes no pueden consumir la última unidad dos veces.
    current=rpc(c,'neifit_product_json',pid)
    rpc(c,'neifit_save_product',admin,Jsonb({'stock':1,'expected_updated_at':current['updated_at']}),pid)
    def buy_one(_):
        try:
            with psycopg.connect(**CONN,autocommit=True) as conn:
                rpc(conn,'neifit_create_document',owner,'order',uuid4(),Jsonb({**data,'items':[{'product_id':pid,'quantity':1}]}))
            return 'ok'
        except psycopg.Error as error:return error.sqlstate
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(buy_one,range(2)))
    assert sorted(results)==['P0001','ok'],results
    assert c.execute('select stock from public.products where id=%s',(pid,)).fetchone()[0]==0
    # Los roles del navegador no pueden llamar RPC ni escribir pedidos.
    for role in ['anon','authenticated']:
        assert not c.execute("select has_function_privilege(%s,'public.neifit_create_document(uuid,text,uuid,jsonb)','EXECUTE')",(role,)).fetchone()[0]
        assert not c.execute("select has_table_privilege(%s,'public.orders','INSERT')",(role,)).fetchone()[0]
    # Aislamiento RLS real con dos identidades.
    c.execute('set role authenticated')
    c.execute("select set_config('request.jwt.claims',%s,false)",(json.dumps({'sub':str(other),'role':'authenticated'}),))
    assert c.execute('select count(*) from public.orders').fetchone()[0]==0
    c.execute('reset role')
print('OK PostgreSQL real: importes de servidor, stock, idempotencia, rollback, cotizaciones, estados, mensajería, cancelación, concurrencia y RLS.')
