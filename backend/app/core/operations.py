"""Registro operativo sin tokens, cuerpos, correos ni direcciones."""
import json
import logging
import time
from uuid import uuid4

logger = logging.getLogger('neifit.requests')


async def request_log(request, call_next):
    request_id = uuid4().hex
    start = time.monotonic()
    try:
        response = await call_next(request)
    except Exception as error:
        # No registrar el mensaje de la excepción: podría contener datos privados.
        logger.error(json.dumps({'event': 'request_failed', 'request_id': request_id, 'exception_type': type(error).__name__}))
        from starlette.responses import JSONResponse
        response = JSONResponse({'detail': 'Error interno. Conserva el identificador de solicitud para soporte.', 'request_id': request_id}, status_code=500)
    route = request.scope.get('route')
    logger.log(logging.ERROR if response.status_code >= 500 else logging.INFO,
               json.dumps({'event': 'http_request', 'request_id': request_id, 'method': request.method,
                           'route': getattr(route, 'path', 'unmatched'), 'status': response.status_code,
                           'duration_ms': round((time.monotonic()-start)*1000)}))
    response.headers['X-Request-ID'] = request_id
    return response


def validate_production(settings):
    if settings.APP_ENV != 'production':
        return
    if (settings.DEBUG or settings.ENABLE_DEMO_AUTH or not settings.RBAC_DATABASE_ENABLED
        or not settings.SUPABASE_URL.startswith('https://') or not settings.SUPABASE_SERVICE_ROLE_KEY
        or not settings.SUPABASE_JWKS_URL or not settings.SUPABASE_JWT_ISSUER
        or not settings.ALLOWED_ORIGINS or any(not origin.startswith('https://') or origin.endswith('/') for origin in settings.ALLOWED_ORIGINS)):
        raise RuntimeError('Configuración de producción incompleta: revisa DEBUG, Auth, RBAC, Supabase y orígenes HTTPS exactos.')
