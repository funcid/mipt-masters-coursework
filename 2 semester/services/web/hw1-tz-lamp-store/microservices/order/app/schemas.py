import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrderStatus(StrEnum):
    NEW = "NEW"
    CONFIRMED = "CONFIRMED"
    ASSEMBLING = "ASSEMBLING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class CartCreateResponse(BaseModel):
    cart_token: uuid.UUID


class CartLineRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_snapshot: dict
    quantity: int
    line_total_cents: int

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    id: uuid.UUID
    cart_token: uuid.UUID
    status: str
    lines: list[CartLineRead]
    total_cents: int
    currency: str = "RUB"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)


class CheckoutRequest(BaseModel):
    customer_name: str = Field(min_length=2, max_length=255)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=5, max_length=32)
    delivery_address: str = Field(min_length=5)
    comment: str | None = None


class OrderLineRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    sku: str
    unit_price_cents: int
    quantity: int
    line_total_cents: int

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: uuid.UUID
    order_number: str
    cart_id: uuid.UUID | None
    status: OrderStatus
    customer_name: str
    customer_email: str
    customer_phone: str
    delivery_address: str
    comment: str | None
    total_cents: int
    currency: str
    created_at: datetime
    updated_at: datetime
    lines: list[OrderLineRead]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
