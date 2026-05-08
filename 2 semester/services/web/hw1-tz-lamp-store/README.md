# Домашнее задание 5: панель управления в микросервисной архитектуре

Реализация интернет-магазина завода лампочек по ТЗ из `ТЗ.md`.

## Состав

- `frontend` — пользовательская часть интернет-магазина на React, React Router DOM и mock-данных.
- `catalog-service` — товары, категории, изображения, сиды 20 товаров.
- `order-service` — корзина по `X-Cart-Token`, оформление заказа, просмотр и смена статусов.
- `auth-service` — вход по email/паролю и выдача JWT.
- `admin-panel` — веб-панель администратора (вход, товары, заказы, смена статусов, выход).
- `catalog_db` и `order_db` — отдельные PostgreSQL БД.
- `postman_collection.json` — сценарий демонстрации в Postman.

## Запуск frontend

```bash
cd frontend
npm install
npm run dev
```

Приложение содержит основные пользовательские страницы: главную, каталог с фильтрами, карточку товара, корзину,
оформление заказа и страницу подтверждения. Backend для этой части не требуется, данные лежат в `src/data/products.ts`.

## Запуск backend

```bash
docker compose up --build
```

После запуска:

- Catalog API: `http://localhost:8001/docs`
- Order API: `http://localhost:8002/docs`
- Auth API: `http://localhost:8005/docs`
- Admin panel: `http://localhost:8100`
- Catalog health: `http://localhost:8001/health`
- Order health: `http://localhost:8002/health`

## Основные сценарии

1. Войти в админ-панель (`admin@example.com` / `Admin123!`) и получить JWT.
2. Получить список товаров: `GET /api/v1/products` c `Authorization: Bearer <token>`.
2. Создать корзину: `POST /api/v1/carts`.
3. Передавать полученный UUID в `X-Cart-Token`.
4. Добавить товар: `POST /api/v1/cart/items`.
5. Оформить заказ: `POST /api/v1/orders/checkout` c JWT.
6. Сменить статус заказа: `PATCH /api/v1/orders/{order_id}/status` c JWT.

Для критериев ДЗ5 защищены JWT:

- все операции с товарами (`/api/v1/products...`);
- операции с заказами (`/api/v1/orders...`).
