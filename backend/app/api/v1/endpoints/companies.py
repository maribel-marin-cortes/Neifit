from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.security import require_auth, require_platform_superadmin
from typing import Literal
from app.core.supabase_rest import supabase_rest as db

router = APIRouter()


class CompanyCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=3, max_length=100)
    slug: str = Field(min_length=3, max_length=63, pattern=r'^[a-z0-9][a-z0-9-]*[a-z0-9]$')


class CompanyStatus(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: Literal['activa','suspendida','inactiva']


@router.get('/plataforma')
async def platform_companies(_=Depends(require_platform_superadmin)):
    return await db.rows('empresas', {
        'select':'id,nombre,slug,estado,creado_en,actualizado_en,miembros_empresa(count)',
        'order':'creado_en.desc'})


@router.patch('/plataforma/{company_id}/estado')
async def platform_company_status(company_id: str, data: CompanyStatus,
                                  admin=Depends(require_platform_superadmin)):
    from app.core.supabase_rest import uuid_value
    company_id=uuid_value(company_id,'Empresa')
    rows=await db.request('PATCH','empresas',params={'id':'eq.'+company_id},
                          data={'estado':data.status},headers={'Prefer':'return=representation'})
    if not rows:
        from fastapi import HTTPException
        raise HTTPException(status_code=404,detail='Empresa no encontrada')
    return rows[0]


@router.get('/plataforma/auditoria')
async def platform_audit(_=Depends(require_platform_superadmin)):
    return await db.rows('auditoria_acceso', {
        'select':'id,empresa_id,actor_id,accion,objetivo,detalles,creado_en',
        'order':'creado_en.desc','limit':'200'})


@router.get('')
async def my_companies(user=Depends(require_auth)):
    return await db.rows('miembros_empresa', {
        'usuario_id': 'eq.' + user['id'], 'estado': 'eq.activo',
        'select': 'role:rol,company:empresas!inner(id,nombre,slug,estado)',
        'order': 'creado_en',
    })


@router.post('', status_code=201)
async def create_company(data: CompanyCreate, user=Depends(require_auth)):
    return await db.rpc('neifit_crear_empresa', p_actor=user['id'],
                        p_nombre=data.name, p_slug=data.slug)
