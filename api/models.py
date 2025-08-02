from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

class BoundingBox(BaseModel):
    x: int
    y: int
    w: int
    h: int

class Point(BaseModel):
    x: float
    y: float

class DetectionResponse(BaseModel):
    id: int
    timestamp: datetime
    object_id: str
    camera_id: Optional[str]
    area_id: Optional[int]
    bbox: BoundingBox
    center_point: Point
    confidence: float
    entered: bool
    exited: bool

class CountStats(BaseModel):
    area_id: int
    timestamp: datetime
    count_in: int
    count_out: int
    total_in: int
    total_out: int

class LiveStats(BaseModel):
    area_id: int
    current_count_in: int
    current_count_out: int
    last_detection: Optional[datetime]
    active_objects: int

class PolygonConfig(BaseModel):
    name: str
    coordinates: List[List[int]]

class StatsFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    area_id: Optional[int] = None
    page: int = 1
    limit: int = 100

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
