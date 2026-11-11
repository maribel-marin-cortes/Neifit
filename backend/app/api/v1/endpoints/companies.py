from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.security import require_auth
from app.core.supabase_rest import supabase_rest as db

router = APIRouter()


class CompanyCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=3, max_length=100)
    slug: str = Field(min_length=3, max_length=63, pattern=r'^[a-z0-9][a-z0-9-]*[a-z0-9]$')


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
