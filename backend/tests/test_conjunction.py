"""
Unit tests for the conjunction screening math.

These build PropagatedObject fixtures directly with synthetic numpy
trajectories (no real SGP4 propagation needed) so the geometry logic can
be verified in isolation from network/TLE concerns.
"""

import numpy as np
import pytest

from app.conjunction import find_conjunctions
from app.models import TLERecord
from app.propagator import PropagatedObject


def make_object(name, norad_id, positions, velocities=None, t_offsets=None):
    positions = np.array(positions, dtype=np.float64)
    n = len(positions)
    if velocities is None:
        velocities = np.zeros((n, 3))
    if t_offsets is None:
        t_offsets = np.arange(n, dtype=np.float64) * 60.0

    record = TLERecord(name=name, norad_id=norad_id, line1="1 dummy", line2="2 dummy")
    return PropagatedObject(
        record=record,
        t_offsets=t_offsets,
        positions_km=positions,
        velocities_kmps=np.array(velocities, dtype=np.float64),
    )


def test_flags_pair_within_threshold():
    # Two objects that start far apart and converge to 5 km at t=60s.
    obj_a = make_object(
        "Sat-A",
        "10001",
        positions=[[0, 0, 7000], [0, 0, 7000], [0, 0, 7000]],
    )
    obj_b = make_object(
        "Sat-B",
        "10002",
        positions=[[100, 0, 7000], [5, 0, 7000], [200, 0, 7000]],
    )

    propagated = {"10001": obj_a, "10002": obj_b}
    events = find_conjunctions(propagated, threshold_km=25)

    assert len(events) == 1
    event = events[0]
    assert {event.norad_id_a, event.norad_id_b} == {"10001", "10002"}
    assert event.miss_distance_km == pytest.approx(5.0, abs=1e-6)
    # Closest approach happens at the second timestep (index 1 -> t=60s).
    assert event.t_offset_seconds == pytest.approx(60.0)


def test_ignores_pair_beyond_threshold():
    obj_a = make_object("Sat-A", "20001", positions=[[0, 0, 7000]])
    obj_b = make_object("Sat-B", "20002", positions=[[500, 0, 7000]])

    propagated = {"20001": obj_a, "20002": obj_b}
    events = find_conjunctions(propagated, threshold_km=25)

    assert events == []


def test_relative_velocity_is_computed_at_closest_approach():
    obj_a = make_object(
        "Sat-A",
        "30001",
        positions=[[0, 0, 7000], [0, 0, 7000]],
        velocities=[[7.5, 0, 0], [7.5, 0, 0]],
    )
    obj_b = make_object(
        "Sat-B",
        "30002",
        positions=[[10, 0, 7000], [10, 0, 7000]],
        velocities=[[-7.5, 0, 0], [0, 0, 0]],
    )

    propagated = {"30001": obj_a, "30002": obj_b}
    events = find_conjunctions(propagated, threshold_km=25)

    assert len(events) == 1
    # Both timesteps are equidistant (10 km); np.nanargmin picks the first,
    # so relative velocity should reflect index 0: |7.5 - (-7.5)| = 15.0
    assert events[0].relative_velocity_kmps == pytest.approx(15.0)


def test_skips_self_pairs_and_handles_multiple_objects():
    objects = {
        "40001": make_object("A", "40001", positions=[[0, 0, 7000]]),
        "40002": make_object("B", "40002", positions=[[3, 0, 7000]]),
        "40003": make_object("C", "40003", positions=[[1000, 0, 7000]]),
    }
    events = find_conjunctions(objects, threshold_km=25)

    # Only the A-B pair should be within threshold; C is far from both.
    assert len(events) == 1
    assert {events[0].norad_id_a, events[0].norad_id_b} == {"40001", "40002"}


def test_ignores_near_zero_miss_distance():
    # Two objects on the same rigid structure or docked (distance < 0.5 km)
    obj_a = make_object("ISS Zarya", "25544", positions=[[0, 0, 7000]])
    obj_b = make_object("ISS Nauka", "49044", positions=[[0.1, 0, 7000]])  # 100 meters apart

    propagated = {"25544": obj_a, "49044": obj_b}
    events = find_conjunctions(propagated, threshold_km=25)

    # Should be filtered out as non-event (docked/same physical object)
    assert events == []

