import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody


class CategoryRead(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=128)


class ProductImageRead(BaseModel):
    id: uuid.UUID
    url: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    sku: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    category_id: uuid.UUID
    price_cents: int = Field(ge=0)
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    watt: int | None = Field(default=None, ge=0)
    base_type: str | None = Field(default=None, max_length=16)
    color_temp_k: int | None = Field(default=None, ge=0)
    lifetime_hours: int | None = Field(default=None, ge=0)
    stock_qty: int = Field(default=0, ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    image_urls: list[str] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=2, max_length=64)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    category_id: uuid.UUID | None = None
    price_cents: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    watt: int | None = Field(default=None, ge=0)
    base_type: str | None = Field(default=None, max_length=16)
    color_temp_k: int | None = Field(default=None, ge=0)
    lifetime_hours: int | None = Field(default=None, ge=0)
    stock_qty: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    image_urls: list[str] | None = None


class ProductRead(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    category: CategoryRead
    images: list[ProductImageRead]

    model_config = ConfigDict(from_attributes=True)
