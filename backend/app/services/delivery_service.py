from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uuid
from pydantic import BaseModel, Field
from app.core.supabase_rest import database_enabled, supabase_rest as db
from app.core.tenant import current_company_id


class DeliveryRequestCreate(BaseModel):
    full_name: str = Field(min_length=3, max_length=100)
    email: str = Field(max_length=254)
    phone: str = Field(min_length=7, max_length=30)
    document_id: str = Field(min_length=5, max_length=30)
    vehicle_type: str = Field(min_length=2, max_length=30)
    vehicle_plate: str = Field(default="", max_length=20)
    city: str = Field(default="Medellín", max_length=60)
    password: str = Field(min_length=6, max_length=128)
    notes: str = Field(default="", max_length=500)


class DeliveryRequestReview(BaseModel):
    reason: str = Field(default="", max_length=500)


INITIAL_MOCK_REQUESTS = [
    {
        "id": "req-del-001",
        "empresa_id": "00000000-0000-0000-0000-000000000001",
        "full_name": "Mateo Valencia Ospina",
        "email": "mateo.valencia@gmail.com",
        "phone": "+57 314 8899001",
        "document_id": "1037654321",
        "vehicle_type": "moto",
        "vehicle_plate": "KTM-45F",
        "city": "Medellín",
        "status": "pendiente",
        "rejection_reason": "",
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": datetime(2026, 11, 10, 14, 20, tzinfo=timezone.utc).isoformat(),
        "notes": "Experiencia de 2 años en reparto de alimentos refrigerados."
    }
]

INITIAL_MOCK_NOTIFICATIONS = [
    {
        "id": "notif-del-001",
        "empresa_id": "00000000-0000-0000-0000-000000000001",
        "user_id": None,  # Para todos los administradores
        "title": "Nueva solicitud de mensajero",
        "message": "Mateo Valencia Ospina solicitó registrarse como mensajero (moto - KTM-45F). Requiere tu aprobación.",
        "link": "/admin?modulo=solicitudes-mensajeria",
        "created_at": datetime(2026, 11, 10, 14, 20, tzinfo=timezone.utc).isoformat(),
        "read_at": None
    }
]


class DeliveryService:
    def __init__(self):
        self._requests: Dict[str, Dict[str, Any]] = {r["id"]: dict(r) for r in INITIAL_MOCK_REQUESTS}
        self._notifications: List[Dict[str, Any]] = [dict(n) for n in INITIAL_MOCK_NOTIFICATIONS]

    async def list_requests(self, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cid = company_id or current_company_id()
        if database_enabled():
            try:
                rows = await db.rows('solicitudes_mensajeria', {
                    'empresa_id': 'eq.' + cid,
                    'select': 'id,full_name:nombre_completo,email:correo,phone:telefono,document_id:documento_identidad,vehicle_type:tipo_vehiculo,vehicle_plate:placa_vehiculo,city:ciudad,status:estado,rejection_reason:motivo_rechazo,reviewed_by:revisado_por,reviewed_at:revisado_en,created_at:creado_en',
                    'order': 'creado_en.desc'
                })
                if rows is not None:
                    return rows
            except Exception:
                pass
        return sorted(list(self._requests.values()), key=lambda x: x.get('created_at', ''), reverse=True)

    async def create_request(self, data: DeliveryRequestCreate, company_id: Optional[str] = None) -> Dict[str, Any]:
        cid = company_id or current_company_id()
        req_id = f"req-{uuid.uuid4()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        req_record = {
            "id": req_id,
            "empresa_id": cid,
            "full_name": data.full_name.strip(),
            "email": data.email.strip().lower(),
            "phone": data.phone.strip(),
            "document_id": data.document_id.strip(),
            "vehicle_type": data.vehicle_type.strip(),
            "vehicle_plate": data.vehicle_plate.strip().upper(),
            "city": data.city.strip(),
            "status": "pendiente",
            "rejection_reason": "",
            "reviewed_by": None,
            "reviewed_at": None,
            "created_at": now_iso,
            "notes": data.notes.strip()
        }

        # Guardar en Supabase si está disponible
        if database_enabled():
            try:
                translated = {
                    'id': str(uuid.uuid4()),
                    'empresa_id': cid,
                    'nombre_completo': req_record['full_name'],
                    'correo': req_record['email'],
                    'telefono': req_record['phone'],
                    'documento_identidad': req_record['document_id'],
                    'tipo_vehiculo': req_record['vehicle_type'],
                    'placa_vehiculo': req_record['vehicle_plate'],
                    'ciudad': req_record['city'],
                    'estado': 'pendiente'
                }
                saved = await db.request('POST', 'solicitudes_mensajeria', data=translated, headers={'Prefer': 'return=representation'})
                if saved and len(saved) > 0:
                    req_record['id'] = saved[0].get('id', req_id)
            except Exception:
                pass

        # Persistir en memoria
        self._requests[req_record["id"]] = req_record

        # Crear notificación para el administrador
        notif_msg = f"{req_record['full_name']} ha solicitado registrarse como mensajero ({req_record['vehicle_type']} {req_record['vehicle_plate']}). Requiere tu aprobación."
        await self.add_notification(
            title="Nueva solicitud de mensajero",
            message=notif_msg,
            link="/admin?modulo=solicitudes-mensajeria",
            company_id=cid
        )

        return req_record

    async def approve_request(self, request_id: str, actor: Dict[str, Any], company_id: Optional[str] = None) -> Dict[str, Any]:
        cid = company_id or current_company_id()
        now_iso = datetime.now(timezone.utc).isoformat()
        actor_id = actor.get('id', 'admin')

        req = self._requests.get(request_id)
        if not req and database_enabled():
            rows = await self.list_requests(cid)
            matched = [r for r in rows if str(r.get('id')) == str(request_id)]
            if matched:
                req = matched[0]

        if not req:
            req = {
                "id": request_id,
                "full_name": "Mensajero",
                "email": "mensajeria@neifit.com",
                "status": "pendiente"
            }

        req["status"] = "aprobado"
        req["reviewed_by"] = actor_id
        req["reviewed_at"] = now_iso
        self._requests[request_id] = req

        # Si Supabase está conectado, actualizar la tabla
        if database_enabled():
            try:
                await db.request('PATCH', 'solicitudes_mensajeria', params={'id': f'eq.{request_id}'}, data={
                    'estado': 'aprobado',
                    'revisado_por': actor_id if len(actor_id) == 36 else None,
                    'revisado_en': now_iso
                })
            except Exception:
                pass

        # Notificación de confirmación para el mensajero
        await self.add_notification(
            title="¡Solicitud de mensajero aprobada!",
            message=f"La cuenta de mensajería para {req.get('full_name')} ha sido aprobada. Ya tiene permiso para realizar entregas.",
            link="/mensajeria",
            company_id=cid,
            user_id=req.get("email")
        )

        return req

    async def reject_request(self, request_id: str, reason: str, actor: Dict[str, Any], company_id: Optional[str] = None) -> Dict[str, Any]:
        cid = company_id or current_company_id()
        now_iso = datetime.now(timezone.utc).isoformat()
        actor_id = actor.get('id', 'admin')

        req = self._requests.get(request_id)
        if not req and database_enabled():
            rows = await self.list_requests(cid)
            matched = [r for r in rows if str(r.get('id')) == str(request_id)]
            if matched:
                req = matched[0]

        if not req:
            req = {
                "id": request_id,
                "full_name": "Mensajero",
                "status": "pendiente"
            }

        req["status"] = "rechazado"
        req["rejection_reason"] = reason or "No cumple los requisitos actuales."
        req["reviewed_by"] = actor_id
        req["reviewed_at"] = now_iso
        self._requests[request_id] = req

        if database_enabled():
            try:
                await db.request('PATCH', 'solicitudes_mensajeria', params={'id': f'eq.{request_id}'}, data={
                    'estado': 'rechazado',
                    'motivo_rechazo': req["rejection_reason"],
                    'revisado_por': actor_id if len(actor_id) == 36 else None,
                    'revisado_en': now_iso
                })
            except Exception:
                pass

        return req

    async def add_notification(self, title: str, message: str, link: str, company_id: str, user_id: Optional[str] = None):
        notif = {
            "id": f"notif-{uuid.uuid4()}",
            "empresa_id": company_id,
            "usuario_id": user_id,
            "title": title,
            "message": message,
            "link": link,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "read_at": None
        }
        self._notifications.insert(0, notif)

        if database_enabled() and user_id:
            try:
                await db.request('POST', 'notificaciones', data={
                    'empresa_id': company_id,
                    'usuario_id': user_id,
                    'titulo': title,
                    'mensaje': message,
                    'enlace': link
                })
            except Exception:
                pass

    async def get_notifications(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        cid = current_company_id()
        uid = user.get('id')
        role = user.get('role', 'cliente')

        if database_enabled():
            try:
                rows = await db.request('GET', 'notificaciones', params={
                    'empresa_id': 'eq.' + cid,
                    'usuario_id': 'eq.' + uid,
                    'select': 'id,title:titulo,message:mensaje,link:enlace,created_at:creado_en,read_at:leido_en',
                    'order': 'creado_en.desc,id',
                    'limit': '50'
                })
                if rows:
                    return rows
            except Exception:
                pass

        # Filtrar notificaciones en memoria:
        # Los administradores ven notificaciones dirigidas a ellos o del sistema (usuario_id is None)
        is_admin = role in ('admin', 'propietario')
        results = []
        for n in self._notifications:
            target_user = n.get('usuario_id')
            if is_admin or target_user == uid or target_user == user.get('email'):
                results.append(n)
        return results

    async def mark_notification_read(self, notice_id: str, user: Dict[str, Any]) -> bool:
        cid = current_company_id()
        now_iso = datetime.now(timezone.utc).isoformat()

        if database_enabled():
            try:
                await db.request('PATCH', 'notificaciones', params={
                    'id': 'eq.' + str(notice_id),
                    'empresa_id': 'eq.' + cid,
                    'usuario_id': 'eq.' + user['id'],
                    'leido_en': 'is.null'
                }, data={'leido_en': now_iso})
                return True
            except Exception:
                pass

        for n in self._notifications:
            if n.get('id') == str(notice_id):
                n['read_at'] = now_iso
                return True
        return True


delivery_service = DeliveryService()

