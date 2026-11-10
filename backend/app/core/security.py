"""JWT de Supabase y permisos consultados en profiles."""
from functools import lru_cache
from typing import Optional
from uuid import UUID

import httpx
import jwt
import logging
import re
from fastapi import Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings
from app.core.supabase_headers import service_headers
from app.core.permissions import ROLE_PERMISSIONS, has_permission

security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)
DEMO_TOKENS = {
    "demo-token-admin": {"id": "usr-admin-1", "role": "admin", "full_name": "Administrador General"},
    "demo-token-mensajeria": {"id": "usr-delivery-1", "role": "mensajeria", "full_name": "Carlos Mensajero Neifit"},
    "demo-token-cliente": {"id": "usr-cliente-1", "role": "cliente", "full_name": "María Fernanda Gómez"},
}


@lru_cache(maxsize=4)
def get_jwks_client(url: str):
    return jwt.PyJWKClient(url, timeout=10)


def decode_token(token: str) -> dict:
    key = get_jwks_client(settings.SUPABASE_JWKS_URL).get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token, key.key, algorithms=["RS256", "ES256"],
        audience="authenticated", issuer=settings.SUPABASE_JWT_ISSUER,
        leeway=30,
        options={"require": ["exp", "sub", "iss", "aud"]},
    )
    UUID(payload["sub"])
    return payload


async def load_profile(user_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/profiles",
                params={"id": f"eq.{user_id}", "select": "id,role,full_name,phone", "limit": "1"},
                headers=service_headers(settings.SUPABASE_SERVICE_ROLE_KEY),
            )
            response.raise_for_status()
            profiles = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=503, detail="No se pudo verificar el perfil") from None
    if not isinstance(profiles, list) or len(profiles) != 1:
        raise HTTPException(status_code=403, detail="Perfil no autorizado")
    profile = profiles[0]
    if (not isinstance(profile, dict) or profile.get("id") != user_id
            or not isinstance(profile.get('role'), str)
            or not re.fullmatch(r'[a-z][a-z0-9_]{2,39}', profile['role'])
            or (not settings.RBAC_DATABASE_ENABLED and profile['role'] not in ROLE_PERMISSIONS)):
        raise HTTPException(status_code=403, detail="Perfil no autorizado")
    return profile


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    if not credentials:
        return None
    token = credentials.credentials
    if token in DEMO_TOKENS:
        if (settings.ENABLE_DEMO_AUTH and settings.APP_ENV == "development"
                and not settings.SUPABASE_URL and not settings.SUPABASE_JWKS_URL
                and not settings.SUPABASE_JWT_ISSUER and not settings.SUPABASE_SERVICE_ROLE_KEY):
            user = dict(DEMO_TOKENS[token])
            return {**user, 'permissions': list(ROLE_PERMISSIONS[user['role']])}
        raise HTTPException(status_code=401, detail="Autenticación demo deshabilitada")
    if not all((settings.SUPABASE_URL, settings.SUPABASE_JWKS_URL,
                settings.SUPABASE_JWT_ISSUER, settings.SUPABASE_SERVICE_ROLE_KEY)):
        raise HTTPException(status_code=503, detail="Autenticación no configurada")
    try:
        payload = await run_in_threadpool(decode_token, token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Tu sesión ha expirado. Vuelve a iniciar sesión.',
                            headers={'WWW-Authenticate': 'Bearer', 'X-Auth-Error': 'token_expired'}) from None
    except jwt.ImmatureSignatureError:
        raise HTTPException(status_code=401, detail='La hora del equipo no permite validar la sesión. Revisa la sincronización del reloj.',
                            headers={'WWW-Authenticate': 'Bearer', 'X-Auth-Error': 'token_not_yet_valid'}) from None
    except jwt.PyJWKClientConnectionError:
        raise HTTPException(status_code=503, detail="Servicio de autenticación no disponible") from None
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as error:
        logger.warning('JWT rechazado: %s', type(error).__name__)
        raise HTTPException(status_code=401, detail='No se pudo validar tu sesión. Cierra sesión y vuelve a entrar.',
                            headers={'WWW-Authenticate': 'Bearer', 'X-Auth-Error': 'token_invalid'}) from None
    profile = await load_profile(payload["sub"])
    if settings.RBAC_DATABASE_ENABLED:
        from app.services.access_service import access_service
        permissions = await access_service.permissions_for_role(profile['role'])
    else:
        permissions = list(ROLE_PERMISSIONS[profile['role']])
    return {**profile, "email": payload.get("email"), 'permissions': permissions}


async def require_auth(user: Optional[dict] = Depends(get_current_user)) -> dict:
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    return user


def require_permission(*permissions):
    async def dependency(user=Depends(require_auth)):
        if not any(has_permission(user, code) for code in permissions):
            raise HTTPException(status_code=403, detail='No tienes permiso para esta operación')
        return user
    return dependency


async def require_admin(user: dict = Depends(require_auth)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden realizar esta acción")
    return user


async def require_mensajeria_or_admin(user: dict = Depends(require_auth)) -> dict:
    if user.get("role") not in ("admin", "mensajeria"):
        raise HTTPException(status_code=403, detail="Acceso restringido al personal autorizado")
    return user
