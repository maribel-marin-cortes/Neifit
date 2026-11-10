"""Presentación de registros sintéticos previamente autorizados.

Solo modifica los UUID del manifiesto y valida sus request_id deterministas.
Los escenarios de pago se identifican en payment_transactions.raw_response;
no se llama a pasarelas, no se cobran fondos ni se envían notificaciones.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from uuid import NAMESPACE_URL,uuid5

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT/'backend/.env',override=True)
os.environ['DEBUG']='true'
import httpx
from app.core.supabase_rest import supabase_rest as db

CUSTOMERS=[
 {'customer_name':'Camila Torres','customer_phone':'+57 300 000 0101','customer_email':'camila.torres@example.com','address':'Carrera 45 # 12-30, Medellín'},
 {'customer_name':'Mateo Ríos','customer_phone':'+57 300 000 0102','customer_email':'mateo.rios@example.com','address':'Calle 32 # 65-18, Medellín'},
 {'customer_name':'Laura Gómez','customer_phone':'+57 300 000 0103','customer_email':'laura.gomez@example.com','address':'Carrera 70 # 44-25, Medellín'},
]
QUOTE_NOTES=['Cotización para refrigerios de una reunión empresarial.','Solicitud de snacks para compartir en oficina.','Selección de bebidas para un evento interno.']
ORDER_NOTES=['Entregar en recepción.','Confirmar entrega con portería.','Empacar los productos por separado.']


async def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--aplicar',action='store_true')
 parser.add_argument('--administrador')
 args=parser.parse_args()
 if not args.aplicar:
  print('Solo escenarios sintéticos del manifiesto: nombres y direcciones habituales; dos pagos aprobados simulados y uno pendiente.');return
 if not args.administrador:parser.error('Falta --administrador')
 path=ROOT/'supabase/datos_consulta_creados.json'
 manifest=json.loads(path.read_text(encoding='utf-8'))
 async with httpx.AsyncClient(timeout=25) as client:
  db.client=client
  admins=await db.rows('profiles',{'select':'id,role','email':'eq.'+args.administrador.strip().lower()})
  if len(admins)!=1 or admins[0]['role']!='admin':raise RuntimeError('Administrador autorizado no encontrado')
  actor=admins[0]['id']
  # Validar todo el conjunto ANTES de escribir. No tocar documentos ajenos.
  for group,table,kind in [('pedidos','orders','pedido'),('cotizaciones','quotes','cotizacion')]:
   if len(manifest[group])!=3:raise RuntimeError('Manifiesto inesperado')
   for index,entry in enumerate(manifest[group],1):
    rows=await db.rows(table,{'select':'id,user_id,request_id','id':'eq.'+entry['id']})
    expected=str(uuid5(NAMESPACE_URL,f'neifit-consultas-v1/{actor}/{kind}/{index}'))
    if len(rows)!=1 or rows[0]['user_id']!=actor or rows[0]['request_id']!=expected:
     raise RuntimeError('El documento no corresponde al conjunto sintético autorizado')
  for entry in manifest['pedidos']:
   transactions=await db.rows('payment_transactions',{'select':'id,provider','order_id':'eq.'+entry['id']})
   if any(row['provider']!='simulacion_consultas' for row in transactions):
    raise RuntimeError('Existe una transacción de otro proveedor; el escenario no se modifica')
  for index,entry in enumerate(manifest['cotizaciones']):
   customer={key:value for key,value in CUSTOMERS[index].items() if key!='address'}
   await db.request('PATCH','quotes',params={'id':'eq.'+entry['id']},data={**customer,'notes':QUOTE_NOTES[index]})
   entry['cliente']=customer['customer_name']
  for index,entry in enumerate(manifest['pedidos']):
   before=(await db.rows('orders',{'select':'id,total,order_status,assigned_delivery_user_id','id':'eq.'+entry['id']}))[0]
   payment='aprobado' if index<2 else 'pendiente'
   if index<2:
    await db.request('POST','payment_transactions',params={'on_conflict':'provider,provider_reference'},headers={'Prefer':'resolution=ignore-duplicates'},data={
     'order_id':entry['id'],'provider':'simulacion_consultas','provider_reference':'ESCENARIO-'+entry['id'],
     'amount':before['total'],'currency':'COP','status':'aprobado',
     'raw_response':{'source':'datos_inventados_autorizados','simulated':True,'real_funds':False,'purpose':'Presentación de consultas SQL, sin cobro ni webhook real'}})
   await db.request('PATCH','orders',params={'id':'eq.'+entry['id']},data={**CUSTOMERS[index],'notes':ORDER_NOTES[index],
    'payment_status':payment,'payment_method':'transferencia' if index<2 else 'contraentrega'})
   events=await db.rows('order_tracking',{'select':'id,status,message','order_id':'eq.'+entry['id']})
   messages={'recibido':'Pedido recibido.','confirmado':'Pedido confirmado.','en_preparacion':'Productos en preparación.'}
   for event in events:
    if 'PRUEBA' in event['message'].upper():
     await db.request('PATCH','order_tracking',params={'id':'eq.'+event['id']},data={'message':messages.get(event['status'],'Responsable de entrega asignado.')})
   entry.update(cliente=CUSTOMERS[index]['customer_name'],pago=payment,pago_simulado=index<2)
  # Los nombres históricos del conjunto también pierden el prefijo visual.
  for table,fk,group in [('order_items','order_id','pedidos'),('quote_items','quote_id','cotizaciones')]:
   for entry in manifest[group]:
    items=await db.rows(table,{'select':'id,product_name',fk:'eq.'+entry['id']})
    for item in items:
     if item['product_name'].startswith('[PRUEBA] '):
      await db.request('PATCH',table,params={'id':'eq.'+item['id']},data={'product_name':item['product_name'].removeprefix('[PRUEBA] ').strip()})
  # Verificar etiquetas e importes sin alterar existencias ni permisos.
  for group,table in [('pedidos','orders'),('cotizaciones','quotes')]:
   for entry in manifest[group]:
    row=(await db.rows(table,{'select':'*','id':'eq.'+entry['id']}))[0]
    if 'prueba' in ' '.join(str(row.get(key) or '') for key in ['customer_name','address','notes']).lower():
     raise RuntimeError('Quedó una etiqueta visual pendiente')
  manifest['tipo']='Datos inventados autorizados para presentación; dos aprobaciones de pago simuladas, sin fondos reales.'
  manifest['identificacion_interna']='UUID/request_id del conjunto y payment_transactions.raw_response.simulated. No representa operaciones reales.'
  path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 db.client=None
 print('Actualizados: 3 cotizaciones y 3 pedidos. Dos escenarios de pago aprobado identificados internamente como simulados. Sin cobros, cuentas nuevas ni mensajes.')


if __name__=='__main__':
 try:asyncio.run(main())
 except Exception as error:
  from fastapi import HTTPException
  print('Proceso detenido:',error.detail if isinstance(error,HTTPException) else str(error) if isinstance(error,RuntimeError) else type(error).__name__)
  raise SystemExit(1)
