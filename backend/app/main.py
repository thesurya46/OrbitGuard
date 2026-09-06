"""
OrbitGuard API.

Endpoints
---------
GET  /api/health                -> service + sample-data status
GET  /api/tles?group=stations   -> raw TLE records currently in use
POST /api/conjunctions/run      -> run the full pipeline, return ranked risk events

Run locally with:
    uvicorn app.main:app --reload
or simply:
    python run.py
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .conjunction import find_conjunctions
from .models import (
    ConjunctionRequest,
    ConjunctionResponse,
    HealthResponse,
    TLERecord,
)
from .propagator import propagate_all
from .risk_scoring import score_all
from .tle_fetcher import TLEFetchError, get_tles

app = FastAPI(
    title="OrbitGuard API",
    description="Satellite conjunction & collision risk screening pipeline.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=app.version,
        sample_data_available=config.SAMPLE_TLE_FILE.exists(),
    )


@app.get("/api/tles", response_model=list[TLERecord])
def list_tles(group: str = config.DEFAULT_GROUP, use_sample_data: bool = False) -> list[TLERecord]:
    try:
        return get_tles(group=group, use_sample_data=use_sample_data)
    except TLEFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/conjunctions/run", response_model=ConjunctionResponse)
def run_conjunction_pipeline(req: ConjunctionRequest) -> ConjunctionResponse:
    try:
        records = get_tles(
            group=req.group,
            use_sample_data=req.use_sample_data,
            force_refresh=req.force_refresh,
        )
    except TLEFetchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not records:
        raise HTTPException(status_code=502, detail="No TLE records available to screen.")

    records = records[: config.MAX_OBJECTS_PER_RUN]

    start = datetime.now(timezone.utc)
    propagated = propagate_all(
        records,
        start=start,
        window_hours=req.window_hours,
        step_seconds=req.step_seconds,
    )

    if len(propagated) < 2:
        # Not enough successfully-propagated objects to form a pair.
        return ConjunctionResponse(
            generated_at_iso=start.isoformat(),
            group=req.group,
            objects_tracked=len(propagated),
            window_hours=req.window_hours,
            threshold_km=req.threshold_km,
            events=[],
        )

    raw_events = find_conjunctions(propagated, threshold_km=req.threshold_km)
    scored_events = score_all(raw_events, threshold_km=req.threshold_km, propagation_start=start)

    return ConjunctionResponse(
        generated_at_iso=start.isoformat(),
        group=req.group,
        objects_tracked=len(propagated),
        window_hours=req.window_hours,
        threshold_km=req.threshold_km,
        events=scored_events,
    )
