"""Datos ficticios autorizados para practicar consultas. No envía correos ni pagos.

Sin --aplicar solo muestra lo que se cargaría. Una segunda ejecución no repone
stock ni duplica documentos: se utilizan slugs propios y request_id estables.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from uuid import uuid5, NAMESPACE_URL

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'backend/.env',override=True)
os.environ['DEBUG']='true'
import httpx
from app.core.supabase_rest import supabase_rest as db

DATA=[
 ('Postre de Maracuyá','postre-maracuya','postres',12500,12,'postre-maracuya'),
 ('Mousse de Mango','mousse-mango','postres',13000,10,'mousse-mango'),
 ('Postre de Fresa','postre-fresa','postres',13500,8,'postre-fresa'),
 ('Postre de Melocotón','postre-melocoton','postres',12800,6,'postre-melocoton'),
 ('Postre de Chontaduro','postre-chontaduro','postres',14500,3,'torta-chontaduro'),
 ('Postre Regional','postre-regional','postres',14000,0,'postre-regional'),
 ('Cocadas','cocadas','snacks',8500,15,'cocadas'),
 ('Dátiles con Crema de Maní','datiles-mani','snacks',11000,12,'datiles-mani'),
 ('Maní Tostado','mani-tostado','snacks',6000,3,'mani-tostado'),
 ('Mix de Frutos Secos','mix-frutos-secos','snacks',12000,10,'mix-frutos-secos'),
 ('Bebida Tropical 1','bebida-tropical-1','bebidas',22000,8,'bebidas-ilustrativas'),
 ('Bebida Tropical 2','bebida-tropical-2','bebidas',24000,6,'bebidas-ilustrativas'),
 ('Bebida Tropical 3','bebida-tropical-3','bebidas',25000,5,'bebidas-ilustrativas'),
]

DESCRIPTIONS={
 'postre-maracuya':'Postre de maracuyá de la selección Neifit.',
 'mousse-mango':'Mousse de mango de nuestra selección de postres.',
 'postre-fresa':'Postre de fresa para acompañar tus momentos especiales.',
 'postre-melocoton':'Postre de melocotón de la selección Neifit.',
 'postre-chontaduro':'Postre de chontaduro de nuestra selección de sabores tropicales.',
 'postre-regional':'Una opción de nuestra selección de postres regionales.',
 'cocadas':'Cocadas de la selección de snacks Neifit.',
 'datiles-mani':'Dátiles con crema de maní de nuestra selección de snacks.',
 'mani-tostado':'Maní tostado para disfrutar como snack.',
 'mix-frutos-secos':'Mix de frutos secos para acompañar tus momentos del día.',
 'bebida-tropical-1':'Bebida de la selección tropical Neifit.',
 'bebida-tropical-2':'Otra opción de nuestra selección de bebidas tropicales.',
 'bebida-tropical-3':'Bebida para acompañar tus postres y snacks favoritos.',
}


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--aplicar',action='store_true')
    parser.add_argument('--administrador',help='Correo de la cuenta administradora autorizada para los ejemplos')
    args=parser.parse_args()
    if not args.aplicar:
        print('PREVISUALIZACIÓN: 13 productos, 3 cotizaciones y 3 pedidos ficticios. Todos los pagos pendientes.')
        for name,slug,category,price,stock,image in DATA:print(f'{name} | {category} | {price} COP | stock inicial {stock} (datos ficticios)')
        return
    if not args.administrador:
        parser.error('--aplicar requiere --administrador con el correo de la cuenta autorizada')
    result={'tipo':'Datos inventados autorizados para consultas; los escenarios adicionales se identifican en payment_transactions.','productos':[],'cotizaciones':[],'pedidos':[]}
    async with httpx.AsyncClient(timeout=30) as client:
        db.client=client
        profiles=await db.rows('profiles',{'select':'id,role','email':'eq.'+args.administrador.strip().lower()})
        if len(profiles)!=1 or profiles[0]['role']!='admin':
            raise RuntimeError('No se encontró la cuenta administradora autorizada. No se cambian roles.')
        actor=profiles[0]['id']
        categories={row['slug']:row['id'] for row in await db.rows('categories',{'select':'id,slug','is_active':'eq.true'})}
        if not {'postres','snacks','bebidas'}.issubset(categories):
            raise RuntimeError('Faltan las categorías activas de Neifit')
        products={}
        for index,(name,slug,category,price,stock,image) in enumerate(DATA):
            slug='prueba-'+slug
            existing=await db.rows('products',{'select':'id,name,description,price,stock','slug':'eq.'+slug})
            if existing:
                description=existing[0].get('description') or ''
                if not (description.startswith('DATOS FICTICIOS') or description==DESCRIPTIONS[slug.removeprefix('prueba-')]):
                    raise RuntimeError('El slug ya pertenece a un producto sin etiqueta de prueba: '+slug)
                row=existing[0]
            else:
                row=await db.rpc('neifit_save_product',p_actor=actor,p_id=None,p_data={
                    'name':name,'slug':slug,'category_id':categories[category],
                    'description':DESCRIPTIONS[slug.removeprefix('prueba-')],
                    'price':price,'stock':stock,'is_active':True,'is_available':True,'featured':index<3,
                    'image_url':'/images/'+image+'.png'})
            products[slug.removeprefix('prueba-')]=row['id']
            result['productos'].append({'id':row['id'],'nombre':row['name'],'precio':row['price']})
        customer={'customer_name':'Cliente de prueba — consultas','customer_phone':'0000000000',
                  'customer_email':'consultas@example.invalid','notes':'PRUEBA: datos ficticios autorizados para consultas. No representa una solicitud real. No contactar ni despachar.'}
        quote_items=[ [('postre-maracuya',1),('mousse-mango',1),('postre-fresa',1)],
                      [('cocadas',10),('datiles-mani',5)], [('bebida-tropical-1',2),('mix-frutos-secos',2)] ]
        for index,items in enumerate(quote_items,1):
            row=await db.rpc('neifit_create_document',p_actor=actor,p_kind='quote',
                p_request=str(uuid5(NAMESPACE_URL,f'neifit-consultas-v1/{actor}/cotizacion/{index}')),
                p_data={**customer,'items':[{'product_id':products[key],'quantity':quantity} for key,quantity in items]})
            if index==3 and row['status']=='pendiente':
                row=await db.rpc('neifit_update_quote',p_actor=actor,p_id=row['id'],p_status='respondida')
            result['cotizaciones'].append({'id':row['id'],'numero':row['quote_number'],'estado':row['status']})
        order_items=[ [('postre-maracuya',1),('mousse-mango',2)], [('postre-fresa',3)], [('cocadas',5),('datiles-mani',2)] ]
        for index,items in enumerate(order_items,1):
            row=await db.rpc('neifit_create_document',p_actor=actor,p_kind='order',
                p_request=str(uuid5(NAMESPACE_URL,f'neifit-consultas-v1/{actor}/pedido/{index}')),
                p_data={**customer,'address':'DIRECCIÓN DE PRUEBA — No realizar entregas', 'payment_method':'contraentrega',
                        'items':[{'product_id':products[key],'quantity':quantity} for key,quantity in items]})
            # Usar administrador como responsable de la simulación; no crear cuentas ni cambiar roles.
            if index<=2 and not row.get('assigned_delivery_user_id') and row['order_status'] not in ('entregado','cancelado'):
                row=await db.rpc('neifit_assign_delivery',p_actor=actor,p_id=row['id'],p_delivery=actor)
            if index==2:
                if row['order_status']=='recibido':row=await db.rpc('neifit_update_order',p_actor=actor,p_id=row['id'],p_status='confirmado',p_message='PRUEBA: confirmación operativa; el pago continúa pendiente.')
                if row['order_status']=='confirmado':row=await db.rpc('neifit_update_order',p_actor=actor,p_id=row['id'],p_status='en_preparacion',p_message='PRUEBA: estado ilustrativo, no preparar ni despachar.')
            result['pedidos'].append({'id':row['id'],'numero':row['order_number'],'estado':row['order_status'],'pago':row['payment_status'],'total':row['total']})
        ids=[entry['id'] for entry in result['productos']]
        final=await db.rows('products',{'select':'id,name,stock,price','id':'in.('+','.join(ids)+')','order':'name'})
        result['existencias_finales']=final
        (ROOT/'supabase/datos_consulta_creados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'Carga verificada: {len(final)} productos de prueba, {len(result["cotizaciones"])} cotizaciones y {len(result["pedidos"])} pedidos.')
        print('Estados de pago conservados según los documentos existentes. Sin envío de mensajes ni cobros.')
        print('Resumen: supabase/datos_consulta_creados.json')
    db.client=None


if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as error:
        from fastapi import HTTPException
        if isinstance(error,HTTPException):print('Carga detenida:',error.detail)
        else:print('Carga detenida:',type(error).__name__)
        raise SystemExit(1)
