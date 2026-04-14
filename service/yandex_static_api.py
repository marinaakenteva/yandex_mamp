import os
import math

import requests

from schemas import MapRequest, Point

YANDEX_STATIC_API_KEY = os.environ.get("YANDEX_STATIC_API_KEY", "")

MAP_WIDTH = 450
MAP_HEIGHT = 450
TILE_SIZE = 256


def _lon_to_global_px(lon: float, zoom: int) -> float:
    return ((lon + 180.0) / 360.0) * TILE_SIZE * (2 ** zoom)


def _lat_to_global_px(lat: float, zoom: int) -> float:
    lat_rad = math.radians(lat)
    return (
        (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi)
        / 2.0
        * TILE_SIZE
        * (2 ** zoom)
    )


def calculate_map_center_and_zoom(request: MapRequest) -> tuple[Point, int]:
    if request.route is None or len(request.route.segments) == 0:
        return request.position.point, request.zoom

    all_points: list[Point] = []
    for segment in request.route.segments:
        all_points.extend(segment)

    if len(all_points) == 0:
        return request.position.point, request.zoom

    min_lon = min(p.lon for p in all_points)
    max_lon = max(p.lon for p in all_points)
    min_lat = min(p.lat for p in all_points)
    max_lat = max(p.lat for p in all_points)

    center_lon = (min_lon + max_lon) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    center = Point(lon=center_lon, lat=center_lat)

    padding = 40
    usable_width = MAP_WIDTH - 2 * padding
    usable_height = MAP_HEIGHT - 2 * padding

    if usable_width <= 0 or usable_height <= 0:
        return center, 15

    delta_lon_px_z0 = abs(
        _lon_to_global_px(max_lon, 0) - _lon_to_global_px(min_lon, 0)
    )
    delta_lat_px_z0 = abs(
        _lat_to_global_px(min_lat, 0) - _lat_to_global_px(max_lat, 0)
    )

    if delta_lon_px_z0 > 0:
        z_lon = math.log2(usable_width / delta_lon_px_z0)
    else:
        z_lon = 21

    if delta_lat_px_z0 > 0:
        z_lat = math.log2(usable_height / delta_lat_px_z0)
    else:
        z_lat = 21

    zoom = int(math.floor(min(z_lon, z_lat)))
    zoom = max(0, min(zoom, 21))

    return center, zoom


def fetch_yandex_map(
    center: Point, zoom: int, width: int = MAP_WIDTH, height: int = MAP_HEIGHT
) -> bytes:
    params = {
        "ll": f"{center.lon},{center.lat}",
        "z": zoom,
        "l": "map",
        "size": f"{width},{height}",
        "apikey": YANDEX_STATIC_API_KEY,
    }

    response = requests.get(
        "https://static-maps.yandex.ru/v1",
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    return response.content