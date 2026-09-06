"""Unit tests for the risk scoring formula and urgency labeling."""

from datetime import datetime, timezone

import pytest

from app.conjunction import RawConjunction
from app.risk_scoring import score_all, score_conjunction


def make_raw(miss_distance_km, relative_velocity_kmps, t_offset_seconds):
    return RawConjunction(
        norad_id_a="10001",
        norad_id_b="10002",
        name_a="Sat-A",
        name_b="Sat-B",
        miss_distance_km=miss_distance_km,
        relative_velocity_kmps=relative_velocity_kmps,
        t_offset_seconds=t_offset_seconds,
    )


def test_closer_and_faster_pair_scores_higher():
    start = datetime.now(timezone.utc)

    close_fast = score_conjunction(
        make_raw(miss_distance_km=1, relative_velocity_kmps=14, t_offset_seconds=3600),
        threshold_km=25,
        propagation_start=start,
    )
    far_slow = score_conjunction(
        make_raw(miss_distance_km=24, relative_velocity_kmps=1, t_offset_seconds=3600),
        threshold_km=25,
        propagation_start=start,
    )

    assert close_fast.risk_score > far_slow.risk_score


def test_risk_score_is_bounded_0_to_100():
    start = datetime.now(timezone.utc)
    event = score_conjunction(
        make_raw(miss_distance_km=0, relative_velocity_kmps=100, t_offset_seconds=0),
        threshold_km=25,
        propagation_start=start,
    )
    assert 0 <= event.risk_score <= 100


def test_urgency_labels_follow_time_to_closest_approach():
    start = datetime.now(timezone.utc)

    critical = score_conjunction(
        make_raw(1, 5, t_offset_seconds=3 * 3600), 25, start
    )
    high = score_conjunction(
        make_raw(1, 5, t_offset_seconds=12 * 3600), 25, start
    )
    moderate = score_conjunction(
        make_raw(1, 5, t_offset_seconds=30 * 3600), 25, start
    )
    low = score_conjunction(
        make_raw(1, 5, t_offset_seconds=60 * 3600), 25, start
    )

    assert critical.urgency == "Critical"
    assert high.urgency == "High"
    assert moderate.urgency == "Moderate"
    assert low.urgency == "Low"


def test_score_all_ranks_highest_risk_first():
    start = datetime.now(timezone.utc)
    raws = [
        make_raw(miss_distance_km=20, relative_velocity_kmps=1, t_offset_seconds=3600),
        make_raw(miss_distance_km=1, relative_velocity_kmps=14, t_offset_seconds=3600),
        make_raw(miss_distance_km=10, relative_velocity_kmps=5, t_offset_seconds=3600),
    ]
    events = score_all(raws, threshold_km=25, propagation_start=start)

    scores = [e.risk_score for e in events]
    assert scores == sorted(scores, reverse=True)
