from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, SecretStr, field_validator
from app.core.security import require_permission, require_admin
from app.core.permissions import ROLE_PERMISSIONS, CUSTOM_ROLE_PERMISSIONS
from app.services.access_service import access_service

router = APIRouter()
Role = Annotated[str, Field(pattern=r'^[a-z][a-z0-9_]{2,39}$')]


class RoleAssignment(BaseModel):
    role: Role


class PermissionAssignment(BaseModel):
    permissions: list[str] = Field(max_length=20)


class NewRole(PermissionAssignment):
    code: Role
    name: str = Field(min_length=3, max_length=60, pattern=r'.*\S.*')


class NewUser(BaseModel):
    full_name: str = Field(min_length=3, max_length=100, pattern=r'.*\S.*')
    email: str = Field(max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    phone: str = Field(min_length=7, max_length=30, pattern=r'^\+?[0-9 ()-]+$')
    password: SecretStr
    role: Role = 'mensajeria'
    email_verified_by_admin: bool

    @field_validator('password')
    @classmethod
    def password_length(cls, value):
        if not 8 <= len(value.get_secret_value()) <= 128:
            raise ValueError('La contraseña debe tener entre 8 y 128 caracteres')
        return value

    @field_validator('email_verified_by_admin')
    @classmethod
    def verified_email(cls, value):
        if not value:
            raise ValueError('El administrador debe verificar el correo de la persona')
        return value


@router.get('/', dependencies=[Depends(require_admin)])
async def configuration(admin=Depends(require_permission('access.manage'))):
    return await access_service.configuration()


@router.put('/roles/{role}/permisos', dependencies=[Depends(require_admin)])
@router.put('/roles/{role}/permissions', dependencies=[Depends(require_admin)], deprecated=True)
async def assign_permissions(role: Role, data: PermissionAssignment, admin=Depends(require_permission('access.manage'))):
    if role == 'admin' or 'profile.read' not in data.permissions or not set(data.permissions).issubset(ROLE_PERMISSIONS.get(role, CUSTOM_ROLE_PERMISSIONS)):
        raise HTTPException(status_code=403, detail='Solo puedes modificar los permisos delegables de cliente y mensajería')
    await access_service.request('POST', 'rpc/neifit_establecer_permisos_rol', json={
        'p_rol': role, 'p_permisos': sorted(set(data.permissions)), 'p_actor_id': admin['id']})
    return {'role': role, 'permissions': sorted(set(data.permissions))}


@router.post('/roles', status_code=201, dependencies=[Depends(require_admin)])
async def create_role(data: NewRole, admin=Depends(require_permission('access.manage'))):
    if data.code in ROLE_PERMISSIONS or 'profile.read' not in data.permissions or not set(data.permissions).issubset(CUSTOM_ROLE_PERMISSIONS):
        raise HTTPException(status_code=403, detail='Nombre reservado o permisos no delegables. Incluye profile.read.')
    await access_service.request('POST', 'rpc/neifit_crear_rol', json={
        'p_actor_id': admin['id'], 'p_codigo': data.code, 'p_nombre': data.name.strip(), 'p_permisos': sorted(set(data.permissions))})
    return {'role': data.code, 'name': data.name.strip()}


@router.post('/usuarios', status_code=201, dependencies=[Depends(require_admin)])
@router.post('/users', status_code=201, dependencies=[Depends(require_admin)], deprecated=True)
async def create_user(data: NewUser, admin=Depends(require_permission('users.manage'))):
    return await access_service.create_user(data, admin['id'])


@router.patch('/usuarios/{user_id}/rol', dependencies=[Depends(require_admin)])
@router.patch('/users/{user_id}/role', dependencies=[Depends(require_admin)], deprecated=True)
async def assign_role(user_id: UUID, data: RoleAssignment, admin=Depends(require_permission('access.manage'))):
    if str(user_id) == admin['id']:
        raise HTTPException(status_code=403, detail='No puedes modificar tu propio rol')
    await access_service.request('POST', 'rpc/neifit_asignar_rol', json={
        'p_usuario_id': str(user_id), 'p_rol': data.role, 'p_actor_id': admin['id']})
    return {'id': str(user_id), 'role': data.role}
