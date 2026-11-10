from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    name: str = Field(min_length=3,max_length=150,pattern=r'.*\S.*')
    slug: Optional[str] = Field(default=None,pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    description: Optional[str] = None
    price: float = Field(gt=0,allow_inf_nan=False)
    stock: int = 0
    is_available: Optional[bool] = None
    image_url: Optional[str] = None
    featured: bool = False
    is_active: bool = True
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
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
    category_id: str = Field(min_length=1)


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
    expected_updated_at: Optional[datetime] = None
    name: Optional[str] = Field(default=None,min_length=3,max_length=150,pattern=r'.*\S.*')
    slug: Optional[str] = Field(default=None,pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    description: Optional[str] = None
    price: Optional[float] = Field(default=None,gt=0,allow_inf_nan=False)
    stock: Optional[int] = Field(default=None,ge=0)
    is_available: Optional[bool] = None
    image_url: Optional[str] = None
    featured: Optional[bool] = None
    category_id: Optional[str] = None
    is_active: Optional[bool] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None


class ProductOut(ProductBase):
    id: str
    sales_enabled: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

