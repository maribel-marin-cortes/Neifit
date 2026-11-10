from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from app.core.security import require_permission
from app.core.permissions import ROLE_PERMISSIONS
from app.services.access_service import access_service

router = APIRouter()
Role = Literal['cliente', 'mensajeria', 'admin']


class RoleAssignment(BaseModel):
    role: Role


class PermissionAssignment(BaseModel):
    permissions: list[str] = Field(max_length=20)


@router.get('/')
async def configuration(admin=Depends(require_permission('access.manage'))):
    return await access_service.configuration()


@router.put('/roles/{role}/permissions')
async def assign_permissions(role: Role, data: PermissionAssignment, admin=Depends(require_permission('access.manage'))):
    if role == 'admin' or 'profile.read' not in data.permissions or not set(data.permissions).issubset(ROLE_PERMISSIONS[role]):
        raise HTTPException(status_code=403, detail='Solo puedes modificar los permisos delegables de cliente y mensajería')
    await access_service.request('POST', 'rpc/neifit_set_role_permissions', json={
        'p_role': role, 'p_permissions': sorted(set(data.permissions)), 'p_actor_id': admin['id']})
    return {'role': role, 'permissions': sorted(set(data.permissions))}


@router.patch('/users/{user_id}/role')
async def assign_role(user_id: UUID, data: RoleAssignment, admin=Depends(require_permission('access.manage'))):
    if str(user_id) == admin['id']:
        raise HTTPException(status_code=403, detail='No puedes modificar tu propio rol')
    await access_service.request('POST', 'rpc/neifit_assign_role', json={
        'p_user_id': str(user_id), 'p_role': data.role, 'p_actor_id': admin['id']})
    return {'id': str(user_id), 'role': data.role}
