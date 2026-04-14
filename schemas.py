from pydantic import BaseModel, Field


class Point(BaseModel):
    lon: float
    lat: float


class UserPosition(BaseModel):
    point: Point
    compass_direction: float


class Route(BaseModel):
    segments: list[list[Point]]


class MapRequest(BaseModel):
    position: UserPosition
    zoom: int = Field(..., ge=0, le=21)
    route: Route | None = None