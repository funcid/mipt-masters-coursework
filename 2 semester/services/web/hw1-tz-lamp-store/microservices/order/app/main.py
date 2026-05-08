import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import os

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from jwt import ExpiredSignatureError, InvalidSignatureError, PyJWTError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog_client import fetch_product_snapshot
from app.db import get_session, init_db
from app.models import Cart, CartLine, CustomerOrder, OrderLine
from app.schemas import (
    CartCreateResponse,
    CartItemCreate,
    CartItemUpdate,
    CartRead,
    CheckoutRequest,
    OrderRead,
    OrderStatus,
    OrderStatusUpdate,
)

ALLOWED_STATUS_TRANSITIONS = {
    OrderStatus.NEW: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.ASSEMBLING, OrderStatus.CANCELLED},
    OrderStatus.ASSEMBLING: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Order Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8100"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_jwt(authorization: str | None = Header(default=None)) -> int:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен отсутствует")
    parts = authorization.split(" ", maxsplit=1)
    if len(parts) != 2 or parts[0] != "Bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некорректный заголовок авторизации")
    token = parts[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истек")
    except (InvalidSignatureError, PyJWTError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный токен")
    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный payload токена")
    return user_id


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == status.HTTP_404_NOT_FOUND else "request_error"
    return error_response(code, str(exc.detail), exc.status_code)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def cart_token_header(x_cart_token: uuid.UUID | None = Header(default=None, alias="X-Cart-Token")) -> uuid.UUID:
    if x_cart_token is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Передайте заголовок X-Cart-Token")
    return x_cart_token


def cart_query():
    return select(Cart).options(selectinload(Cart.lines))


async def get_cart_by_token(token: uuid.UUID, session: AsyncSession) -> Cart:
    cart = await session.scalar(cart_query().where(Cart.cart_token == token))
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Корзина не найдена")
    return cart


def serialize_cart(cart: Cart) -> dict:
    lines = []
    total_cents = 0
    for line in cart.lines:
        line_total = line.product_snapshot["price_cents"] * line.quantity
        total_cents += line_total
        lines.append(
            {
                "id": line.id,
                "product_id": line.product_id,
                "product_snapshot": line.product_snapshot,
                "quantity": line.quantity,
                "line_total_cents": line_total,
            },
        )
    return {
        "id": cart.id,
        "cart_token": cart.cart_token,
        "status": cart.status,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "RUB",
        "created_at": cart.created_at,
        "updated_at": cart.updated_at,
    }


@app.post("/api/v1/carts", response_model=CartCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_cart(session: AsyncSession = Depends(get_session)) -> CartCreateResponse:
    cart = Cart()
    session.add(cart)
    await session.commit()
    await session.refresh(cart)
    return CartCreateResponse(cart_token=cart.cart_token)


@app.get("/api/v1/cart", response_model=CartRead)
async def get_cart(
    token: uuid.UUID = Depends(cart_token_header),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cart = await get_cart_by_token(token, session)
    return serialize_cart(cart)


@app.post("/api/v1/cart/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
async def add_cart_item(
    payload: CartItemCreate,
    token: uuid.UUID = Depends(cart_token_header),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cart = await get_cart_by_token(token, session)
    if cart.status != "OPEN":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Корзина уже оформлена")

    snapshot = await fetch_product_snapshot(payload.product_id)
    line = next((item for item in cart.lines if item.product_id == payload.product_id), None)
    if line:
        line.quantity += payload.quantity
        line.product_snapshot = snapshot
    else:
        cart.lines.append(CartLine(product_id=payload.product_id, product_snapshot=snapshot, quantity=payload.quantity))

    await session.commit()
    cart = await get_cart_by_token(token, session)
    return serialize_cart(cart)


@app.patch("/api/v1/cart/items/{product_id}", response_model=CartRead)
async def update_cart_item(
    product_id: uuid.UUID,
    payload: CartItemUpdate,
    token: uuid.UUID = Depends(cart_token_header),
    session: AsyncSession = Depends(get_session),
) -> dict:
    cart = await get_cart_by_token(token, session)
    line = next((item for item in cart.lines if item.product_id == product_id), None)
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Позиция корзины не найдена")
    line.quantity = payload.quantity
    await session.commit()
    cart = await get_cart_by_token(token, session)
    return serialize_cart(cart)


@app.delete("/api/v1/cart/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cart_item(
    product_id: uuid.UUID,
    token: uuid.UUID = Depends(cart_token_header),
    session: AsyncSession = Depends(get_session),
) -> Response:
    cart = await get_cart_by_token(token, session)
    line = next((item for item in cart.lines if item.product_id == product_id), None)
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Позиция корзины не найдена")
    await session.delete(line)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def next_order_number(session: AsyncSession) -> str:
    count = await session.scalar(select(func.count(CustomerOrder.id)))
    return f"ORD-{datetime.now(UTC).year}-{(count or 0) + 1:05d}"


@app.post("/api/v1/orders/checkout", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout(
    payload: CheckoutRequest,
    _: int = Depends(require_jwt),
    token: uuid.UUID = Depends(cart_token_header),
    session: AsyncSession = Depends(get_session),
) -> CustomerOrder:
    cart = await get_cart_by_token(token, session)
    if cart.status != "OPEN":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Корзина уже оформлена")
    if not cart.lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Корзина пуста")

    order = CustomerOrder(
        order_number=await next_order_number(session),
        cart_id=cart.id,
        status=OrderStatus.NEW.value,
        customer_name=payload.customer_name,
        customer_email=str(payload.customer_email),
        customer_phone=payload.customer_phone,
        delivery_address=payload.delivery_address,
        comment=payload.comment,
        total_cents=0,
    )
    for line in cart.lines:
        unit_price = line.product_snapshot["price_cents"]
        line_total = unit_price * line.quantity
        order.total_cents += line_total
        order.lines.append(
            OrderLine(
                product_id=line.product_id,
                product_name=line.product_snapshot["name"],
                sku=line.product_snapshot["sku"],
                unit_price_cents=unit_price,
                quantity=line.quantity,
                line_total_cents=line_total,
            ),
        )
    cart.status = "CHECKED_OUT"
    session.add(order)
    await session.commit()
    return await get_order_or_404(order.id, session)


def order_query():
    return select(CustomerOrder).options(selectinload(CustomerOrder.lines))


async def get_order_or_404(order_id: uuid.UUID, session: AsyncSession) -> CustomerOrder:
    order = await session.scalar(order_query().where(CustomerOrder.id == order_id))
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    return order


@app.get("/api/v1/orders", response_model=list[OrderRead])
async def list_orders(
    status_filter: OrderStatus | None = None,
    _: int = Depends(require_jwt),
    session: AsyncSession = Depends(get_session),
) -> list[CustomerOrder]:
    query = order_query().order_by(CustomerOrder.created_at.desc())
    if status_filter:
        query = query.where(CustomerOrder.status == status_filter.value)
    result = await session.scalars(query)
    return list(result.unique())


@app.get("/api/v1/orders/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID,
    _: int = Depends(require_jwt),
    session: AsyncSession = Depends(get_session),
) -> CustomerOrder:
    return await get_order_or_404(order_id, session)


@app.patch("/api/v1/orders/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    _: int = Depends(require_jwt),
    session: AsyncSession = Depends(get_session),
) -> CustomerOrder:
    order = await get_order_or_404(order_id, session)
    current_status = OrderStatus(order.status)
    if payload.status not in ALLOWED_STATUS_TRANSITIONS[current_status]:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Недопустимый переход статуса")
    order.status = payload.status.value
    await session.commit()
    return await get_order_or_404(order.id, session)
