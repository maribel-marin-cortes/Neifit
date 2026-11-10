"""Diagnóstico de solo lectura; --activar habilita RBAC si TODAS las pruebas pasan.
No imprime claves ni lee datos personales. Ejecutar desde la raíz del proyecto.
"""
import argparse
import asyncio
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from dotenv import dotenv_values, set_key
import httpx
from app.core.supabase_headers import service_headers


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--activar',action='store_true')
    args=parser.parse_args()
    env_path=ROOT/'backend/.env'
    values=dotenv_values(env_path)
    url=(values.get('SUPABASE_URL') or '').rstrip('/')
    key=values.get('SUPABASE_SERVICE_ROLE_KEY') or ''
    if not url or not key:
        print('Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en backend/.env.');return 1
    good=True
    async with httpx.AsyncClient(timeout=20,headers={**service_headers(key),'Prefer':'count=exact'}) as client:
        for table in ['categories','products','profiles','quotes','orders','permissions','access_roles','customer_addresses','notifications']:
            try:
                r=await client.get(url+'/rest/v1/'+table,params={'select':'id' if table not in ('permissions','access_roles') else 'code','limit':'1'})
                ok=r.is_success
                good=good and ok
                count=r.headers.get('content-range','*/?').split('/')[-1]
                print(f'{table}: '+(f'OK ({count} registros)' if ok else f'pendiente o inaccesible (HTTP {r.status_code})'))
            except httpx.HTTPError:
                good=False;print(table+': no se pudo conectar')
        try:
            r=await client.post(url+'/rest/v1/rpc/neifit_read_orders',json={'p_actor':'00000000-0000-0000-0000-000000000000','p_id':None,'p_tracking':None})
            good=good and r.is_success and r.json()==[]
            print('RPC de pedidos: '+('OK' if r.is_success and r.json()==[] else 'falta migración 0005'))
            r=await client.get(url+'/rest/v1/company_settings',params={'select':'shipping_cost','limit':'1'})
            good=good and r.is_success and bool(r.json())
            print('Tarifa de domicilio: '+('OK' if r.is_success else 'falta migración 0005'))
        except (httpx.HTTPError,ValueError):
            good=False;print('No se pudo verificar la migración comercial')
    if good:
        if args.activar:
            set_key(str(env_path),'RBAC_DATABASE_ENABLED','true',quote_mode='never')
            print('RBAC_DATABASE_ENABLED=true guardado. Reinicia el backend.')
        print('Conexión y estructura listas. Si products está vacío, registra productos reales desde Administración.')
        return 0
    print('Ejecuta supabase/activar_servicios_supabase.sql completo en SQL Editor y vuelve a comprobar. No se modificó .env.')
    return 1


if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
