"""
Модуль для работы с геометрическими объектами: точки, многоугольники, расстояния.
"""

import math
from typing import List, Tuple


def euclidean_distance(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """
    Вычисляет евклидово расстояние между двумя точками.
    
    Args:
        point1: Координаты первой точки (x, y)
        point2: Координаты второй точки (x, y)
    
    Returns:
        Расстояние между точками
    """
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def point_in_polygon(point: Tuple[float, float], polygon: List[Tuple[float, float]]) -> bool:
    """
    Проверяет, находится ли точка внутри многоугольника, используя алгоритм ray casting.
    
    Args:
        point: Координаты точки (x, y)
        polygon: Список вершин многоугольника [(x1, y1), (x2, y2), ...]
    
    Returns:
        True, если точка внутри многоугольника, False иначе
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def get_polygon_bounds(polygon: List[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    """
    Вычисляет ограничивающий прямоугольник для многоугольника.
    
    Args:
        polygon: Список вершин многоугольника
    
    Returns:
        Кортеж (x_min, y_min, x_max, y_max)
    """
    if not polygon:
        return (0, 0, 0, 0)
    
    x_coords = [p[0] for p in polygon]
    y_coords = [p[1] for p in polygon]
    
    return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))


def get_all_districts_bounds(districts: List[dict]) -> Tuple[float, float, float, float]:
    """
    Вычисляет общие границы всех районов города.
    
    Args:
        districts: Список словарей с информацией о районах
    
    Returns:
        Кортеж (x_min, y_min, x_max, y_max)
    """
    if not districts:
        return (0, 0, 0, 0)
    
    all_x = []
    all_y = []
    
    for district in districts:
        polygon = [tuple(vertex) for vertex in district["polygon"]]
        x_min, y_min, x_max, y_max = get_polygon_bounds(polygon)
        all_x.extend([x_min, x_max])
        all_y.extend([y_min, y_max])
    
    return (min(all_x), min(all_y), max(all_x), max(all_y))


def point_in_any_district(point: Tuple[float, float], districts: List[dict]) -> bool:
    """
    Проверяет, находится ли точка внутри хотя бы одного из районов.
    
    Args:
        point: Координаты точки (x, y)
        districts: Список словарей с информацией о районах
    
    Returns:
        True, если точка находится в каком-либо районе
    """
    for district in districts:
        polygon = [tuple(vertex) for vertex in district["polygon"]]
        if point_in_polygon(point, polygon):
            return True
    return False


def polygon_area(polygon: List[Tuple[float, float]]) -> float:
    """
    Вычисляет площадь многоугольника по формуле шнурков (Shoelace formula).
    
    Args:
        polygon: Список вершин многоугольника
    
    Returns:
        Площадь многоугольника
    """
    if len(polygon) < 3:
        return 0.0
    
    area = 0.0
    n = len(polygon)
    for i in range(n):
        j = (i + 1) % n
        area += polygon[i][0] * polygon[j][1]
        area -= polygon[j][0] * polygon[i][1]
    
    return abs(area) / 2.0

