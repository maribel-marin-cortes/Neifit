from app.core.permissions import can_read_order, authorize_delivery_update, project_order
from typing import List, Optional
import uuid
from datetime import datetime
from app.schemas.order import OrderCreate, OrderStatusUpdate


MOCK_ORDERS = [
    {
        "id": "ord-101",
        "order_number": "NF-2026-001",
        "user_id": "usr-cliente-1",
        "customer_name": "María Fernanda Gómez",
        "customer_phone": "+57 300 1234567",
        "customer_email": "maria.gomez@gmail.com",
        "address": "Calle 10 # 43E - 22, El Poblado, Medellín",
        "order_status": "en_ruta",
        "payment_status": "aprobado",
        "payment_method": "wompi",
        "subtotal": 25500,
        "shipping_cost": 5000,
        "total": 30500,
        "assigned_delivery_user_id": "usr-delivery-1",
        "assigned_delivery_name": "Carlos Mensajero Neifit",
        "notes": "Entregar en portería torre 2",
        "items": [
            {"product_id":"prod-1","product_name":"Postre de Maracuyá Saludable","quantity":1,"unit_price":12500,"subtotal":12500},
            {"product_id":"prod-2","product_name":"Mousse Natural de Mango","quantity":1,"unit_price":13000,"subtotal":13000},
        ],
        "tracking_history": [
            {"status":"recibido","message":"Pedido recibido en el sistema de Neifit.","timestamp":datetime(2026,11,1,10,30)},
            {"status":"confirmado","message":"Pago confirmado exitosamente.","timestamp":datetime(2026,11,1,10,32)},
            {"status":"en_preparacion","message":"Cocina artesanal preparando los postres frescos.","timestamp":datetime(2026,11,1,11,0)},
            {"status":"empacado","message":"Pedido empacado en contenedor isotérmico ecológico.","timestamp":datetime(2026,11,1,11,45)},
            {"status":"en_ruta","message":"Mensajero Carlos en camino a la dirección indicada.","timestamp":datetime(2026,11,1,12,15)},
        ],
        "created_at": datetime(2026,11,1,10,30),
    },
    {
        "id": "ord-102",
        "order_number": "NF-2026-002",
        "user_id": "usr-cliente-2",
        "customer_name": "Andrés Felipe Ruiz",
        "customer_phone": "+57 311 9876543",
        "customer_email": "andres.ruiz@hotmail.com",
        "address": "Circular 4 # 73 - 15, Laureles, Medellín",
        "order_status": "entregado",
        "payment_status": "aprobado",
        "payment_method": "transferencia",
        "subtotal": 33000,
        "shipping_cost": 5000,
        "total": 38000,
        "assigned_delivery_user_id": "usr-delivery-1",
        "assigned_delivery_name": "Carlos Mensajero Neifit",
        "notes": "Timbre 301",
        "items": [
            {"product_id":"prod-8","product_name":"Dátiles Medjool con Crema de Maní","quantity":3,"unit_price":11000,"subtotal":33000},
        ],
        "tracking_history": [
            {"status":"recibido","message":"Pedido recibido.","timestamp":datetime(2026,10,31,15,20)},
            {"status":"confirmado","message":"Confirmado.","timestamp":datetime(2026,10,31,15,25)},
            {"status":"despachado","message":"Despachado con mensajería.","timestamp":datetime(2026,10,31,16,0)},
            {"status":"entregado","message":"Entregado a satisfacción.","timestamp":datetime(2026,10,31,17,10)},
        ],
        "created_at": datetime(2026,10,31,15,20),
    }
]


class OrderService:
    def __init__(self):
        self._data = {o["id"]: o for o in MOCK_ORDERS}
        self._counter = len(MOCK_ORDERS) + 1

    async def list_for_user(self, user: dict) -> List[dict]:
        return [project_order(user, order) for order in self._data.values() if can_read_order(user, order)]

    async def create_order(self, data: OrderCreate, user: dict) -> dict:
        # En producción: validar stock atómicamente con transacción PostgreSQL
        order_id = str(uuid.uuid4())
        order_number = f"NF-2026-{self._counter:03d}"
        self._counter += 1
        order = {
            "id": order_id,
            "order_number": order_number,
            "user_id": user.get("id") or data.user_id or "guest",
            "customer_name": data.customer_name,
            "customer_phone": data.customer_phone,
            "customer_email": data.customer_email,
            "address": data.address,
            "order_status": "recibido",
            "payment_status": "pendiente" if data.payment_method == "contraentrega" else "aprobado",
            "payment_method": data.payment_method,
            "subtotal": data.subtotal,
            "shipping_cost": data.shipping_cost,
            "total": data.total,
            "notes": data.notes,
            "assigned_delivery_user_id": None,
            "assigned_delivery_name": None,
            "items": [i.model_dump() for i in data.items],
            "tracking_history": [
                {"status":"recibido","message":"Pedido recibido en Neifit y en validación.","timestamp":datetime.now()}
            ],
            "created_at": datetime.now(),
        }
        self._data[order_id] = order
        return order

    async def get_by_id(self, order_id: str, user: dict) -> Optional[dict]:
        order = self._data.get(order_id)
        if not order:
            return None
        return project_order(user, order) if can_read_order(user, order) else None

    async def get_by_tracking_code(self, code: str) -> Optional[dict]:
        code_clean = code.strip().upper()
        for order in self._data.values():
            if order["order_number"].upper() == code_clean or order["id"] == code:
                return order
        return None

    async def update_status(self, order_id: str, data: OrderStatusUpdate, user: dict) -> Optional[dict]:
        order = self._data.get(order_id)
        if not order:
            return None
        authorize_delivery_update(user, order, data.status)
        order["order_status"] = data.status
        history = order.get("tracking_history", [])
        history.append({
            "status": data.status,
            "message": data.message or f"Estado actualizado a: {data.status.replace('_',' ')}",
            "timestamp": datetime.now()
        })
        order["tracking_history"] = history
        self._data[order_id] = order
        return project_order(user, order)

