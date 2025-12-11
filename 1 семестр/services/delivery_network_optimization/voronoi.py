"""
Модуль для построения зон доставки на основе диаграммы Вороного.
Реализует упрощенный алгоритм построения зон с учетом ограничения по радиусу доставки.
"""

import math
from typing import List, Tuple, Dict
from geometry import euclidean_distance, point_in_any_district, get_polygon_bounds


def voronoi_zone_for_point(
    center: Tuple[float, float],
    all_centers: List[Tuple[float, float]],
    bounds: Tuple[float, float, float, float],
    max_radius: float,
    districts: List[Dict],
    resolution: float = 10.0
) -> List[Tuple[float, float]]:
    """
    Строит зону Вороного для заданной точки с учетом ограничения по радиусу.
    Использует алгоритм на основе сетки для упрощения вычислений.
    
    Args:
        center: Центр зоны (координаты ПВЗ)
        all_centers: Список всех центров (включая текущий)
        bounds: Границы области (x_min, y_min, x_max, y_max)
        max_radius: Максимальный радиус доставки
        districts: Список районов города
        resolution: Разрешение для построения границы зоны
    
    Returns:
        Список вершин многоугольника зоны доставки
    """
    x_min, y_min, x_max, y_max = bounds
    
    # Создаем сетку точек для определения границы зоны
    zone_points = []
    
    # Проверяем точки на границе области
    # Верхняя и нижняя границы
    for x in range(int(x_min), int(x_max) + 1, int(resolution)):
        for y in [y_min, y_max]:
            point = (float(x), float(y))
            if _is_closest_to_center(point, center, all_centers, max_radius):
                if point_in_any_district(point, districts):
                    zone_points.append(point)
    
        # Проверяем промежуточные точки по y
        for y in range(int(y_min), int(y_max) + 1, int(resolution)):
            point = (float(x), float(y))
            if _is_closest_to_center(point, center, all_centers, max_radius):
                if point_in_any_district(point, districts):
                    zone_points.append(point)
    
    # Левая и правая границы
    for y in range(int(y_min), int(y_max) + 1, int(resolution)):
        for x in [x_min, x_max]:
            point = (float(x), float(y))
            if _is_closest_to_center(point, center, all_centers, max_radius):
                if point_in_any_district(point, districts):
                    zone_points.append(point)
    
    # Если точек недостаточно, используем упрощенный подход
    if len(zone_points) < 3:
        return _create_simple_zone(center, max_radius, bounds, districts)
    
    # Сортируем точки по углу относительно центра для построения выпуклой оболочки
    zone_points = _sort_points_by_angle(zone_points, center)
    
    # Строим выпуклую оболочку
    return _convex_hull(zone_points)


def _is_closest_to_center(
    point: Tuple[float, float],
    center: Tuple[float, float],
    all_centers: List[Tuple[float, float]],
    max_radius: float
) -> bool:
    """
    Проверяет, является ли точка ближайшей к заданному центру среди всех центров.
    
    Args:
        point: Проверяемая точка
        center: Центр, для которого проверяем
        all_centers: Все центры
        max_radius: Максимальный радиус доставки
    
    Returns:
        True, если точка ближайшая к center и в пределах max_radius
    """
    dist_to_center = euclidean_distance(point, center)
    
    if dist_to_center > max_radius:
        return False
    
    for other_center in all_centers:
        if other_center == center:
            continue
        dist_to_other = euclidean_distance(point, other_center)
        if dist_to_other < dist_to_center:
            return False
    
    return True


def _create_simple_zone(
    center: Tuple[float, float],
    max_radius: float,
    bounds: Tuple[float, float, float, float],
    districts: List[Dict]
) -> List[Tuple[float, float]]:
    """
    Создает простую круговую зону с учетом границ и районов.
    
    Args:
        center: Центр зоны
        max_radius: Радиус зоны
        bounds: Границы области
        districts: Список районов
    
    Returns:
        Список вершин многоугольника (приближение круга)
    """
    x, y = center
    x_min, y_min, x_max, y_max = bounds
    
    # Создаем многоугольник, приближающий круг
    num_points = 16
    zone_points = []
    
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        px = x + max_radius * math.cos(angle)
        py = y + max_radius * math.sin(angle)
        
        # Ограничиваем точками внутри границ и районов
        px = max(x_min, min(x_max, px))
        py = max(y_min, min(y_max, py))
        
        point = (px, py)
        if point_in_any_district(point, districts):
            zone_points.append(point)
    
    if not zone_points:
        # Если нет точек в районах, возвращаем минимальный прямоугольник
        return [
            (max(x_min, x - max_radius), max(y_min, y - max_radius)),
            (min(x_max, x + max_radius), max(y_min, y - max_radius)),
            (min(x_max, x + max_radius), min(y_max, y + max_radius)),
            (max(x_min, x - max_radius), min(y_max, y + max_radius))
        ]
    
    return zone_points


def _sort_points_by_angle(
    points: List[Tuple[float, float]],
    center: Tuple[float, float]
) -> List[Tuple[float, float]]:
    """
    Сортирует точки по углу относительно центра.
    
    Args:
        points: Список точек
        center: Центр
    
    Returns:
        Отсортированный список точек
    """
    def angle_from_center(point):
        dx = point[0] - center[0]
        dy = point[1] - center[1]
        return math.atan2(dy, dx)
    
    return sorted(points, key=angle_from_center)


def _convex_hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Строит выпуклую оболочку для набора точек (алгоритм Грэхема).
    
    Args:
        points: Список точек
    
    Returns:
        Список вершин выпуклой оболочки
    """
    if len(points) < 3:
        return points
    
    # Находим самую нижнюю точку (и самую левую при равенстве y)
    start = min(points, key=lambda p: (p[1], p[0]))
    
    # Сортируем точки по полярному углу относительно start
    def polar_angle(point):
        if point == start:
            return -1
        dx = point[0] - start[0]
        dy = point[1] - start[1]
        return math.atan2(dy, dx)
    
    sorted_points = sorted([p for p in points if p != start], key=polar_angle)
    sorted_points.insert(0, start)
    
    # Строим оболочку
    hull = [sorted_points[0], sorted_points[1]]
    
    for i in range(2, len(sorted_points)):
        while len(hull) > 1:
            # Векторное произведение для определения направления поворота
            # cross > 0 означает поворот против часовой стрелки (выпуклость сохраняется)
            p1, p2, p3 = hull[-2], hull[-1], sorted_points[i]
            cross = (p2[0] - p1[0]) * (p3[1] - p1[1]) - (p2[1] - p1[1]) * (p3[0] - p1[0])
            if cross > 0:
                break
            hull.pop()
        hull.append(sorted_points[i])
    
    return hull

