# БД микросервиса управления заказами (`order-service`)

СУБД: PostgreSQL (рекомендуется). Схема: `orders`.

## Таблица `cart`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | Идентификатор корзины |
| cart_token | UUID | UNIQUE, NOT NULL | Токен для гостя (`X-Cart-Token`) |
| status | VARCHAR(16) | NOT NULL, default 'OPEN' | `OPEN` / `CHECKED_OUT` / `ABANDONED` |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() | |

## Таблица `cart_line`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| cart_id | UUID | FK → cart(id) ON DELETE CASCADE, NOT NULL | |
| product_id | UUID | NOT NULL | Ссылка на товар в каталоге (без FK между БД) |
| product_snapshot | JSONB | NOT NULL | Копия названия/SKU/цены на момент добавления |
| quantity | INTEGER | NOT NULL, CHECK > 0 | |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() | |

Уникальный индекс: `(cart_id, product_id)` — одна строка на товар в корзине.

## Таблица `customer_order`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | Номер заказа |
| order_number | VARCHAR(32) | UNIQUE, NOT NULL | Человекочитаемый номер (например ORD-2026-00001) |
| cart_id | UUID | FK → cart(id) | Исходная корзина |
| status | VARCHAR(32) | NOT NULL | См. ТЗ: NEW, CONFIRMED, … |
| customer_name | VARCHAR(255) | NOT NULL | |
| customer_email | VARCHAR(255) | NOT NULL | |
| customer_phone | VARCHAR(32) | NOT NULL | |
| delivery_address | TEXT | NOT NULL | |
| comment | TEXT | | |
| total_cents | INTEGER | NOT NULL | Итог в копейках |
| currency | CHAR(3) | NOT NULL, default 'RUB' | |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() | |

Индексы: `(status)`, `(customer_email)`, `(created_at DESC)`.

## Таблица `order_line`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| order_id | UUID | FK → customer_order(id) ON DELETE CASCADE | |
| product_id | UUID | NOT NULL | |
| product_name | VARCHAR(255) | NOT NULL | Снимок |
| sku | VARCHAR(64) | NOT NULL | |
| unit_price_cents | INTEGER | NOT NULL | Цена за единицу |
| quantity | INTEGER | NOT NULL, CHECK > 0 | |
| line_total_cents | INTEGER | NOT NULL | |
