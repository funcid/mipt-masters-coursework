# Снимок GitHub + KPI (для отчёта НИР 3)

Дата снимка: **20.10.2026**. Источники: репозиторий [`funcid/funcfund`](https://github.com/funcid/funcfund), README roadmap, CustDev (14 интервью), Superset/Grafana product metrics (экспорт `analytics/exports/`).

## GitHub — delivery (сент–окт 2026)

| Метрика | Значение |
|---|---|
| Коммиты с 01.09.2026 | **12** (1 в сент., 11 в окт.) |
| Затронутых файлов | **~317** |
| Diff (approx) | **+16k / −4k** строк |
| Primary surface | `mobile/` (Expo/PWA) |
| Backend | Kotlin microservices + billing + portfolio + dictionary/indexer |

Ключевые поставки (по коммитам):

| Дата | Что |
|---|---|
| 28.09 | WebSocket в mobile |
| 05.10 | Billing + PWA |
| 06.10 | Каталог sources / importation; history |
| 07.10 | PWA design; balance update |
| 09–11.10 | Roadmap; edit assets; CBR; detailed assets; MOEX add + dictionary/indexer |

Репозиторий курса (артефакты ОНИТ/ВКРС): [`funcid/mipt-masters-coursework`](https://github.com/funcid/mipt-masters-coursework).

## Product KPI (целевые из roadmap)

| Чекпоинт | KPI | Статус на 20.10 |
|---|---|---|
| Ф0 prod-ready | p95 API, регистрация, 0 P0 | частично (0.6b–0.7 открыты) |
| Ф1 MVP-ценность | ≥1 импорт + history + manual assets | ✅ Сбер; next ≥2–3 парсера |
| Ф2 монетизация | первые **10 оплат** | эквайринг ✅, прод-цены/бета — впереди |
| Ф3 рост | **50–100** платящих, **17–35k ₽ MRR**, churn &lt;7% | горизонт 4 сем. |

Якоря юнит-экономики (из 5.2 / README):

- ARPU-якорь: **~3 000 ₽/год** (год **2 990 ₽**; мес Premium **349 ₽**)
- Demo checkout сейчас: **10 ₽** (нужно синхронизировать с прод-ценами)
- H3 (импорт): цель **≥80%** успешных онбордингов без поддержки
- H1 (готовность платить): конверсия trial→pay — измерить на бете/пилоте

## CustDev baseline (до НИР 3)

- n = **14** B2C-интервью
- 2+ банка/брокера у респондентов
- важность автоагрегации **9.1/10**
- ICP волны 1: DIY MOEX, боль ручной сверки

## Observability / product metrics

- Grafana product-дашборд + экспорт Superset `Project_Metrics` / `Users Total` (счётчик `users.registered_at`)
- PostHog funnel — ещё нет (roadmap 3.5)
- Для отчёта: зафиксировать **число зарегистрированных** и **число успешных импортов Сбер** на дату сдачи (выгрузить из PG / Grafana)

## Как использовать в отчёте

1. Раздел «результаты» — таблица поставок GitHub + статус БФТ.
2. Раздел «методика ДС» — пайплайн данных (fetcher → valuation → ClickHouse snapshots → history API) и метрики качества.
3. Раздел «пилот» — KPI Ф2/Ф3 как критерии успеха эксперимента 4 семестра; в НИР 3 — промежуточные (бета, импорт success rate).
