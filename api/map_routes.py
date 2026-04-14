from fastapi import APIRouter, HTTPException
import requests

from schemas import MapRequest
from service.yandex_static_api import calculate_map_center_and_zoom, fetch_yandex_map
from service.map_drawer import draw_elements_on_map

router = APIRouter()


@router.post("/map")
async def generate_map(request: MapRequest) -> dict[str, str]:
    try:
        center, zoom = calculate_map_center_and_zoom(request)
        image_bytes = fetch_yandex_map(center, zoom)
        image_base64 = draw_elements_on_map(image_bytes, request, center, zoom)
        return {"image_base64": image_base64}
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=502, detail="Bad Gateway: Yandex API is unavailable")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")