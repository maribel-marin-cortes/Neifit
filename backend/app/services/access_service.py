import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.core.supabase_headers import service_headers
from app.core.permissions import ROLE_PERMISSIONS, PERMISSIONS, CUSTOM_ROLE_PERMISSIONS


class AccessService:
    async def request(self, method, path, **kwargs):
        if not settings.RBAC_DATABASE_ENABLED:
            raise HTTPException(status_code=503, detail='Primero aplica la migración RBAC y activa RBAC_DATABASE_ENABLED')
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise HTTPException(status_code=503, detail='Supabase no configurado para gestionar accesos')
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.request(method, settings.SUPABASE_URL.rstrip('/') + '/rest/v1/' + path,
                    headers=service_headers(settings.SUPABASE_SERVICE_ROLE_KEY), **kwargs)
                response.raise_for_status()
                return response.json() if response.content else None
        except httpx.HTTPStatusError as error:
            if error.response.status_code == 409:
                raise HTTPException(status_code=409, detail='El código del rol ya existe. Utiliza otro código.') from None
            if error.response.status_code in (400, 403):
                raise HTTPException(status_code=403, detail='Cambio de acceso rechazado. Revisa el rol, los permisos y el usuario seleccionado.') from None
            raise HTTPException(status_code=503, detail='No se pudo consultar la gestión de accesos. Revisa la migración RBAC.') from None
        except (httpx.HTTPError, ValueError):
            raise HTTPException(status_code=503, detail='Servicio de gestión de accesos no disponible') from None

    async def permissions_for_role(self, role):
        if role == 'admin':
            return list(ROLE_PERMISSIONS['admin'])
        rows = await self.request('GET', 'permisos_rol', params={'rol': 'eq.' + role, 'select': 'permission_code:codigo_permiso'})
        if not isinstance(rows, list):
            raise HTTPException(status_code=503, detail='No se pudieron verificar permisos')
        return [row['permission_code'] for row in rows if row.get('permission_code') in ROLE_PERMISSIONS.get(role, CUSTOM_ROLE_PERMISSIONS)]

    async def configuration(self):
        roles = []
        definitions = await self.request('GET', 'roles_acceso', params={'select': 'code:codigo,name:nombre', 'order': 'nombre'}) if settings.RBAC_DATABASE_ENABLED else [
            {'code': code, 'name': name} for code, name in [('admin', 'Administrador'), ('cliente', 'Cliente'), ('mensajeria', 'Mensajero / domiciliario')]]
        for definition in definitions:
            role = definition['code']
            allowed = ROLE_PERMISSIONS.get(role, CUSTOM_ROLE_PERMISSIONS)
            granted = await self.permissions_for_role(role) if settings.RBAC_DATABASE_ENABLED else allowed
            roles.append({'role': role, 'name': definition['name'], 'permissions': granted, 'allowed_permissions': allowed})
        users = await self.request('GET', 'perfiles', params={'select': 'id,full_name:nombre_completo,email:correo,phone:telefono,role:rol', 'order': 'creado_en.desc', 'limit': '100'}) if settings.RBAC_DATABASE_ENABLED else []
        return {'editable': settings.RBAC_DATABASE_ENABLED, 'roles': roles, 'permissions': PERMISSIONS, 'users': users}

    async def create_user(self, data, actor_id):
        # Comprobar migración y rol antes de crear una identidad en Auth.
        roles = await self.request('GET', 'roles_acceso', params={'codigo': 'eq.' + data.role, 'select': 'code:codigo'})
        if not roles:
            raise HTTPException(status_code=422, detail='El rol seleccionado no existe')
        headers = service_headers(settings.SUPABASE_SERVICE_ROLE_KEY)
        base = settings.SUPABASE_URL.rstrip('/') + '/auth/v1/admin/users'
        user_id = None
        async with httpx.AsyncClient(timeout=20) as client:
            try:
                response = await client.post(base, headers=headers, json={
                    'email': str(data.email).strip().lower(), 'password': data.password.get_secret_value(),
                    'email_confirm': True, 'ban_duration': '876000h',
                    'user_metadata': {'full_name': data.full_name, 'phone': data.phone}})
                if response.status_code in (400, 422):
                    raise HTTPException(status_code=409, detail='No se pudo registrar: revisa si el correo ya existe o si la contraseña cumple la política de Supabase.')
                response.raise_for_status()
                from uuid import UUID
                user_id = str(UUID(response.json()['id']))
                await self.request('POST', 'rpc/neifit_asignar_rol', json={
                    'p_actor_id': actor_id, 'p_usuario_id': user_id, 'p_rol': data.role})
                activated = await client.put(base + '/' + user_id, headers=headers, json={'ban_duration': 'none'})
                activated.raise_for_status()
                return {'id': user_id, 'email': str(data.email).strip().lower(), 'role': data.role}
            except (HTTPException, httpx.HTTPError, ValueError, KeyError) as error:
                if user_id:
                    try:
                        cleanup = await client.delete(base + '/' + user_id, headers=headers)
                        cleanup.raise_for_status()
                    except httpx.HTTPError:
                        raise HTTPException(status_code=503, detail='El alta quedó incompleta. Revisa Authentication → Users antes de reintentar; la cuenta puede seguir bloqueada.') from None
                if isinstance(error, HTTPException):
                    raise
                raise HTTPException(status_code=503, detail='No se completó el alta. Revisa la conexión y Authentication → Users antes de reintentar.') from None


access_service = AccessService()
