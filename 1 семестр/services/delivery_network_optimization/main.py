"""
Главный модуль для запуска оптимизации сети пунктов выдачи заказов.
Вариант 2: Оптимизация сети
"""

import json
import sys
from pathlib import Path
from optimizer import DeliveryNetworkOptimizer


def load_input_data(input_file: str) -> dict:
    """
    Загружает входные данные из JSON файла.
    
    Args:
        input_file: Путь к файлу с входными данными
    
    Returns:
        Словарь с входными данными
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: файл {input_file} не найден.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Ошибка: неверный формат JSON в файле {input_file}: {e}")
        sys.exit(1)


def save_output_data(output_data: dict, output_file: str):
    """
    Сохраняет результаты оптимизации в JSON файл.
    
    Args:
        output_data: Словарь с результатами оптимизации
        output_file: Путь к выходному файлу
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"Результаты сохранены в файл: {output_file}")
    except Exception as e:
        print(f"Ошибка при сохранении результатов: {e}")
        sys.exit(1)


def main():
    """
    Главная функция программы.
    """
    # Определяем пути к файлам
    script_dir = Path(__file__).parent
    default_input = script_dir / "example_input.json"
    default_output = script_dir / "output.json"
    
    # Получаем пути из аргументов командной строки или используем значения по умолчанию
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = str(default_input)
    
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = str(default_output)
    
    print("=" * 60)
    print("Оптимизация сети пунктов выдачи заказов")
    print("Вариант 2: Оптимизация сети")
    print("=" * 60)
    print(f"Входной файл: {input_file}")
    print(f"Выходной файл: {output_file}")
    print()
    
    # Загружаем входные данные
    print("Загрузка входных данных...")
    input_data = load_input_data(input_file)
    
    # Проверяем наличие необходимых данных
    required_keys = ["districts", "historical_orders", "existing_pickup_points", "task_parameters"]
    for key in required_keys:
        if key not in input_data:
            print(f"Ошибка: отсутствует обязательное поле '{key}' во входных данных.")
            sys.exit(1)
    
    print(f"  - Районов: {len(input_data['districts'])}")
    print(f"  - Исторических заказов: {len(input_data['historical_orders'])}")
    print(f"  - Существующих ПВЗ: {len(input_data['existing_pickup_points'])}")
    print(f"  - Новых ПВЗ для размещения: {input_data['task_parameters'].get('new_pp_count', 0)}")
    print()
    
    # Создаем оптимизатор и выполняем оптимизацию
    print("Выполнение оптимизации...")
    try:
        optimizer = DeliveryNetworkOptimizer(input_data)
        results = optimizer.optimize()
        
        print("  ✓ Карта плотности спроса создана")
        print(f"  ✓ Размещено новых ПВЗ: {len(results['new_delivery_points'])}")
        print(f"  ✓ Построено зон доставки: {len(results['delivery_zones'])}")
        print(f"  ✓ Метрики вычислены")
        print()
        
        # Выводим метрики
        metrics = results["metrics"]
        print("Метрики эффективности:")
        print(f"  - Среднее расстояние доставки: {metrics['avg_delivery_distance']}")
        print(f"  - Эффективность покрытия: {metrics['coverage_efficiency']:.2%}")
        print(f"  - Дисбаланс нагрузки: {metrics['load_imbalance']:.2f}")
        print()
        
        # Сохраняем результаты
        save_output_data(results, output_file)
        
        print("Оптимизация завершена успешно!")
        
    except Exception as e:
        print(f"Ошибка при выполнении оптимизации: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

