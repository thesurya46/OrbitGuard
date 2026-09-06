"""Pydantic schemas shared between the API layer and the pipeline modules."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from . import config


class TLERecord(BaseModel):
    """A single Two-Line Element set."""

    name: str
    norad_id: str
    line1: str
    line2: str


class OrbitSample(BaseModel):
    """One propagated (time, position, velocity) sample for a single object."""

    t_offset_seconds: float
    position_km: List[float]  # [x, y, z] in the TEME frame
    velocity_kmps: List[float]  # [vx, vy, vz] in the TEME frame


class ConjunctionEvent(BaseModel):
    """A single flagged close-approach event between two tracked objects."""

    object_a: str
    object_b: str
    norad_id_a: str
    norad_id_b: str
    miss_distance_km: float
    relative_velocity_kmps: float
    time_to_closest_approach_hours: float
    closest_approach_iso: str
    risk_score: float = Field(..., ge=0, le=100)
    urgency: str  # "Critical" | "High" | "Moderate" | "Low"


class ConjunctionRequest(BaseModel):
    group: str = config.DEFAULT_GROUP
    threshold_km: float = config.DEFAULT_THRESHOLD_KM
    window_hours: float = config.DEFAULT_WINDOW_HOURS
    step_seconds: float = config.DEFAULT_STEP_SECONDS
    use_sample_data: bool = False
    force_refresh: bool = False


class ConjunctionResponse(BaseModel):
    generated_at_iso: str
    group: str
    objects_tracked: int
    window_hours: float
    threshold_km: float
    events: List[ConjunctionEvent]


class HealthResponse(BaseModel):
    status: str
    version: str
    sample_data_available: bool
