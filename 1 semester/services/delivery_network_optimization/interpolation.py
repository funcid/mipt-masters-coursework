"""
Модуль для интерполяции плотности спроса на основе исторических заказов.
Использует метод KDE (Kernel Density Estimation) для построения карты плотности.
"""

import math
from typing import List, Tuple, Dict


def gaussian_kernel(distance: float, bandwidth: float) -> float:
    """
    Гауссово ядро для оценки плотности.
    
    Args:
        distance: Расстояние от точки до центра ядра
        bandwidth: Ширина полосы пропускания (bandwidth)
    
    Returns:
        Значение ядра
    """
    if bandwidth <= 0:
        return 0.0
    return (1.0 / (bandwidth * math.sqrt(2 * math.pi))) * math.exp(-0.5 * (distance / bandwidth) ** 2)


def calculate_density_at_point(
    point: Tuple[float, float],
    orders: List[Dict],
    bandwidth: float
) -> float:
    """
    Вычисляет плотность спроса в заданной точке на основе исторических заказов.
    
    Args:
        point: Координаты точки (x, y)
        orders: Список исторических заказов
        bandwidth: Ширина полосы пропускания для KDE
    
    Returns:
        Значение плотности в точке
    """
    total_density = 0.0
    
    for order in orders:
        delivery_point = tuple(order["delivery_point"])
        weight = order.get("weight", 1.0)
        
        distance = math.sqrt(
            (point[0] - delivery_point[0]) ** 2 + 
            (point[1] - delivery_point[1]) ** 2
        )
        
        # Учитываем вес заказа при расчете плотности
        total_density += weight * gaussian_kernel(distance, bandwidth)
    
    return total_density


def create_density_grid(
    bounds: Tuple[float, float, float, float],
    resolution: float,
    orders: List[Dict],
    districts: List[Dict]
) -> Dict:
    """
    Создает растровую карту плотности спроса.
    
    Args:
        bounds: Границы области (x_min, y_min, x_max, y_max)
        resolution: Разрешение сетки (шаг между точками)
        orders: Список исторических заказов
        districts: Список районов города
    
    Returns:
        Словарь с информацией о карте плотности
    """
    x_min, y_min, x_max, y_max = bounds
    
    # Вычисляем размеры сетки
    x_steps = int((x_max - x_min) / resolution) + 1
    y_steps = int((y_max - y_min) / resolution) + 1
    
    # Автоматический выбор bandwidth на основе разрешения сетки
    # bandwidth = 2 * resolution обеспечивает плавную интерполяцию
    bandwidth = resolution * 2.0
    
    density_matrix = []
    max_density = 0.0
    
    # Вычисляем плотность для каждой ячейки сетки
    for j in range(y_steps):
        row = []
        y = y_max - j * resolution  # Начинаем с верхней границы
        
        for i in range(x_steps):
            x = x_min + i * resolution
            point = (x, y)
            
            # Вычисляем плотность только для точек внутри районов
            from geometry import point_in_any_district
            if point_in_any_district(point, districts):
                density = calculate_density_at_point(point, orders, bandwidth)
                row.append(density)
                max_density = max(max_density, density)
            else:
                row.append(0.0)
        
        density_matrix.append(row)
    
    # Нормализуем плотность от 0 до 1
    if max_density > 0:
        density_matrix = [[d / max_density for d in row] for row in density_matrix]
    
    return {
        "grid_bounds": {
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max
        },
        "resolution": resolution,
        "density_matrix": density_matrix
    }


def get_density_at_point(
    point: Tuple[float, float],
    density_map: Dict
) -> float:
    """
    Получает значение плотности в заданной точке из карты плотности.
    Использует билинейную интерполяцию для более точного результата.
    
    Args:
        point: Координаты точки (x, y)
        density_map: Карта плотности
    
    Returns:
        Значение плотности в точке
    """
    bounds = density_map["grid_bounds"]
    resolution = density_map["resolution"]
    matrix = density_map["density_matrix"]
    
    x, y = point
    x_min = bounds["x_min"]
    y_max = bounds["y_max"]  # y_max соответствует верхней границе (ось Y направлена вверх)
    
    # Вычисляем индексы в сетке
    i = (x - x_min) / resolution
    j = (y_max - y) / resolution  # Инвертируем y
    
    # Проверяем границы
    if i < 0 or j < 0:
        return 0.0
    
    i_floor = int(i)
    j_floor = int(j)
    i_ceil = min(i_floor + 1, len(matrix[0]) - 1) if matrix else 0
    j_ceil = min(j_floor + 1, len(matrix) - 1) if matrix else 0
    
    if j_floor >= len(matrix) or i_floor >= len(matrix[0]):
        return 0.0
    
    # Билинейная интерполяция
    dx = i - i_floor
    dy = j - j_floor
    
    v00 = matrix[j_floor][i_floor] if j_floor < len(matrix) and i_floor < len(matrix[0]) else 0.0
    v10 = matrix[j_floor][i_ceil] if j_floor < len(matrix) and i_ceil < len(matrix[0]) else 0.0
    v01 = matrix[j_ceil][i_floor] if j_ceil < len(matrix) and i_floor < len(matrix[0]) else 0.0
    v11 = matrix[j_ceil][i_ceil] if j_ceil < len(matrix) and i_ceil < len(matrix[0]) else 0.0
    
    # Интерполяция по x
    v0 = v00 * (1 - dx) + v10 * dx
    v1 = v01 * (1 - dx) + v11 * dx
    
    # Интерполяция по y
    return v0 * (1 - dy) + v1 * dy

