# БД микросервиса управления товарами (`catalog-service`)

СУБД на выбор исполнителя (PostgreSQL рекомендуется). Схема: `catalog`.

## Таблица `category`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK, default gen_random_uuid() | Идентификатор |
| slug | VARCHAR(64) | UNIQUE, NOT NULL | URL-имя |
| name | VARCHAR(128) | NOT NULL | Название |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | Создание |

## Таблица `product`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | Идентификатор |
| sku | VARCHAR(64) | UNIQUE, NOT NULL | Артикул |
| name | VARCHAR(255) | NOT NULL | Название |
| description | TEXT | | HTML/текст |
| category_id | UUID | FK → category(id), NOT NULL | Категория |
| price_cents | INTEGER | NOT NULL, CHECK ≥ 0 | Цена в копейках |
| currency | CHAR(3) | NOT NULL, default 'RUB' | Валюта |
| watt | INTEGER | | Мощность (Вт) |
| base_type | VARCHAR(16) | | Цоколь (E27, E14, GU10, …) |
| color_temp_k | INTEGER | | Цветовая температура (K), nullable |
| lifetime_hours | INTEGER | | Срок службы (ч), nullable |
| stock_qty | INTEGER | NOT NULL, default 0 | Остаток (упрощённо) |
| is_active | BOOLEAN | NOT NULL, default true | На витрине |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() | |

Индексы: `(category_id)`, `(is_active)`, полнотекст по `name` — опционально.

## Таблица `product_image`

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| id | UUID | PK | |
| product_id | UUID | FK → product(id) ON DELETE CASCADE | |
| url | VARCHAR(1024) | NOT NULL | Ссылка на файл/CDN |
| sort_order | SMALLINT | NOT NULL, default 0 | Порядок в галерее |

## Начальные данные

20 товаров из раздела 8 основного `ТЗ.md` — сидировать скриптом миграции.
