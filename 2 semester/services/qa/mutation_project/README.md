# Mutation Testing — итоговое задание

**Автор:** Царюк Артём Владимирович  
**Дисциплина:** Основы тестирования для разработчиков (МФТИ)

В этом проекте мы потренировались в mutation testing, создавая unit-тесты для модуля расчёта платежей `billing/calculator.py`.

## Исходное состояние

Стартовые тесты в `tests/test_skeleton.py` содержали только `...` (Ellipsis): pytest их пропускал как «успешные», но фактически **ничего не проверял**. Покрытие и Mutation Score были близки к нулю.

## Стратегия улучшения тестов

1. **Точные assert-ы** — проверка конкретных числовых результатов (`== 121.0`), а не расплывчатых условий вроде `> 0`.
2. **Граничные значения** — для `bulk_discount` протестированы qty = 9, 10, 19, 20; для `is_weekend_rate` — суббота и понедельник; для `compute_refund` — percentage = 0.0 и 1.0.
3. **Обе ветки каждого условия** — позитивные и негативные сценарии для всех `if/raise`.
4. **Точные тексты исключений** — `str(exc_info.value) == "..."` вместо частичного `match=`, чтобы убивать мутанты, меняющие сообщения об ошибках.
5. **Параметризация** — `@pytest.mark.parametrize` для однотипных кейсов (негативные qty, parts, percentage).
6. **Покрытие всех 20 функций** — помимо скелетных тестов добавлен `tests/test_calculator_extended.py` для функций, не экспортируемых из `billing/__init__.py`, но мутируемых mutmut.
7. **Итерации с mutmut** — после первого прогона команда `mutmut results` показала выживших мутантов; тесты дополнялись точечно до достижения целевого score.

## Что было добавлено

| Файл | Содержание |
|------|------------|
| `tests/conftest.py` | Добавление корня проекта в `sys.path` для импорта `billing` |
| `tests/test_skeleton.py` | Заполнены все заглушки; добавлены тесты купонов NEWUSER5/BLACKFRIDAY, qty=1, точные исключения |
| `tests/test_calculator_extended.py` | 41 тест для validate_coupon, split_payment, parse_iso_date, compute_refund, bulk_discount, compute_bulk_total, tax_breakdown, validate_tax_number, apply_dynamic_tax, loyalty_points_earned, apply_loyalty_discount, cap_price, round_money, is_weekend_rate |

## Работа с mutmut

```bash
make test                                          # 64 теста
mutmut run --paths-to-mutate billing --runner "python -m pytest -q"
mutmut results                                     # список выживших
mutmut show <id>                                   # diff конкретного мутанта
```

Команда `mutmut results json` отсутствует в mutmut 2.5. Файл `mut.json` генерируется из кэша после прогона:

```bash
python -c "import sqlite3, json; conn = sqlite3.connect('.mutmut-cache'); c = conn.cursor(); c.execute('SELECT status, COUNT(*) FROM Mutant GROUP BY status'); res = dict(c.fetchall()); print(json.dumps(res, indent=4))" > mut.json
```

> **Примечание:** для mutmut 2.5 потребовался Python 3.12 (на 3.13 падает из-за несовместимости pony/pickle). В задании указана таблица `mutant` (строчными), в mutmut 2.5 она называется `Mutant`.

## Итоговые метрики

| Метрика | До | После |
|---------|-----|-------|
| Mutation Score | ~0% | **97.2%** (104 killed / 107 total) |
| Branch Coverage | ~0% | **100%** (14/14 веток) |
| Line Coverage | ~0% | **100%** (86/86 строк) |
| Количество тестов | 9 (пустых) | **64** |

### Выжившие мутанты (3)

Эквивалентные мутации, не влияющие на поведение:
- `apply_coupon`: замена `""` на `"XXXX"` при отсутствии купона — оба ключа отсутствуют в словаре, скидка 0.
- `round_money`: мутации внутреннего кортежа `Decimal((0, (1,), ...))` — дают идентичный результат округления.

## Запуск

```bash
python3.12 -m venv .venv && source .venv/bin/activate
make install
make test
make htmlcov
```
