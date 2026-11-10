from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    price: float
    stock: int = 0
    is_available: Optional[bool] = None
    image_url: Optional[str] = None
    featured: bool = False
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    category_slug: Optional[str] = None

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        return v

    @field_validator("stock")
    @classmethod
    def stock_non_negative(cls, v):
        if v < 0:
            raise ValueError("El stock no puede ser negativo")
        return v


class ProductCreate(ProductBase):
    pass


class ProductPreview(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    category_name: Optional[str] = None
    price: float
    is_available: bool
    featured: bool


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    is_available: Optional[bool] = None
    image_url: Optional[str] = None
    featured: Optional[bool] = None
    category_id: Optional[str] = None


class ProductOut(ProductBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

