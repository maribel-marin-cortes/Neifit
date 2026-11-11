"""Crea o promueve administradores de una empresa sin guardar contraseñas.

Las identidades faltantes solicitan la clave mediante ``getpass``. Las existentes
solo actualizan perfil y membresía. No concede roles de PostgreSQL.
"""
import argparse
import asyncio
from getpass import getpass
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from dotenv import load_dotenv
load_dotenv(ROOT / 'backend/.env', override=True)
os.environ['DEBUG'] = 'true'

import httpx
from app.core.config import settings
from app.core.supabase_headers import service_headers
from app.core.supabase_rest import supabase_rest as db


def usuario(value):
    parts = [part.strip() for part in value.split('|')]
    if len(parts) != 3 or not all(parts):
        raise argparse.ArgumentTypeError('Usa NOMBRE|CORREO|TELEFONO')
    return {'nombre': parts[0], 'correo': parts[1].lower(), 'telefono': parts[2]}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--empresa', default='neifit')
    parser.add_argument('--usuario', action='append', type=usuario, required=True)
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args()
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError('Supabase no está configurado en backend/.env')

    async with httpx.AsyncClient(timeout=30) as client:
        db.client = client
        empresas = await db.rows('empresas', {'slug':'eq.' + args.empresa,
            'estado':'eq.activa','select':'id,slug'})
        if len(empresas) != 1:
            raise RuntimeError('Empresa activa no encontrada: ' + args.empresa)
        empresa_id = empresas[0]['id']
        encontrados = {}
        for item in args.usuario:
            rows = await db.rows('perfiles', {'correo':'eq.' + item['correo'],
                'select':'id,correo,nombre_completo,telefono'})
            if len(rows) > 1:
                raise RuntimeError('Correo duplicado: ' + item['correo'])
            encontrados[item['correo']] = rows[0] if rows else None
            print(item['correo'] + ': ' + ('existente' if rows else 'se crearía'))
        if not args.aplicar:
            print('Comprobación terminada. No se modificó ningún usuario.')
            return

        passwords = {}
        for item in args.usuario:
            if encontrados[item['correo']] is None:
                password = getpass('Contraseña temporal para ' + item['correo'] + ': ')
                if not 8 <= len(password) <= 128:
                    raise RuntimeError('La contraseña debe tener entre 8 y 128 caracteres')
                passwords[item['correo']] = password

        for item in args.usuario:
            profile = encontrados[item['correo']]
            if profile is None:
                response = await client.post(settings.SUPABASE_URL.rstrip('/') + '/auth/v1/admin/users',
                    headers=service_headers(settings.SUPABASE_SERVICE_ROLE_KEY), json={
                    'email':item['correo'],'password':passwords[item['correo']],
                    'email_confirm':True,'user_metadata':{'nombre_completo':item['nombre'],
                    'full_name':item['nombre'],'telefono':item['telefono'],'phone':item['telefono']}})
                response.raise_for_status()
                user_id = response.json()['id']
            else:
                user_id = profile['id']
            await db.request('PATCH','perfiles',params={'id':'eq.' + user_id},data={
                'nombre_completo':item['nombre'],'telefono':item['telefono'],'rol':'admin'})
            await db.request('POST','miembros_empresa',params={'on_conflict':'empresa_id,usuario_id'},
                data={'empresa_id':empresa_id,'usuario_id':user_id,'rol':'admin','estado':'activo'},
                headers={'Prefer':'resolution=merge-duplicates'})
            print(item['correo'] + ': administrador de ' + args.empresa)
        db.client = None


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as error:
        from fastapi import HTTPException
        print('Proceso detenido:', error.detail if isinstance(error,HTTPException) else str(error))
        raise SystemExit(1)
