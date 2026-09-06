"""
Propagates every tracked object forward in time using the SGP4/SDP4
model, so we know where each object will be at every timestep in the
forecast window.

We deliberately keep this module dumb and numeric: it takes TLEs in,
returns arrays of (time, position, velocity) out. No screening or
scoring logic lives here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Dict, List, NamedTuple

import numpy as np

from .models import TLERecord


class PropagatedObject(NamedTuple):
    record: TLERecord
    # Shape (n_steps,) - seconds since propagation start.
    t_offsets: np.ndarray
    # Shape (n_steps, 3) - TEME frame, kilometers.
    positions_km: np.ndarray
    # Shape (n_steps, 3) - TEME frame, km/s.
    velocities_kmps: np.ndarray


def _time_grid(start: datetime, window_hours: float, step_seconds: float) -> List[datetime]:
    n_steps = int((window_hours * 3600) // step_seconds) + 1
    return [start + timedelta(seconds=i * step_seconds) for i in range(n_steps)]


def propagate_object(
    record: TLERecord,
    start: datetime,
    window_hours: float,
    step_seconds: float,
) -> PropagatedObject:
    """Propagate a single TLE across the forecast window."""
    # Imported lazily so modules that only need the PropagatedObject
    # container (e.g. conjunction screening tests) don't require the
    # sgp4 package to be installed just to import this module.
    from sgp4.api import Satrec, jday

    satellite = Satrec.twoline2rv(record.line1, record.line2)

    times = _time_grid(start, window_hours, step_seconds)
    n = len(times)

    positions = np.empty((n, 3), dtype=np.float64)
    velocities = np.empty((n, 3), dtype=np.float64)
    t_offsets = np.empty((n,), dtype=np.float64)

    for i, t in enumerate(times):
        jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
        error_code, position, velocity = satellite.sgp4(jd, fr)
        if error_code != 0:
            # SGP4 failed for this timestep (e.g. decayed orbit) - mark as NaN
            # so downstream conjunction screening can skip it cleanly.
            positions[i] = np.nan
            velocities[i] = np.nan
        else:
            positions[i] = position
            velocities[i] = velocity
        t_offsets[i] = (t - start).total_seconds()

    return PropagatedObject(
        record=record,
        t_offsets=t_offsets,
        positions_km=positions,
        velocities_kmps=velocities,
    )


def propagate_all(
    records: List[TLERecord],
    start: datetime | None = None,
    window_hours: float = 72.0,
    step_seconds: float = 60.0,
) -> Dict[str, PropagatedObject]:
    """
    Propagate every record in `records` across the same time grid.

    Returns a dict keyed by NORAD ID so the conjunction screener can pair
    objects up cheaply.
    """
    start = start or datetime.now(timezone.utc)
    result: Dict[str, PropagatedObject] = {}
    for record in records:
        try:
            result[record.norad_id] = propagate_object(
                record, start, window_hours, step_seconds
            )
        except Exception as e:
            # A single malformed TLE shouldn't take down the whole run.
            continue
    return result
