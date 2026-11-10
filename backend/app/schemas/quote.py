from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class QuoteItemCreate(BaseModel):
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    quantity: int
    reference_price: float


class QuoteCreate(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    notes: Optional[str] = None
    items: List[QuoteItemCreate]


class QuoteOut(BaseModel):
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

