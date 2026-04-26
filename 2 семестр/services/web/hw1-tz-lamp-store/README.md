# Домашнее задание 2: микросервисы товаров и заказов

Реализация интернет-магазина завода лампочек по ТЗ из `ТЗ.md`.

## Состав

- `catalog-service` — товары, категории, изображения, сиды 20 товаров.
- `order-service` — корзина по `X-Cart-Token`, оформление заказа, просмотр и смена статусов.
- `catalog_db` и `order_db` — отдельные PostgreSQL БД.
- `postman_collection.json` — сценарий демонстрации в Postman.

## Запуск

```bash
docker compose up --build
```

После запуска:

- Catalog API: `http://localhost:8001/docs`
- Order API: `http://localhost:8002/docs`
- Catalog health: `http://localhost:8001/health`
- Order health: `http://localhost:8002/health`

## Основные сценарии

1. Получить список товаров: `GET /api/v1/products`.
2. Создать корзину: `POST /api/v1/carts`.
3. Передавать полученный UUID в `X-Cart-Token`.
4. Добавить товар: `POST /api/v1/cart/items`.
5. Оформить заказ: `POST /api/v1/orders/checkout`.
6. Сменить статус заказа: `PATCH /api/v1/orders/{order_id}/status`.

Аутентификация намеренно не добавлена: по условию ДЗ2 операции панели управления выполняются без авторизации.
