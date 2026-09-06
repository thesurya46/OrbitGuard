"""
Turns a raw geometric close-approach (distance + relative velocity) into
a single 0-100 risk score and an urgency label, so the dashboard can sort
and color-code events without the viewer needing to interpret raw
kilometers and km/s themselves.

Scoring model (intentionally simple and explainable for a hackathon
judge to follow in one breath):

    risk = 70% * how far into the "danger zone" the miss distance is
         + 30% * how fast the objects are closing, relative to a
                 reference max closing speed

Both components are clamped to [0, 1] before weighting, so the final
score always lands in [0, 100].
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from . import config
from .conjunction import RawConjunction
from .models import ConjunctionEvent


def _distance_component(miss_distance_km: float, threshold_km: float) -> float:
    if threshold_km <= 0:
        return 0.0
    proximity = 1.0 - (miss_distance_km / threshold_km)
    return max(0.0, min(1.0, proximity))


def _velocity_component(relative_velocity_kmps: float) -> float:
    ratio = relative_velocity_kmps / config.RISK_VELOCITY_REFERENCE_KMPS
    return max(0.0, min(1.0, ratio))


def _urgency_label(hours_to_ca: float) -> str:
    if hours_to_ca < 6:
        return "Critical"
    if hours_to_ca < 24:
        return "High"
    if hours_to_ca < 48:
        return "Moderate"
    return "Low"


def score_conjunction(
    raw: RawConjunction,
    threshold_km: float,
    propagation_start: datetime,
) -> ConjunctionEvent:
    distance_score = _distance_component(raw.miss_distance_km, threshold_km)
    velocity_score = _velocity_component(raw.relative_velocity_kmps)

    risk = (
        config.RISK_DISTANCE_WEIGHT * distance_score
        + config.RISK_VELOCITY_WEIGHT * velocity_score
    ) * 100

    hours_to_ca = raw.t_offset_seconds / 3600.0
    closest_approach_time = propagation_start + timedelta(seconds=raw.t_offset_seconds)

    return ConjunctionEvent(
        object_a=raw.name_a,
        object_b=raw.name_b,
        norad_id_a=raw.norad_id_a,
        norad_id_b=raw.norad_id_b,
        miss_distance_km=round(raw.miss_distance_km, 3),
        relative_velocity_kmps=round(raw.relative_velocity_kmps, 3),
        time_to_closest_approach_hours=round(hours_to_ca, 2),
        closest_approach_iso=closest_approach_time.isoformat(),
        risk_score=round(risk, 1),
        urgency=_urgency_label(hours_to_ca),
    )


def score_all(
    raw_conjunctions: List[RawConjunction],
    threshold_km: float,
    propagation_start: datetime | None = None,
) -> List[ConjunctionEvent]:
    """Score every raw conjunction and return them ranked highest-risk first."""
    propagation_start = propagation_start or datetime.now(timezone.utc)
    events = [
        score_conjunction(raw, threshold_km, propagation_start)
        for raw in raw_conjunctions
    ]
    events.sort(key=lambda e: e.risk_score, reverse=True)
    return events
