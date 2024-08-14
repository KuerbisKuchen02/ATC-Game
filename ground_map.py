import heapq

import pygame


class Waypoint:

    def __init__(self, name: str, x: int, y: int, connected_points=None):
        self.name = name
        self.x = x
        self.y = y
        self.connected_points = connected_points if connected_points is not None else []

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 0, 255), (self.x - 5, self.y - 5, 10, 10), 10, 5)


class GroundMap:
    def __init__(self):
        self._points = {}

    def add_point(self, point: Waypoint):
        self._points[point.name] = point

    def draw(self, surface):
        for _, point in self._points.items():
            point.draw(surface)

    def manhattan_distance(self, point1_name: str, point2_name: str) -> int:
        point1 = self._points[point1_name]
        point2 = self._points[point2_name]
        return abs(point1.x - point2.x) + abs(point1.y - point2.y)

    def dijkstra(self, start_point: str):
        heap = []
        distances = {start_point: 0}
        previous_points = {start_point: None}

        heapq.heappush(heap, (0, start_point))

        while len(heap) > 0:
            _, point = heapq.heappop(heap)
            for connected_point in self._points[point].connected_points:
                alternative = distances[point] + self.manhattan_distance(point, connected_point)
                try:
                    distances[connected_point]
                except KeyError:
                    distances[connected_point] = 9999
                if alternative < distances[connected_point]:
                    distances[connected_point] = alternative
                    previous_points[connected_point] = point
                    heapq.heappush(heap, (alternative, connected_point))
        return distances, previous_points

    def get_shortest_path(self, start_point: str, end_point: str):
        _, previous_points = self.dijkstra(start_point)
        path = []
        point = end_point
        while point != start_point:
            path.append(point)
            point = previous_points[point]
        path.reverse()
        return path



