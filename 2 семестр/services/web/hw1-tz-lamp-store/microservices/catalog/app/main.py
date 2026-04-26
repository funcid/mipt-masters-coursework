import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import SessionLocal, get_session, init_db
from app.models import Category, Product, ProductImage
from app.schemas import CategoryCreate, CategoryRead, ProductCreate, ProductRead, ProductUpdate
from app.seed import seed_catalog


def error_response(code: str, message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    async with SessionLocal() as session:
        await seed_catalog(session)
    yield


app = FastAPI(title="Catalog Service", version="1.0.0", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == status.HTTP_404_NOT_FOUND else "request_error"
    return error_response(code, str(exc.detail), exc.status_code)


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(_: Request, __: IntegrityError) -> JSONResponse:
    return error_response("conflict", "Нарушено ограничение уникальности или внешнего ключа", status.HTTP_409_CONFLICT)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/categories", response_model=list[CategoryRead])
async def list_categories(session: AsyncSession = Depends(get_session)) -> list[Category]:
    result = await session.scalars(select(Category).order_by(Category.name))
    return list(result)


@app.post("/api/v1/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, session: AsyncSession = Depends(get_session)) -> Category:
    category = Category(**payload.model_dump())
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


def product_query():
    return select(Product).options(selectinload(Product.category), selectinload(Product.images))


@app.get("/api/v1/products", response_model=list[ProductRead])
async def list_products(
    category_slug: str | None = None,
    base_type: str | None = None,
    active_only: bool = True,
    q: str | None = Query(default=None, min_length=2),
    session: AsyncSession = Depends(get_session),
) -> list[Product]:
    query = product_query().join(Product.category)
    if active_only:
        query = query.where(Product.is_active.is_(True))
    if category_slug:
        query = query.where(Category.slug == category_slug)
    if base_type:
        query = query.where(Product.base_type == base_type)
    if q:
        query = query.where(Product.name.ilike(f"%{q}%"))

    result = await session.scalars(query.order_by(Product.name))
    return list(result.unique())


async def get_product_or_404(product_id: uuid.UUID, session: AsyncSession) -> Product:
    product = await session.scalar(product_query().where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")
    return product


@app.get("/api/v1/products/{product_id}", response_model=ProductRead)
async def get_product(product_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Product:
    return await get_product_or_404(product_id, session)


@app.post("/api/v1/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, session: AsyncSession = Depends(get_session)) -> Product:
    image_urls = payload.image_urls
    product = Product(**payload.model_dump(exclude={"image_urls"}))
    product.images = [ProductImage(url=url, sort_order=index) for index, url in enumerate(image_urls)]
    session.add(product)
    await session.commit()
    return await get_product_or_404(product.id, session)


@app.put("/api/v1/products/{product_id}", response_model=ProductRead)
async def replace_product(
    product_id: uuid.UUID,
    payload: ProductCreate,
    session: AsyncSession = Depends(get_session),
) -> Product:
    product = await get_product_or_404(product_id, session)
    for key, value in payload.model_dump(exclude={"image_urls"}).items():
        setattr(product, key, value)
    product.images = [ProductImage(url=url, sort_order=index) for index, url in enumerate(payload.image_urls)]
    await session.commit()
    return await get_product_or_404(product.id, session)


@app.patch("/api/v1/products/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    session: AsyncSession = Depends(get_session),
) -> Product:
    product = await get_product_or_404(product_id, session)
    data = payload.model_dump(exclude_unset=True)
    image_urls = data.pop("image_urls", None)
    for key, value in data.items():
        setattr(product, key, value)
    if image_urls is not None:
        product.images = [ProductImage(url=url, sort_order=index) for index, url in enumerate(image_urls)]
    await session.commit()
    return await get_product_or_404(product.id, session)


@app.delete("/api/v1/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_product(product_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Response:
    product = await get_product_or_404(product_id, session)
    product.is_active = False
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
