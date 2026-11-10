from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    subtotal: float

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        return v


class OrderCreate(BaseModel):
    user_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    address: str
    payment_method: str = "contraentrega"
    notes: Optional[str] = None
    subtotal: float
    shipping_cost: float = 5000
    total: float
    items: List[OrderItemCreate]


class OrderStatusUpdate(BaseModel):
    status: str
    message: Optional[str] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        valid = ["recibido","confirmado","en_preparacion","empacado","despachado","en_ruta","entregado","novedad","cancelado"]
        if v not in valid:
            raise ValueError(f"Estado inválido. Opciones: {', '.join(valid)}")
        return v


class TrackingEvent(BaseModel):
    status: str
    message: str
    timestamp: datetime


class OrderOut(BaseModel):
    id: str
    order_number: str
    user_id: Optional[str] = None
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    address: str
    order_status: str
    payment_status: str
    payment_method: str
    subtotal: float
    shipping_cost: float
    total: float
    notes: Optional[str] = None
    assigned_delivery_user_id: Optional[str] = None
    assigned_delivery_name: Optional[str] = None
    items: Optional[list] = []
    tracking_history: Optional[List[TrackingEvent]] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DeliveryOrderOut(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_phone: str
    address: str
    order_status: str
    notes: Optional[str] = None
    assigned_delivery_user_id: Optional[str] = None
    items: list = []
    tracking_history: Optional[List[TrackingEvent]] = []
    created_at: Optional[datetime] = None

