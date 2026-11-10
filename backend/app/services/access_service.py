import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.core.permissions import ROLE_PERMISSIONS, PERMISSIONS


class AccessService:
    async def request(self, method, path, **kwargs):
        if not settings.RBAC_DATABASE_ENABLED:
            raise HTTPException(status_code=503, detail='Primero aplica la migración RBAC y activa RBAC_DATABASE_ENABLED')
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise HTTPException(status_code=503, detail='Supabase no configurado para gestionar accesos')
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.request(method, settings.SUPABASE_URL.rstrip('/') + '/rest/v1/' + path,
                    headers={'apikey': settings.SUPABASE_SERVICE_ROLE_KEY, 'Authorization': 'Bearer ' + settings.SUPABASE_SERVICE_ROLE_KEY}, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else None
        except httpx.HTTPStatusError as error:
            if error.response.status_code in (400, 403):
                raise HTTPException(status_code=403, detail='Cambio de acceso rechazado. Revisa el rol, los permisos y el usuario seleccionado.') from None
            raise HTTPException(status_code=503, detail='No se pudo consultar la gestión de accesos. Revisa la migración RBAC.') from None
        except (httpx.HTTPError, ValueError):
            raise HTTPException(status_code=503, detail='Servicio de gestión de accesos no disponible') from None

    async def permissions_for_role(self, role):
        if role == 'admin':
            return list(ROLE_PERMISSIONS['admin'])
        rows = await self.request('GET', 'role_permissions', params={'role': 'eq.' + role, 'select': 'permission_code'})
        if not isinstance(rows, list):
            raise HTTPException(status_code=503, detail='No se pudieron verificar permisos')
        return [row['permission_code'] for row in rows if row.get('permission_code') in ROLE_PERMISSIONS.get(role, [])]

    async def configuration(self):
        roles = []
        for role, allowed in ROLE_PERMISSIONS.items():
            granted = await self.permissions_for_role(role) if settings.RBAC_DATABASE_ENABLED else allowed
            roles.append({'role': role, 'permissions': granted, 'allowed_permissions': allowed})
        users = await self.request('GET', 'profiles', params={'select': 'id,full_name,email,role', 'order': 'created_at.desc', 'limit': '100'}) if settings.RBAC_DATABASE_ENABLED else []
        return {'editable': settings.RBAC_DATABASE_ENABLED, 'roles': roles, 'permissions': PERMISSIONS, 'users': users}


access_service = AccessService()
