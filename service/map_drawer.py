import base64
import io
import math

from PIL import Image, ImageDraw, ImageFont

from schemas import MapRequest, Point, UserPosition, Route

MAP_WIDTH = 450
MAP_HEIGHT = 450
TILE_SIZE = 256

SEGMENT_COLORS = [
    "#F44336",
    "#2196F3",
    "#4CAF50",
    "#FFC107",
    "#9C27B0",
    "#FF5722",
    "#00BCD4",
    "#E91E63",
    "#8BC34A",
    "#03A9F4",
]


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


def _geo_to_pixels(
    point: Point, center: Point, zoom: int,
    img_width: int = MAP_WIDTH, img_height: int = MAP_HEIGHT,
) -> tuple[int, int]:
    center_gx = _lon_to_global_px(center.lon, zoom)
    center_gy = _lat_to_global_px(center.lat, zoom)

    point_gx = _lon_to_global_px(point.lon, zoom)
    point_gy = _lat_to_global_px(point.lat, zoom)

    dx = point_gx - center_gx
    dy = point_gy - center_gy

    px = int(img_width / 2 + dx)
    py = int(img_height / 2 + dy)

    return px, py


def _get_font(size: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()


def _draw_route(
    draw: ImageDraw.Draw, route: Route, center: Point, zoom: int,
) -> None:
    font = _get_font(14)
    font_small = _get_font(11)

    for seg_idx, segment in enumerate(route.segments):
        if len(segment) < 2:
            continue

        color = SEGMENT_COLORS[seg_idx % len(SEGMENT_COLORS)]
        seg_pixels = [_geo_to_pixels(p, center, zoom) for p in segment]

        for i in range(len(seg_pixels) - 1):
            draw.line([seg_pixels[i], seg_pixels[i + 1]], fill=color, width=4)

        mid_idx = len(seg_pixels) // 2
        mx, my = seg_pixels[mid_idx]

        label = str(seg_idx + 1)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.rectangle(
            [mx - tw // 2 - 3, my - th // 2 - 3, mx + tw // 2 + 3, my + th // 2 + 3],
            fill="white",
            outline=color,
            width=2,
        )
        draw.text((mx - tw // 2, my - th // 2), label, fill=color, font=font)

    if route.segments and len(route.segments[0]) > 0:
        start_point = route.segments[0][0]
        sx, sy = _geo_to_pixels(start_point, center, zoom)
        r = 10
        draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill="#4CAF50", outline="white", width=2)
        bbox_a = draw.textbbox((0, 0), "A", font=font_small)
        aw = bbox_a[2] - bbox_a[0]
        ah = bbox_a[3] - bbox_a[1]
        draw.text((sx - aw // 2, sy - ah // 2), "A", fill="white", font=font_small)

    if route.segments and len(route.segments[-1]) > 0:
        end_point = route.segments[-1][-1]
        ex, ey = _geo_to_pixels(end_point, center, zoom)
        r = 10
        draw.ellipse([ex - r, ey - r, ex + r, ey + r], fill="#F44336", outline="white", width=2)
        bbox_b = draw.textbbox((0, 0), "B", font=font_small)
        bw = bbox_b[2] - bbox_b[0]
        bh = bbox_b[3] - bbox_b[1]
        draw.text((ex - bw // 2, ey - bh // 2), "B", fill="white", font=font_small)


def _draw_user_marker(
    draw: ImageDraw.Draw,
    position: UserPosition,
    center: Point,
    zoom: int,
) -> None:
    px, py = _geo_to_pixels(position.point, center, zoom)
    font = _get_font(16)

    marker_r = 14
    draw.ellipse(
        [px - marker_r, py - marker_r, px + marker_r, py + marker_r],
        fill="#2196F3",
        outline="white",
        width=2,
    )

    bbox_ya = draw.textbbox((0, 0), "R", font=font)
    tw = bbox_ya[2] - bbox_ya[0]
    th = bbox_ya[3] - bbox_ya[1]
    draw.text((px - tw // 2, py - th // 2), "R", fill="white", font=font)

    angle_deg = position.compass_direction
    angle_rad = math.radians(angle_deg)

    arrow_length = 28
    end_x = px + arrow_length * math.sin(angle_rad)
    end_y = py - arrow_length * math.cos(angle_rad)

    draw.line([(px, py), (int(end_x), int(end_y))], fill="#FF0000", width=3)

    head_length = 10
    head_angle = math.radians(25)

    left_x = end_x - head_length * math.sin(angle_rad - head_angle)
    left_y = end_y + head_length * math.cos(angle_rad - head_angle)

    right_x = end_x - head_length * math.sin(angle_rad + head_angle)
    right_y = end_y + head_length * math.cos(angle_rad + head_angle)

    draw.polygon(
        [(int(end_x), int(end_y)), (int(left_x), int(left_y)), (int(right_x), int(right_y))],
        fill="#FF0000",
    )


def draw_elements_on_map(
    image_bytes: bytes,
    request: MapRequest,
    center: Point,
    zoom: int,
) -> str:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    if request.route is not None and len(request.route.segments) > 0:
        _draw_route(draw, request.route, center, zoom)

    _draw_user_marker(draw, request.position, center, zoom)

    result = Image.alpha_composite(image, overlay).convert("RGB")

    buffer = io.BytesIO()
    result.save(buffer, format="PNG")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode("utf-8")