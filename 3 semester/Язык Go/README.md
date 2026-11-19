# Язык Go

## Итоговый проект

**[expense-analytics](expense-analytics/)** — система аналитики личных трат

- Clean Architecture
- Gateway (HTTP) + Ledger (gRPC) + Auth (gRPC)
- PostgreSQL (Goose) + Redis (кеш отчётов)
- JWT, CSV import/export, bulk worker-pool
- Google Sheets UI (Apps Script)
- Docker Compose, OpenAPI, тесты + `cover.out`
