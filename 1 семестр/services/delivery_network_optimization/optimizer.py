"""
Основной модуль для оптимизации сети пунктов выдачи заказов.
Реализует алгоритмы размещения новых ПВЗ и перераспределения зон доставки.
"""

import math
from typing import List, Dict, Tuple
from geometry import (
    euclidean_distance,
    get_all_districts_bounds,
    point_in_any_district,
    polygon_area
)
from interpolation import create_density_grid, get_density_at_point
from voronoi import voronoi_zone_for_point
from metrics import (
    calculate_avg_delivery_distance,
    calculate_coverage_efficiency,
    calculate_load_imbalance
)


class DeliveryNetworkOptimizer:
    """
    Класс для оптимизации сети пунктов выдачи заказов.
    """
    
    def __init__(self, input_data: Dict):
        """
        Инициализирует оптимизатор с входными данными.
        
        Args:
            input_data: Словарь с входными данными задачи
        """
        self.districts = input_data.get("districts", [])
        self.historical_orders = input_data.get("historical_orders", [])
        self.existing_delivery_points = input_data.get("existing_pickup_points", [])
        self.task_parameters = input_data.get("task_parameters", {})
        
        self.new_dp_count = self.task_parameters.get("new_pp_count", 0)
        self.max_delivery_radius = self.task_parameters.get("max_delivery_radius", 100.0)
        self.interpolation_resolution = self.task_parameters.get("interpolation_resolution", 20.0)
        
        # Вычисляем границы области
        self.bounds = get_all_districts_bounds(self.districts)
        
        # Карта плотности (будет вычислена при оптимизации)
        self.density_map = None
    
    def optimize(self) -> Dict:
        """
        Выполняет полную оптимизацию сети ПВЗ.
        
        Returns:
            Словарь с результатами оптимизации
        """
        # Шаг 1: Создаем карту плотности спроса
        self.density_map = create_density_grid(
            self.bounds,
            self.interpolation_resolution,
            self.historical_orders,
            self.districts
        )
        
        # Шаг 2: Размещаем новые ПВЗ
        new_delivery_points = self._place_new_delivery_points()
        
        # Шаг 3: Строим зоны доставки для всех ПВЗ
        all_delivery_points = self.existing_delivery_points + new_delivery_points
        delivery_zones = self._build_delivery_zones(all_delivery_points)
        
        # Шаг 4: Оцениваем количество заказов для каждой зоны
        delivery_zones = self._estimate_orders_per_zone(delivery_zones)
        
        # Шаг 5: Вычисляем метрики
        metrics = self._calculate_metrics(delivery_zones, all_delivery_points)
        
        return {
            "demand_density_map": self.density_map,
            "new_delivery_points": new_delivery_points,
            "delivery_zones": delivery_zones,
            "metrics": metrics
        }
    
    def _place_new_delivery_points(self) -> List[Dict]:
        """
        Размещает новые ПВЗ на основе карты плотности спроса.
        Использует жадный алгоритм: выбирает точки с максимальной плотностью,
        которые находятся на достаточном расстоянии от существующих ПВЗ.
        
        Returns:
            Список новых ПВЗ с координатами
        """
        if self.new_dp_count == 0:
            return []
        
        new_points = []
        # Минимальное расстояние между ПВЗ (60% от максимального радиуса доставки)
        min_distance_between_points = self.max_delivery_radius * 0.6
        
        # Создаем сетку кандидатов для размещения
        x_min, y_min, x_max, y_max = self.bounds
        resolution = self.interpolation_resolution
        
        candidates = []
        
        # Генерируем кандидатов внутри районов
        for x in range(int(x_min), int(x_max) + 1, int(resolution)):
            for y in range(int(y_min), int(y_max) + 1, int(resolution)):
                point = (float(x), float(y))
                
                if not point_in_any_district(point, self.districts):
                    continue
                
                # Получаем плотность в точке
                density = get_density_at_point(point, self.density_map)
                
                if density > 0:
                    candidates.append((point, density))
        
        # Сортируем кандидатов по убыванию плотности
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Жадный алгоритм: выбираем точки с максимальной плотностью,
        # которые находятся на достаточном расстоянии от уже выбранных
        all_existing_locations = [tuple(dp["location"]) for dp in self.existing_delivery_points]
        
        for candidate_point, density in candidates:
            if len(new_points) >= self.new_dp_count:
                break
            
            # Проверяем расстояние до существующих ПВЗ
            too_close_to_existing = False
            for existing_loc in all_existing_locations:
                if euclidean_distance(candidate_point, existing_loc) < min_distance_between_points:
                    too_close_to_existing = True
                    break
            
            if too_close_to_existing:
                continue
            
            # Проверяем расстояние до уже выбранных новых ПВЗ
            too_close_to_new = False
            for new_point in new_points:
                new_loc = tuple(new_point["location"])
                if euclidean_distance(candidate_point, new_loc) < min_distance_between_points:
                    too_close_to_new = True
                    break
            
            if too_close_to_new:
                continue
            
            # Добавляем новую точку
            new_points.append({
                "dp_id": f"N{len(new_points) + 1}",
                "location": list(candidate_point)
            })
        
        return new_points
    
    def _build_delivery_zones(self, all_delivery_points: List[Dict]) -> List[Dict]:
        """
        Строит зоны доставки для всех ПВЗ на основе диаграммы Вороного.
        
        Args:
            all_delivery_points: Список всех ПВЗ (существующих и новых)
        
        Returns:
            Список зон доставки
        """
        all_centers = [tuple(dp["location"]) for dp in all_delivery_points]
        delivery_zones = []
        
        for dp in all_delivery_points:
            center = tuple(dp["location"])
            dp_id = dp["dp_id"]
            
            # Строим зону Вороного для этого ПВЗ
            polygon = voronoi_zone_for_point(
                center,
                all_centers,
                self.bounds,
                self.max_delivery_radius,
                self.districts,
                resolution=self.interpolation_resolution
            )
            
            delivery_zones.append({
                "dp_id": dp_id,
                "polygon": [list(vertex) for vertex in polygon]
            })
        
        return delivery_zones
    
    def _estimate_orders_per_zone(self, delivery_zones: List[Dict]) -> List[Dict]:
        """
        Оценивает количество заказов для каждой зоны доставки на основе
        исторических данных и карты плотности.
        
        Args:
            delivery_zones: Список зон доставки
        
        Returns:
            Список зон с оценкой количества заказов
        """
        for zone in delivery_zones:
            polygon = [tuple(vertex) for vertex in zone["polygon"]]
            zone_area = polygon_area(polygon)
            
            if zone_area == 0:
                zone["estimated_orders"] = 0
                continue
            
            # Подсчитываем исторические заказы в зоне
            orders_in_zone = 0
            total_weight = 0.0
            
            for order in self.historical_orders:
                delivery_point = tuple(order["delivery_point"])
                
                # Проверяем, попадает ли заказ в зону
                from geometry import point_in_polygon
                if point_in_polygon(delivery_point, polygon):
                    weight = order.get("weight", 1.0)
                    orders_in_zone += 1
                    total_weight += weight
            
            # Оцениваем будущее количество заказов на основе исторических данных
            # и площади зоны (пропорционально)
            if len(self.historical_orders) > 0:
                # Средняя плотность заказов на единицу площади
                total_historical_area = sum(
                    polygon_area([tuple(v) for v in d["polygon"]])
                    for d in self.districts
                )
                
                if total_historical_area > 0:
                    avg_orders_per_area = len(self.historical_orders) / total_historical_area
                    estimated_orders = int(avg_orders_per_area * zone_area)
                else:
                    estimated_orders = orders_in_zone
            else:
                estimated_orders = 0
            
            zone["estimated_orders"] = estimated_orders
        
        return delivery_zones
    
    def _calculate_metrics(
        self,
        delivery_zones: List[Dict],
        all_delivery_points: List[Dict]
    ) -> Dict:
        """
        Вычисляет метрики эффективности предложенного решения.
        
        Args:
            delivery_zones: Список зон доставки
            all_delivery_points: Список всех ПВЗ
        
        Returns:
            Словарь с метриками
        """
        avg_distance = calculate_avg_delivery_distance(delivery_zones, all_delivery_points)
        coverage = calculate_coverage_efficiency(self.historical_orders, delivery_zones)
        imbalance = calculate_load_imbalance(delivery_zones)
        
        return {
            "avg_delivery_distance": round(avg_distance, 2),
            "coverage_efficiency": round(coverage, 2),
            "load_imbalance": round(imbalance, 2)
        }

