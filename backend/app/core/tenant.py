"""Resolución del comercio activo para cada solicitud."""
from contextvars import ContextVar
from uuid import UUID

from fastapi import Header, HTTPException

from app.core.supabase_rest import database_enabled, supabase_rest as db


DEFAULT_COMPANY_ID = '00000000-0000-0000-0000-000000000001'
_company = ContextVar('neifit_company', default=None)


async def establish_company(x_empresa: str | None = Header(default=None, alias='X-Empresa')) -> dict:
    """Acepta el slug público de la empresa; nunca confía en un UUID del cliente."""
    slug = (x_empresa or 'neifit').strip().lower()
    if not slug or len(slug) > 63:
        raise HTTPException(status_code=400, detail='Empresa inválida')
    if database_enabled():
        rows = await db.rows('empresas', {
            'select': 'id,slug,nombre,estado', 'slug': 'eq.' + slug,
            'estado': 'eq.activa', 'limit': '1',
        })
        if not rows:
            raise HTTPException(status_code=404, detail='Empresa no encontrada')
        company = rows[0]
    else:
        if slug != 'neifit':
            raise HTTPException(status_code=404, detail='Empresa no encontrada')
        company = {'id': DEFAULT_COMPANY_ID, 'slug': 'neifit', 'nombre': 'Neifit', 'estado': 'activa'}
    _company.set(company)
    return company


def current_company() -> dict:
    company = _company.get()
    if not company:
        raise HTTPException(status_code=500, detail='No se estableció el contexto de empresa')
    return company


def current_company_id() -> str:
    return str(UUID(current_company()['id']))
