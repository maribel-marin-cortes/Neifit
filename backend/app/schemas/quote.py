from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime


class QuoteItemCreate(BaseModel):
    product_id: str = Field(min_length=1)
    product_name: Optional[str] = None
    quantity: int = Field(gt=0,le=10000)
    reference_price: float = Field(default=0,ge=0,allow_inf_nan=False)


class QuoteCreate(BaseModel):
    request_id: Optional[UUID] = None
    customer_name: str = Field(min_length=3,max_length=100,pattern=r'.*\S.*')
    customer_phone: str = Field(min_length=7,max_length=30)
    customer_email: Optional[str] = None
    notes: Optional[str] = Field(default=None,max_length=3000)
    items: List[QuoteItemCreate] = Field(min_length=1,max_length=100)


class QuoteStatusUpdate(BaseModel):
    status: Literal['pendiente','respondida','aceptada','rechazada','cancelada']


class QuoteOut(BaseModel):
    offered_total: Optional[float] = None
    offer_conditions: Optional[str] = None
    offer_valid_until: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    id: str
    quote_number: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    status: str
    notes: Optional[str] = None
    items: Optional[list] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

