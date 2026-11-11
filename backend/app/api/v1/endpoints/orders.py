from fastapi import APIRouter, HTTPException, Depends
from typing import List, Union
from app.schemas.order import OrderOut, OrderCreate, OrderStatusUpdate, DeliveryOrderOut
from app.core.security import require_auth, require_admin, require_mensajeria_or_admin, require_permission
from app.services.order_service import order_service
from app.services.commerce_repository import commerce
from app.schemas.order import DeliveryAssignment
from uuid import UUID
from app.core.config import settings

router = APIRouter()
service = order_service


@router.get('/mensajeros')
@router.get('/delivery-users', deprecated=True)
async def delivery_users(user=Depends(require_permission('orders.manage'))):
    return await commerce.delivery_users()


@router.patch('/{order_id}/mensajero')
@router.patch('/{order_id}/delivery', deprecated=True)
async def assign_delivery(order_id: UUID, data: DeliveryAssignment, user=Depends(require_permission('orders.manage'))):
    return await commerce.assign_delivery(str(order_id), str(data.user_id) if data.user_id else None, user)


@router.get("/", response_model=List[Union[OrderOut, DeliveryOrderOut]])
async def list_orders(user=Depends(require_permission('orders.read_own', 'orders.manage', 'delivery.read_assigned'))):
    """
    Lista de pedidos.
    - Admin: todos los pedidos.
    - Mensajería: pedidos asignados a sí mismo.
    - Cliente: sus propios pedidos.
    """
    return await service.list_for_user(user)


@router.post("/", response_model=OrderOut, status_code=201)
async def create_order(data: OrderCreate, user=Depends(require_permission('orders.create'))):
    """
    Crear pedido.
    El backend valida stock de forma atómica y rechaza si hay producto agotado.
    Nunca confiar en stock declarado por el frontend.
    """
    if settings.APP_ENV == 'production' and data.payment_method != 'contraentrega':
        raise HTTPException(422, 'En el piloto solo está habilitado el pago contraentrega')
    return await service.create_order(data, user)


@router.get("/{order_id}", response_model=Union[OrderOut, DeliveryOrderOut])
async def get_order(order_id: str, user=Depends(require_permission('orders.read_own', 'orders.manage', 'delivery.read_assigned'))):
    """Detalle de un pedido. Solo el dueño, mensajero asignado o admin."""
    order = await service.get_by_id(order_id, user)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.patch("/{order_id}/estado")
@router.patch("/{order_id}/status", deprecated=True)
async def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    user=Depends(require_permission('orders.manage', 'delivery.start', 'delivery.complete', 'delivery.issue'))
):
    """
    Actualizar estado del pedido.
    Solo mensajería (su pedido asignado) o admin.
    Mensajería no puede editar precio ni productos.
    """
    updated = await service.update_status(order_id, data, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return updated

