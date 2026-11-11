"""Acceso de servidor a Supabase. Nunca devuelve secretos ni simula guardados."""
from uuid import UUID
import httpx
from fastapi import HTTPException
from app.core.config import settings
from app.core.supabase_headers import service_headers


def database_enabled():
    return bool(settings.SUPABASE_URL or settings.SUPABASE_SERVICE_ROLE_KEY)


def uuid_value(value, field='identificador'):
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=422, detail=f'{field} inválido. Actualiza el catálogo y utiliza registros reales de Supabase.') from None


class SupabaseRest:
    client = None

    async def request(self, method, resource, *, params=None, data=None, headers=None):
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise HTTPException(status_code=503, detail='Falta configurar Supabase en el backend')
        auth_headers = {**service_headers(settings.SUPABASE_SERVICE_ROLE_KEY), **(headers or {})}
        url = settings.SUPABASE_URL.rstrip('/') + '/rest/v1/' + resource
        try:
            if self.client is not None:
                response = await self.client.request(method, url, params=params, json=data, headers=auth_headers)
            else:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.request(method, url, params=params, json=data, headers=auth_headers)
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail='No se pudo conectar con Supabase. No se confirmó el guardado; reintenta la misma solicitud.') from None
        if response.is_success:
            try:
                return response.json() if response.content else None
            except ValueError:
                raise HTTPException(status_code=503, detail='Respuesta de Supabase no válida') from None
        try:
            error = response.json()
        except ValueError:
            error = {}
        code = error.get('code', '')
        if code in ('PGRST202', 'PGRST205', '42883', '42P01', '42703'):
            raise HTTPException(
                status_code=503,
                detail='El esquema de Supabase y esta versión del backend no coinciden. '
                       'Aplica el instalador correspondiente y vuelve a desplegar el backend; '
                       'consulta PRODUCCION.md y PERSISTENCIA_SUPABASE.md.',
            ) from None
        status = {'42501': 403, 'P0002': 404, 'P0001': 409, '23505': 409,
                  '23503': 422, '23514': 422, '23502': 422, '22023': 422, '22P02': 422, '22003': 422}.get(code)
        if status:
            message = error.get('message') if code in ('P0001', 'P0002', '22023', '42501') else {
                '23505': 'Registro duplicado o solicitud reutilizada con otros datos.',
                '23503': 'La categoría, el producto o el usuario no existe.',
            }.get(code, 'Revisa los campos y valores de la solicitud.')
            raise HTTPException(status_code=status, detail=message) from None
        raise HTTPException(status_code=503, detail='Supabase rechazó la operación. Revisa la configuración y las migraciones.') from None

    async def rows(self, resource, params=None):
        result = []
        offset = 0
        while True:
            page = await self.request('GET', resource, params={**(params or {}), 'offset': str(offset), 'limit': '1000'})
            if not isinstance(page, list):
                raise HTTPException(status_code=503, detail='Respuesta de datos no válida')
            result.extend(page)
            if len(page) < 1000:
                return result
            offset += len(page)

    async def rpc(self, name, **parameters):
        return await self.request('POST', 'rpc/' + name, data=parameters)


supabase_rest = SupabaseRest()
