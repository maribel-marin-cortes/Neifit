from fastapi import APIRouter, HTTPException, Depends
from app.core.security import require_auth
from app.schemas.order import OrderOut, DeliveryOrderOut
from typing import Union
from app.core.permissions import can_read_order, project_order
from app.services.order_service import order_service

router = APIRouter()
service = order_service


@router.get("/{tracking_code}", response_model=Union[OrderOut, DeliveryOrderOut])
async def track_order(tracking_code: str, user=Depends(require_auth)):
    """
    Seguimiento privado: propietario, administrador o mensajero asignado.
    """
    order = await service.get_by_tracking_code(tracking_code, user)
    authorized = order and can_read_order(user, order)
    if not authorized:
        raise HTTPException(
            status_code=404,
            detail="No se encontró ningún pedido con este código. Verifica el número e intenta de nuevo."
        )
    return project_order(user, order)

