# Google Sheets UI

Пример таблицы: https://docs.google.com/spreadsheets/d/1SOthDDViugmRni2U_Mm5YCNfrZ4B7Tmg_sAlx22yCxw/edit

## Быстрый старт

1. Откройте пример выше (или создайте копию: `Файл → Создать копию`).
2. `Расширения → Apps Script`, вставьте код из `Code.gs`.
3. Сохраните проект, обновите таблицу — появится меню **Expense Analytics**.
4. В листе `Settings` укажите публичный URL Gateway (ngrok / cloudflared / VPS).
5. Выполните: **Login → Sync budgets → Sync transactions → Load summary report**.

> Для локальной демонстрации пробросьте порт:  
> `ngrok http 8080` и положите HTTPS URL в `API_BASE_URL`.

## Структура листов

### Settings
| Key | Value |
|-----|-------|
| API_BASE_URL | https://xxxx.ngrok-free.app |
| EMAIL | demo@example.com |
| PASSWORD | secret123 |
| NAME | Demo User |
| TOKEN | _(заполнится скриптом)_ |
| REPORT_FROM | 2024-01-01 |
| REPORT_TO | 2024-12-31 |

### Transactions
| date | amount | category | description | status |
|------|--------|----------|-------------|--------|
| 2024-05-01 | 450 | food | Магазин | |

### Budgets
| category | limit_amount | period | status |
|----------|--------------|--------|--------|
| food | 15000 | monthly | |

### Report
Заполняется функцией `loadReport`.

## Демо-сценарий для проверки

1. Внести бюджет `food = 1000`.
2. Добавить транзакцию `food / 400` → status `OK`.
3. Добавить транзакцию `food / 700` → status с `budget_exceeded`.
4. Загрузить отчёт — увидеть категории, % бюджета и `cache_hit=true` на повторном вызове.
