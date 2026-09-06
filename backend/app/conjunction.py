"""
Given propagated trajectories for every tracked object, find every pair
whose closest approach over the forecast window comes within the safety
threshold.

Approach: for each pair of objects, compute the Euclidean distance
between their positions at every shared timestep, find the minimum
(the closest approach), and check it against the threshold. This is an
O(n^2 * n_steps) brute-force scan - perfectly fine for the "stations"
group or a few dozen objects in a hackathon demo. For a full catalog of
thousands of objects you'd want a coarse spatial filter first (e.g. only
compare objects with similar orbital altitude bands), but that's an
optimization for a v2, not a correctness requirement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Dict, List

import numpy as np

from . import config
from .propagator import PropagatedObject


@dataclass
class RawConjunction:
    """Closest-approach result for a single object pair, pre-scoring."""

    norad_id_a: str
    norad_id_b: str
    name_a: str
    name_b: str
    miss_distance_km: float
    relative_velocity_kmps: float
    t_offset_seconds: float  # seconds from propagation start


def _closest_approach(a: PropagatedObject, b: PropagatedObject) -> RawConjunction | None:
    """Find the closest approach between two propagated objects."""
    # Both objects were propagated on the same time grid, so their arrays
    # line up index-for-index.
    if len(a.t_offsets) != len(b.t_offsets):
        return None

    delta_pos = a.positions_km - b.positions_km  # (n, 3)
    distances = np.linalg.norm(delta_pos, axis=1)  # (n,)

    if np.all(np.isnan(distances)):
        return None

    min_idx = int(np.nanargmin(distances))
    miss_distance = float(distances[min_idx])

    delta_vel = a.velocities_kmps[min_idx] - b.velocities_kmps[min_idx]
    relative_velocity = float(np.linalg.norm(delta_vel))

    return RawConjunction(
        norad_id_a=a.record.norad_id,
        norad_id_b=b.record.norad_id,
        name_a=a.record.name,
        name_b=b.record.name,
        miss_distance_km=miss_distance,
        relative_velocity_kmps=relative_velocity,
        t_offset_seconds=float(a.t_offsets[min_idx]),
    )


MIN_MEANINGFUL_DISTANCE_KM = config.MIN_MEANINGFUL_DISTANCE_KM  # below this, treat as "same physical object" not a real conjunction


def find_conjunctions(
    propagated: Dict[str, PropagatedObject],
    threshold_km: float,
) -> List[RawConjunction]:
    """
    Screen every object pair and return the ones whose closest approach
    is within `threshold_km` and at or above `MIN_MEANINGFUL_DISTANCE_KM`,
    sorted by miss distance (closest first).
    """
    
    flagged: List[RawConjunction] = []

    for obj_a, obj_b in combinations(propagated.values(), 2):
        # Skip self-pairs from duplicate NORAD IDs, if any slipped through.
        if obj_a.record.norad_id == obj_b.record.norad_id:
            continue

        result = _closest_approach(obj_a, obj_b)
        if (
            result is not None
            and MIN_MEANINGFUL_DISTANCE_KM <= result.miss_distance_km <= threshold_km
        ):
            flagged.append(result)

    flagged.sort(key=lambda c: c.miss_distance_km)
    return flagged
