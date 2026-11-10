# Roadmap до первого заработка

Публичная копия раздела из README продукта FuncFund (для комиссии; исходный репозиторий продукта private).

Демо: https://funcfund.ru


Цель: от текущего состояния к первым **10 оплатам Premium** за 8 недель и **50–100 платящих (17–35k ₽ MRR)** за 14 недель.

**GTM-фокус волны 1:** DIY-инвесторы MOEX с 2+ счетами; ключевые гипотезы — готовность платить при экономии времени на сверке (H1) и успешный импорт без поддержки (H3, цель ≥80%). ARPU-якорь — **349 ₽/мес** (год **2 990 ₽** — пока не в каталоге планов). Primary client — **mobile (Expo/PWA)**; `frontend/` — legacy. Прод **funcfund.ru**, эквайринг, legal, Сбер+Т, цена Premium ✅. Остаются: ещё импорты, рекуррент по необходимости, бета ≥5.

Приоритеты: `P0` — блокер запуска, `P1` — критично для удержания, `P2` — важно, `P3` — после запуска.

Легенда статусов: ✅ готово · 🟡 в работе · ⬜ не начато

### Фаза 0. Production-readiness (недели 1–2)

| # | Статус | Задача | Модуль / файлы | Приоритет | Оценка |
|---|---|---|---|---|---|
| 0.1 | ✅ | API-gateway на Traefik для `/gateway/*` (фронт ожидает префикс `/gateway`) | `microservices/infra/docker-compose.yaml` | P0 | 2 д |
| 0.2 | ✅ | Email-верификация, reset-password, refresh-token, `UserStatus` | `user/`, `domain/`, changelog `004`/`006` | P0 | 3 д |
| 0.3 | ✅ | Схема данных: `subscriptions`, `payments`, `notification_settings`, `email_verification_tokens` (PG/Liquibase) + `portfolio_snapshots` (ClickHouse) | `db/.../changelog/` (`004`, `005`), `infra/clickhouse/init/` | P0 | 1 д |
| 0.4 | ✅ | WS-снапшот портфеля: биржевые активы из Redis; валюты/металлы/депозиты через `valuation`; live-обновления металлов (pub/sub) | `ws/`, `valuation/` | P1 | 2 д |
| 0.5 | ✅ | Структурные логи, OpenTelemetry трейсинг, Sentry на фронте | `observability/`, `infra/` (Prometheus/Grafana/Tempo/Loki), `frontend/src/observability/` | P1 | 2 д |
| 0.6a | ✅ | Backup job PostgreSQL + ClickHouse | `microservices/backup/` | P0 | — |
| 0.6b | 🟡 | Прод-домен **funcfund.ru** + LE ✅; автобэкапы в проде — добить | `infra/` | P0 | 0.5 д |
| 0.7 | ⬜ | Шифрование чувствительных полей БД через `pgcrypto` (email, кошельки, API-ключи) | `db/`, `domain/` | P0 | 1 д |

> **0.3:** исторические снапшоты — в **ClickHouse**, не в PostgreSQL.  
> **0.4:** расчёт стоимости вынесен в библиотеку `valuation` (используется `portfolio` и `ws`).  
> **0.5:** стек observability в compose + Sentry на фронте готовы; прод-DSN/sampling — по мере выката.  
> **0.6:** backup job в репозитории есть; прод **funcfund.ru** / `api.funcfund.ru` + Let's Encrypt — есть; автобэкапы в проде — нет.

### Фаза 1. MVP-ценность (недели 3–6)

| # | Статус | Задача | Модуль / файлы | Приоритет | Оценка |
|---|---|---|---|---|---|
| 1.0 | ✅ | Импорт **Сбер** (HTML-отчёт), `POST /api/v1/portfolios/imports/assets` | `portfolio/.../importer/SberBrokerHtmlPortfolioImportParser.kt` | P0 | — |
| 1.1 | ✅ | **Т-Инвестиции** — API connect + sync (не только stub-парсер) | `portfolio/.../integration/tinkoff/`, `mobile/.../tinkoff-connect*` | P0 | — |
| 1.2 | ⬜ | Парсер **Альфа-Инвестиции** (CSV); stub в каталоге sources | `portfolio/.../importer/AlfaBrokerPortfolioImportParser.kt` | P0 | 3 д |
| 1.3 | ✅ | Парсер **ВТБ Мои Инвестиции** (XLSX, плановые остатки) | `portfolio/.../importer/VtbBrokerXlsxPortfolioImportParser.kt` | P0 | — |
| 1.4 | ⬜ | Парсер **Binance CSV** (история + текущие балансы) | `portfolio/.../importer/BinanceCsvImportParser.kt` | P0 | 3 д |
| 1.5 | ⬜ | Generic CSV-importer с UI-мэппером колонок на `PatchPortfolioDto` | `portfolio/`, `mobile/` | P1 | 3 д |
| 1.6 | ✅ | API `/portfolios/imports/sources` + logos + seed catalog | `api/openapi-specs/portfolio-api.yaml`, `portfolio/.../ImportSourceCatalog.kt`, `db/.../010-create-import-source-catalog.xml`, `mobile/.../import-sources-api.ts` | P1 | — |
| 1.7 | ⬜ | Watch-only крипто-адреса (BTC/ETH/TON): fetcher тянет баланс, маппинг в `CRYPTO_CURRENCY` | `fetcher/.../adapter/wallets/`, `domain/` | P1 | 5 д |
| 1.8 | ✅ | Снапшоты портфеля по расписанию (запись в ClickHouse, воркер + метрики) | `portfolio/.../snapshot/`, `infra/clickhouse/init/` | P0 | 2 д |
| 1.9 | ✅ | API `/portfolios/{id}/history?period=1M/3M/YTD/1Y` с агрегацией (`byClass`, summary; Premium gating) | `portfolio/.../history/`, `portfolio/.../snapshot/ClickHouseSnapshotHistoryReader.kt`, `api/openapi-specs/portfolio-api.yaml` | P0 | 2 д |
| 1.10 | 🟡 | Charts/periods на mobile (sparkline); web `recharts` + бенчмарки (IMOEX, RGBI, BTC) — ⬜ | `mobile/src/features/portfolio/`, `frontend/src/` | P0 | 4 д |
| 1.11 | 🟡 | Analytics v2: структура по классам / summary ✅; TWR, YoY/QoQ — ⬜ | `valuation/` (`PortfolioClassSummary`), `portfolio/` | P1 | 5 д |
| 1.12 | ⬜ | Декомпозиция legacy `frontend/src/App.jsx` (~1800 строк); product UI — `mobile/` | `frontend/src/features/*`, `mobile/src/features/*` | P1 | 3 д |
| 1.13 | ✅ | Mobile MVP: auth, dashboard+WS, import Сбер, premium checkout, history gating | `mobile/src/features/{auth,portfolio,import,premium,billing}/` | P0 | — |
| 1.14 | ✅ | Ручные активы на mobile: create/edit/delete (MOEX/валюта/крипта/вклад/металл), picker sheets | `mobile/.../manual-assets/`, `mobile/.../dictionary/` | P0 | — |
| 1.15 | ✅ | Dictionary: search/lookup + shortName в индексе; batch `ids`-lookup; OpenAPI `/assets/lookup`, `/currencies` | `dictionary/`, `indexer/` (schema v3), `search/`, `api/.../dictionary-api.yaml` | P0 | — |
| 1.16 | ✅ | Точечное удаление позиций (STOCK/BOND/ETF/ОФЗ/crypto) — без wipe всей категории; import REPLACE через placeholder | `portfolio/.../impl/*Service.kt`, `db/.../*Repository.kt`, `ImportReplace.kt` | P0 | — |
| 1.17 | ✅ | MOEX fetcher: классификация ETF vs stock, price resolver, meta `shortName` → Redis/index | `fetcher/.../moex/`, `indexer/.../AssetDocumentWriter.kt` | P1 | — |
| 1.18 | ✅ | OAuth **Яндекс** + **VK ID**: `GET /auth/providers`, exchange code → JWT, `oauth_identities`, PKCE (VK), mobile social buttons + `/redirect_url` | `user/.../oauth/`, `db/.../017-create-oauth-identities.xml`, `mobile/.../auth/`, `api/.../user-api.yaml` | P1 | — |

> **1.14–1.16:** закрывают DIY-путь «добавить бумагу без импорта» и критичные баги wipe-on-delete.  
> **1.15:** на экранах активов displayName через lookup; поиск MOEX — typed parallel (STOCK/BOND/ETF/OFZ).  
> **1.18:** clientId/authorize/redirect отдаёт бэкенд; секреты — только env (`YANDEX_OAUTH_*`, `VK_OAUTH_*`). Google — отдельно (фаза 4).

### Фаза 2. Монетизация и legal (недели 7–8) — **первый доход**

| # | Статус | Задача | Модуль / файлы | Приоритет | Оценка |
|---|---|---|---|---|---|
| 2.1 | ✅ | Сервис `billing`: планы, подписки, платежи, webhook events (таблицы PG + OpenAPI) | `microservices/billing/`, `settings.gradle.kts` | P0 | 3 д |
| 2.2 | 🟡 | **ЮKassa** эквайринг / one-shot ✅; рекуррент + СБП + `save_payment_method` + trial 7–14 дней — ⬜ (не блокер пилота) | `billing/.../adapter/yookassa/`, `CheckoutService.kt` | P1 | 4 д |
| 2.3 | 🟡 | Webhook `/webhooks/yookassa` с идемпотентностью ✅; HMAC-подпись — по требованиям прод-кабинета | `billing/` | P1 | 1 д |
| 2.4 | ✅ | Entitlement middleware в WebFlux + Redis-cache активных подписок | `security/entitlement/`, `cache/` | P0 | 2 д |
| 2.5 | 🟡 | Gating: >1 источника импорта + **`/history`** — Premium ✅; экспорт/алерты — ⬜ | `portfolio/`, `ImportEntitlementService.kt`, `mobile/` | P0 | 1 д |
| 2.6 | ✅ | Redirect checkout через ЮKassa (`createCheckout` → confirmationUrl); embedded widget — не блокер (P2) | `billing/`, `mobile/.../billing/`, `frontend/src/features/billing/` | P0 | — |
| 2.7 | 🟡 | `Профиль → Подписка` / Premium UI: отмена, история чеков, смена тарифа (backend API есть; mobile Premium — частично) | `mobile/.../premium/`, `frontend/`, `billing/` | P0 | 2 д |
| 2.8 | 🟡 | Email-транзакционные: приветствие, чек, отмена, оплата; auth-письма через SMTP/Mailpit | `user/` | P0 | 1 д |
| 2.9 | ✅ | Юридическое оформление: **самозанятость/ИП**, оферта, Политика ПД *(согласие на рекуррент — когда включим рекуррент)* | параллельно | P0 | — |
| 2.10 | ⬜ | Подача в реестр операторов ПД (РКН) | параллельно | P0 | — |
| 2.11 | ✅ | Pricing: Premium **349 ₽/мес**, Pro **1 490 ₽/мес** (год **2 990 ₽** — ещё не в `plans[]`) | `billing/.../application.properties`, `frontend/.../plans.js`, `mobile/.../premium-screen.tsx` | P0 | — |

### Фаза 3. Рост и удержание (недели 9–14)

| # | Статус | Задача | Модуль / файлы | Приоритет | Оценка |
|---|---|---|---|---|---|
| 3.1 | ⬜ | SEO-лендинг + блог (SSR на Astro или Next.js) — 5 стартовых статей по custdev-запросам | новый проект `landing/` | P1 | 1 нед |
| 3.2 | ⬜ | Алерты: отклонение структуры от цели, всплеск цены, новости эмитента → email + Telegram-бот | `notification-service`, `analytics-events/` | P1 | 1 нед |
| 3.3 | ⬜ | Telegram-бот: уведомления, быстрый баланс, подтверждение платежей | новый `telegram-bot/` | P1 | 4 д |
| 3.4 | ⬜ | Рекомендательный движок v1 (Sharpe, concentration, currency-exposure, rebalance) — честные формулы | `analytics-events/` | P2 | 1 нед |
| 3.5 | 🟡 | Product-аналитика: Grafana product-дашборд есть; PostHog funnel — нет | `observability/stack/grafana/.../product.json`, `frontend/` | P1 | 3 д |
| 3.6 | ⬜ | Реферальная программа: 1 месяц Premium в подарок за приведённого платящего | `billing/`, `user/` | P2 | 2 д |
| 3.7 | ⬜ | Superset-дашборды: MRR, retention, churn, LTV | `analytics/superset/` | P1 | 2 д |
| 3.8 | ⬜ | Экспорт портфеля (CSV, PDF-отчёт) — gated Premium | `portfolio/` | P2 | 2 д |
| 3.9 | ⬜ | Мультипортфель (для Pro): семейный/корпоративный доступ | `portfolio/`, `domain/` | P2 | 5 д |

### Фаза 4+ (после первого дохода, недели 15+)

| # | Статус | Задача | Приоритет |
|---|---|---|---|
| 4.1 | ⬜ | Mobile store release / native polish (Expo MVP уже в 1.13) | P2 |
| 4.2 | ⬜ | OAuth Google (+ доработка соц-линковки в профиле); Яндекс/VK ID — ✅ в 1.18 | P3 |
| 4.3 | ⬜ | Почтовый шлюз: парсинг отчётов брокеров из email без ручной загрузки | P2 |
| 4.4 | ⬜ | ML-рекомендации поверх v1-формул | P3 |
| 4.5 | ⬜ | B2B Pro-API для финансовых консультантов | P3 |
| 4.6 | ⬜ | Поддержка OKX / Bybit / Bitget (watch-only) | P2 |

### Контрольные точки

| Чекпоинт | Срок | KPI |
|---|---|---|
| Конец Ф0 | неделя 2 | p95 API <300ms, регистрация с верификацией, 0 P0-багов *(0.1–0.5, 0.6a, домен ✅; остались автобэкапы 0.6b и 0.7)* |
| Конец Ф1 | неделя 6 | Сбер+Т + каталог sources + history/sparkline + ручные активы/dictionary + OAuth Яндекс/VK ✅; next: ≥3-й импорт, TWR; retention D7 >25% |
| Конец Ф2 | неделя 8 | **Первые 10 оплат**; legal ✅, эквайринг ✅, цена 349 ✅, ≥2 импорта ✅; next — бета ≥5 + рекуррент по необходимости |
| Конец Ф3 | неделя 14 | **50–100 платящих, 17–35k ₽ MRR**, churn <7%, CAC < LTV/3 |
