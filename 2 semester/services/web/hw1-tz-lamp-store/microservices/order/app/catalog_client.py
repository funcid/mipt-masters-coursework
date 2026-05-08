import uuid

import httpx
from fastapi import HTTPException, status

from app.config import settings


async def fetch_product_snapshot(product_id: uuid.UUID) -> dict:
    url = f"{settings.catalog_service_url}/api/v1/products/{product_id}"
    headers = {"X-Internal-Service-Token": settings.internal_service_token}
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="catalog-service недоступен",
            ) from exc

    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден в каталоге")
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Ошибка ответа catalog-service")

    product = response.json()
    if not product.get("is_active"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Товар снят с витрины")
    if product.get("stock_qty", 0) <= 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Товара нет в наличии")

    return {
        "id": str(product["id"]),
        "sku": product["sku"],
        "name": product["name"],
        "price_cents": product["price_cents"],
        "currency": product.get("currency", "RUB"),
    }
