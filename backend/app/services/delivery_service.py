from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from app.core.config import settings
from app.core.supabase_headers import service_headers
from app.core.supabase_rest import database_enabled, supabase_rest as db
from app.core.tenant import current_company_id

logger = logging.getLogger(__name__)


class DeliveryRequestCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    full_name: str = Field(min_length=3, max_length=100, pattern=r'.*\S.*')
    email: str = Field(max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    phone: str = Field(min_length=7, max_length=30, pattern=r'^\+?[0-9 ()-]+$')
    document_id: str = Field(min_length=5, max_length=30, pattern=r'^[A-Za-z0-9.-]+$')
    vehicle_type: str = Field(pattern=r'^(moto|bicicleta|carro|a_pie)$')
    vehicle_plate: str = Field(default='', max_length=20, pattern=r'^[A-Za-z0-9 -]*$')
    city: str = Field(default='Medellín', min_length=2, max_length=60)
    password: SecretStr
    notes: str = Field(default='', max_length=500)

    @field_validator('password')
    @classmethod
    def secure_password(cls, value):
        if not 8 <= len(value.get_secret_value()) <= 128:
            raise ValueError('La contraseña debe tener entre 8 y 128 caracteres')
        return value

    @field_validator('vehicle_plate')
    @classmethod
    def required_plate(cls, value, info):
        if info.data.get('vehicle_type') in ('moto', 'carro') and not value.strip():
            raise ValueError('La placa es obligatoria para moto o carro')
        return value


class DeliveryRequestReview(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    reason: str = Field(default='', max_length=500)


class DeliveryService:
    def __init__(self):
        self._requests: Dict[str, Dict[str, Any]] = {}
        self._notifications: List[Dict[str, Any]] = []

    @staticmethod
    def _auth_url(user_id=None):
        base = settings.SUPABASE_URL.rstrip('/') + '/auth/v1/admin/users'
        return base + ('/' + user_id if user_id else '')

    @staticmethod
    def _public(row):
        return {key: value for key, value in row.items() if key != 'auth_user_id'}

    async def _create_blocked_identity(self, data):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(self._auth_url(), headers=service_headers(settings.SUPABASE_SERVICE_ROLE_KEY), json={
                    'email': data.email.lower(), 'password': data.password.get_secret_value(),
                    'email_confirm': False, 'ban_duration': '876000h',
                    'user_metadata': {'full_name': data.full_name, 'phone': data.phone},
                })
        except httpx.HTTPError:
            raise HTTPException(503, 'No se pudo crear la identidad del postulante') from None
        if response.status_code in (400, 409, 422):
            raise HTTPException(409, 'El correo ya está registrado o la contraseña no cumple la política de Supabase')
        try:
            response.raise_for_status()
            return str(UUID(response.json()['id']))
        except (httpx.HTTPError, ValueError, KeyError):
            raise HTTPException(503, 'Supabase Auth rechazó el registro del postulante') from None

    async def _set_identity_active(self, user_id, active):
        payload = {'ban_duration': 'none' if active else '876000h'}
        if active:
            payload['email_confirm'] = True
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.put(self._auth_url(user_id), headers=service_headers(settings.SUPABASE_SERVICE_ROLE_KEY), json=payload)
                response.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(503, 'No se pudo actualizar la identidad en Supabase Auth') from None

    async def _delete_identity(self, user_id):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.delete(self._auth_url(user_id), headers=service_headers(settings.SUPABASE_SERVICE_ROLE_KEY))
                response.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(503, 'No se pudo limpiar la identidad incompleta en Supabase Auth') from None

    async def _database_request(self, request_id, company_id):
        rows = await db.rows('solicitudes_mensajeria', {
            'id': 'eq.' + request_id, 'empresa_id': 'eq.' + company_id,
            'select': 'id,auth_user_id:usuario_id,full_name:nombre_completo,email:correo,phone:telefono,'
                      'document_id:documento_identidad,vehicle_type:tipo_vehiculo,vehicle_plate:placa_vehiculo,'
                      'city:ciudad,notes:notas,status:estado,rejection_reason:motivo_rechazo,'
                      'reviewed_by:revisado_por,reviewed_at:revisado_en,created_at:creado_en', 'limit': '1'})
        if not rows:
            raise HTTPException(404, 'Solicitud de mensajería no encontrada')
        return rows[0]

    async def list_requests(self, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cid = company_id or current_company_id()
        if database_enabled():
            return await db.rows('solicitudes_mensajeria', {
                'empresa_id': 'eq.' + cid,
                'select': 'id,full_name:nombre_completo,email:correo,phone:telefono,'
                          'document_id:documento_identidad,vehicle_type:tipo_vehiculo,vehicle_plate:placa_vehiculo,'
                          'city:ciudad,notes:notas,status:estado,rejection_reason:motivo_rechazo,'
                          'reviewed_by:revisado_por,reviewed_at:revisado_en,created_at:creado_en',
                'order': 'creado_en.desc'})
        return sorted(self._requests.values(), key=lambda item: item['created_at'], reverse=True)

    async def create_request(self, data, company_id: Optional[str] = None):
        cid = company_id or current_company_id()
        email = data.email.lower()
        if database_enabled():
            duplicate = await db.rows('solicitudes_mensajeria', {
                'empresa_id': 'eq.' + cid, 'estado': 'eq.pendiente', 'correo': 'ilike.' + email,
                'select': 'id', 'limit': '1'})
            if duplicate:
                raise HTTPException(409, 'Ya existe una solicitud pendiente para este correo')
            user_id = await self._create_blocked_identity(data)
            try:
                saved = await db.request('POST', 'solicitudes_mensajeria', data={
                    'empresa_id': cid, 'usuario_id': user_id, 'nombre_completo': data.full_name,
                    'correo': email, 'telefono': data.phone, 'documento_identidad': data.document_id,
                    'tipo_vehiculo': data.vehicle_type, 'placa_vehiculo': data.vehicle_plate.upper(),
                    'ciudad': data.city, 'notas': data.notes, 'estado': 'pendiente'},
                    headers={'Prefer': 'return=representation'})
            except HTTPException:
                await self._delete_identity(user_id)
                raise
            if not isinstance(saved, list) or len(saved) != 1:
                await self._delete_identity(user_id)
                raise HTTPException(503, 'Supabase no confirmó la solicitud de mensajería')
            try:
                await self._notify_admins(cid, data)
            except HTTPException as error:
                # La solicitud ya quedó persistida: no inducir al postulante a duplicarla.
                logger.error('No se notificó la solicitud de mensajería %s: %s', saved[0]['id'], error.detail)
            return {'id': saved[0]['id'], 'full_name': data.full_name, 'email': email,
                    'phone': data.phone, 'document_id': data.document_id, 'vehicle_type': data.vehicle_type,
                    'vehicle_plate': data.vehicle_plate.upper(), 'city': data.city, 'notes': data.notes,
                    'status': 'pendiente', 'rejection_reason': '', 'reviewed_by': None,
                    'reviewed_at': None, 'created_at': saved[0].get('creado_en')}
        request_id = str(uuid4())
        record = {'id': request_id, 'full_name': data.full_name, 'email': email, 'phone': data.phone,
                  'document_id': data.document_id, 'vehicle_type': data.vehicle_type,
                  'vehicle_plate': data.vehicle_plate.upper(), 'city': data.city, 'notes': data.notes,
                  'status': 'pendiente', 'rejection_reason': '', 'reviewed_by': None,
                  'reviewed_at': None, 'created_at': datetime.now(timezone.utc).isoformat()}
        self._requests[request_id] = record
        return record

    async def _notify_admins(self, company_id, data):
        admins = await db.rows('miembros_empresa', {'empresa_id': 'eq.' + company_id,
            'estado': 'eq.activo', 'rol': 'in.(propietario,admin)', 'select': 'usuario_id'})
        if admins:
            await db.request('POST', 'notificaciones', data=[{
                'empresa_id': company_id, 'usuario_id': row['usuario_id'],
                'titulo': 'Nueva solicitud de mensajero',
                'mensaje': f'{data.full_name} solicitó registrarse como mensajero ({data.vehicle_type} {data.vehicle_plate or "sin placa"}).',
                'enlace': '/admin?modulo=solicitudes-mensajeria'} for row in admins])

    async def approve_request(self, request_id, actor, company_id: Optional[str] = None):
        cid = company_id or current_company_id()
        if not database_enabled():
            request = self._requests.get(request_id)
            if not request:
                raise HTTPException(404, 'Solicitud de mensajería no encontrada')
            request['status'] = 'aprobado'
            return request
        request = await self._database_request(request_id, cid)
        if request['status'] != 'pendiente':
            raise HTTPException(409, 'La solicitud ya fue revisada')
        if not request.get('auth_user_id'):
            raise HTTPException(409, 'La solicitud no tiene una identidad de Auth asociada')
        await self._set_identity_active(request['auth_user_id'], True)
        try:
            result = await db.rpc('neifit_aprobar_solicitud_mensajeria', p_actor=actor['id'],
                                  p_empresa=cid, p_solicitud=request_id)
        except HTTPException:
            try:
                await self._set_identity_active(request['auth_user_id'], False)
            except HTTPException:
                raise HTTPException(503, 'El alta quedó incompleta. Bloquea la cuenta en Authentication antes de reintentar.') from None
            raise
        return self._public(result)

    async def reject_request(self, request_id, reason, actor, company_id: Optional[str] = None):
        cid = company_id or current_company_id()
        reason = reason or 'No cumple los requisitos actuales.'
        if not database_enabled():
            request = self._requests.get(request_id)
            if not request:
                raise HTTPException(404, 'Solicitud de mensajería no encontrada')
            request.update(status='rechazado', rejection_reason=reason)
            return request
        await self._database_request(request_id, cid)
        result = await db.rpc('neifit_rechazar_solicitud_mensajeria', p_actor=actor['id'],
                              p_empresa=cid, p_solicitud=request_id, p_motivo=reason)
        return self._public(result)

    async def get_notifications(self, user):
        uid = user.get('id')
        is_admin = user.get('role') in ('propietario', 'admin')
        return [notice for notice in self._notifications
                if is_admin or notice.get('usuario_id') == uid]

    async def mark_notification_read(self, notice_id, user):
        for notice in self._notifications:
            if notice.get('id') == notice_id and (
                    user.get('role') in ('propietario', 'admin')
                    or notice.get('usuario_id') == user.get('id')):
                notice['read_at'] = datetime.now(timezone.utc).isoformat()
                return True
        return False


delivery_service = DeliveryService()
