"""
Модуль для расчета метрик эффективности предложенного решения.
"""

import math
from typing import List, Dict, Tuple
from geometry import euclidean_distance, polygon_area, point_in_polygon


def calculate_avg_delivery_distance(
    delivery_zones: List[Dict],
    delivery_points: List[Dict]
) -> float:
    """
    Вычисляет среднее расстояние от ПВЗ до случайной точки в его зоне.
    Использует центроид зоны как приближение.
    
    Args:
        delivery_zones: Список зон доставки
        delivery_points: Список ПВЗ с координатами
    
    Returns:
        Среднее расстояние доставки
    """
    total_distance = 0.0
    total_weight = 0.0
    
    # Создаем словарь для быстрого доступа к координатам ПВЗ
    dp_locations = {dp["dp_id"]: tuple(dp["location"]) for dp in delivery_points}
    
    for zone in delivery_zones:
        dp_id = zone["dp_id"]
        polygon = [tuple(vertex) for vertex in zone["polygon"]]
        estimated_orders = zone.get("estimated_orders", 0)
        
        if dp_id not in dp_locations or not polygon:
            continue
        
        center = dp_locations[dp_id]
        
        # Вычисляем центроид многоугольника
        centroid = _polygon_centroid(polygon)
        
        # Расстояние от ПВЗ до центроида зоны
        distance = euclidean_distance(center, centroid)
        
        # Взвешиваем по количеству заказов
        total_distance += distance * estimated_orders
        total_weight += estimated_orders
    
    if total_weight == 0:
        return 0.0
    
    return total_distance / total_weight


def calculate_coverage_efficiency(
    historical_orders: List[Dict],
    delivery_zones: List[Dict]
) -> float:
    """
    Вычисляет долю исторических заказов, попавших в какую-либо зону доставки.
    
    Args:
        historical_orders: Список исторических заказов
        delivery_zones: Список зон доставки
    
    Returns:
        Доля покрытых заказов (от 0 до 1)
    """
    if not historical_orders:
        return 0.0
    
    covered_count = 0
    
    for order in historical_orders:
        delivery_point = tuple(order["delivery_point"])
        
        # Проверяем, попадает ли точка в какую-либо зону
        for zone in delivery_zones:
            polygon = [tuple(vertex) for vertex in zone["polygon"]]
            if point_in_polygon(delivery_point, polygon):
                covered_count += 1
                break
    
    return covered_count / len(historical_orders)


def calculate_load_imbalance(
    delivery_zones: List[Dict]
) -> float:
    """
    Вычисляет коэффициент вариации нагрузки на ПВЗ.
    Коэффициент вариации = стандартное отклонение / среднее значение.
    
    Args:
        delivery_zones: Список зон доставки с оценкой количества заказов
    
    Returns:
        Коэффициент вариации нагрузки
    """
    if not delivery_zones:
        return 0.0
    
    loads = [zone.get("estimated_orders", 0) for zone in delivery_zones]
    
    # Фильтруем нулевые нагрузки
    loads = [load for load in loads if load > 0]
    
    if not loads:
        return 0.0
    
    mean_load = sum(loads) / len(loads)
    
    if mean_load == 0:
        return 0.0
    
    # Вычисляем стандартное отклонение
    variance = sum((load - mean_load) ** 2 for load in loads) / len(loads)
    std_dev = math.sqrt(variance)
    
    # Коэффициент вариации
    return std_dev / mean_load


def _polygon_centroid(polygon: List[Tuple[float, float]]) -> Tuple[float, float]:
    """
    Вычисляет центроид (центр масс) многоугольника.
    
    Args:
        polygon: Список вершин многоугольника
    
    Returns:
        Координаты центроида (x, y)
    """
    if not polygon:
        return (0.0, 0.0)
    
    n = len(polygon)
    if n == 1:
        return polygon[0]
    
    area = polygon_area(polygon)
    if area == 0:
        # Если площадь нулевая, возвращаем среднее арифметическое вершин
        x_sum = sum(p[0] for p in polygon)
        y_sum = sum(p[1] for p in polygon)
        return (x_sum / n, y_sum / n)
    
    cx = 0.0
    cy = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        cross = polygon[i][0] * polygon[j][1] - polygon[j][0] * polygon[i][1]
        cx += (polygon[i][0] + polygon[j][0]) * cross
        cy += (polygon[i][1] + polygon[j][1]) * cross
    
    cx /= (6.0 * area)
    cy /= (6.0 * area)
    
    return (cx, cy)

