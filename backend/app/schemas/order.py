from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional, List
from datetime import datetime


class OrderItemCreate(BaseModel):
    product_id: str
    product_name: Optional[str] = None
    quantity: int
    unit_price: float = Field(default=0,ge=0,allow_inf_nan=False)
    subtotal: float = Field(default=0,ge=0,allow_inf_nan=False)

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        return v


class OrderCreate(BaseModel):
    request_id: Optional[UUID] = None
    user_id: Optional[str] = None
    customer_name: str = Field(min_length=3,max_length=100,pattern=r'.*\S.*')
    customer_phone: str = Field(min_length=7,max_length=30)
    customer_email: Optional[str] = None
    address: str = Field(min_length=5,max_length=300,pattern=r'.*\S.*')
    payment_method: str = "contraentrega"
    notes: Optional[str] = Field(default=None,max_length=3000)
    subtotal: float = Field(default=0,ge=0,allow_inf_nan=False)
    shipping_cost: float = Field(default=0,ge=0,allow_inf_nan=False)
    total: float = Field(default=0,ge=0,allow_inf_nan=False)
    items: List[OrderItemCreate] = Field(min_length=1,max_length=100)


class DeliveryAssignment(BaseModel):
    user_id: Optional[UUID] = None


class OrderStatusUpdate(BaseModel):
    status: str
    message: Optional[str] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        # Se aceptan estados históricos para poder migrar pedidos anteriores.
        valid = ["recibido","confirmado","en_preparacion","empacado","despachado","en_ruta","entregado","novedad","cancelado"]
        if v not in valid:
            raise ValueError(f"Estado inválido. Opciones: {', '.join(valid)}")
        return v


class TrackingEvent(BaseModel):
    status: str
    message: str
    timestamp: datetime


class OrderOut(BaseModel):
    is_simulated: bool = False
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

