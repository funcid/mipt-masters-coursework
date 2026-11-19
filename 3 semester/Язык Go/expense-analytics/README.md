# Expense Analytics

Микросервисная система учёта и анализа личных трат на Go.  
**Clean Architecture · gRPC · JWT · PostgreSQL · Redis · Google Sheets UI**

```
 Google Sheets ──HTTP/JWT──▶ Gateway ──gRPC──▶ Auth
                               │
                               └──gRPC──▶ Ledger ──▶ PostgreSQL
                                              └──▶ Redis (report cache)
```

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build -d
curl http://localhost:8080/ping
# {"status":"ok"}
```

Сервисы: `gateway:8080`, `ledger:9091`, `auth:9092`, `migrate` (one-shot Goose), `postgres:5432`, `redis:6379`.

## Архитектура

| Слой | Путь | Роль |
|------|------|------|
| Domain | `internal/domain` | сущности, правила, порты |
| Use case | `internal/usecase/*` | бизнес-сценарии |
| Adapters | `internal/adapter/*` | HTTP, gRPC, Postgres, Redis |
| Delivery | `cmd/{gateway,ledger,auth}` | точки входа |

Принципы: зависимости направлены внутрь; домен не знает про HTTP/SQL/Redis.

## API (кратко)

OpenAPI: [`docs/openapi.yaml`](docs/openapi.yaml)

### Регистрация и JWT

```bash
curl -s -X POST http://localhost:8080/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"secret123","name":"Demo"}'

TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com","password":"secret123"}' | jq -r .access_token)
```

### Бюджеты и транзакции

```bash
curl -s -X POST http://localhost:8080/api/budgets \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"category":"food","limit_amount":1000,"period":"monthly"}'

curl -s -X POST http://localhost:8080/api/transactions \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"amount":400,"category":"food","description":"lunch","date":"2024-05-01"}'

# превышение бюджета → HTTP 409
curl -s -X POST http://localhost:8080/api/transactions \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"amount":700,"category":"food","description":"dinner","date":"2024-05-02"}'
```

### Отчёт + Redis cache hit/miss

```bash
curl -s "http://localhost:8080/api/reports/summary?from=2024-05-01&to=2024-05-31" \
  -H "Authorization: Bearer $TOKEN"
# первый вызов: "cache_hit": false  (miss в логах ledger)
# второй вызов: "cache_hit": true   (hit в логах ledger)
```

### CSV

```bash
# экспорт
curl -s "http://localhost:8080/api/transactions/export.csv" \
  -H "Authorization: Bearer $TOKEN" -o out.csv

# импорт
curl -s -X POST http://localhost:8080/api/transactions/import \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"csv\":$(jq -Rs . < samples/transactions.csv)}"

# concurrent bulk
curl -s -X POST http://localhost:8080/api/transactions/bulk \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"workers":8,"items":[{"amount":10,"category":"misc","date":"2024-05-10"}]}'
```

Единый формат ошибок:

```json
{"error":"validation_error","message":"..."}
```

Коды: `201` create, `400` validation, `401` JWT, `409` budget/conflict, `500` internal.

## Тесты

```bash
go test ./... -coverprofile=cover.out
go tool cover -func=cover.out
go test ./internal/usecase/transaction -race
```

Покрыты: доменные table-driven тесты, use case (budget exceeded + bulk), HTTP-хендлеры Gateway.

## Google Sheets

Готовый пример таблицы:  
https://docs.google.com/spreadsheets/d/1SOthDDViugmRni2U_Mm5YCNfrZ4B7Tmg_sAlx22yCxw/edit

Скрипт и пошаговая инструкция: [`google-sheets/`](google-sheets/) (`Code.gs`).

Минимум две операции UI:
1. **Sync new transactions / Sync budgets** — запись из таблицы в API;
2. **Load summary report** — выгрузка отчёта на лист `Report`.

Подключение:
1. Откройте таблицу → `Расширения → Apps Script` → вставьте `google-sheets/Code.gs` → сохраните.
2. Пробросьте Gateway наружу: `ngrok http 8080`.
3. В листе `Settings` укажите `API_BASE_URL`, `EMAIL`, `PASSWORD`.
4. Меню **Expense Analytics**: Login → Sync budgets → Sync transactions → Load summary report.

## Переменные окружения

См. [`.env.example`](.env.example). Секреты и DSN только из env.

## Структура репозитория

```
cmd/                  # gateway / ledger / auth
api/proto             # gRPC контракты
api/gen               # сгенерированный код
internal/domain       # чистый домен
internal/usecase      # сценарии
internal/adapter      # postgres, redis, grpc, http
migrations            # Goose SQL (дублируются в adapter для embed)
docs/openapi.yaml
google-sheets/
samples/
docker-compose.yml
```

## Критерии задания → реализация

| Критерий | Где |
|----------|-----|
| Compose + `/ping` | `docker-compose.yml` |
| POST/GET budgets & transactions | Gateway → Ledger gRPC |
| Goose миграции + upsert бюджета | `migrations/`, `BudgetRepo.Upsert` |
| Budget reject + report + CSV | use case + `/api/reports/summary` + export/import |
| Unit + HTTP tests + cover.out | `*_test.go` |
| Redis cache TTL + hit/miss logs | `report.Service` + slog |
| gRPC Ledger отдельным процессом | `cmd/ledger` |
| JWT middleware | Gateway + Auth |
| Google Sheets | `google-sheets/Code.gs` |
| CSV import / bulk worker-pool | `csvio` + `BulkCreate` |

---

Сделано как итоговый проект курса «Язык Go»: микросервисы, синхронизация, горутины (bulk pool), clean architecture.
