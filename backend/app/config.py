"""
Central configuration for OrbitGuard.

Every tunable knob for the pipeline lives here so the rest of the codebase
never hardcodes a magic number.
"""

import os
from pathlib import Path

# --- Paths -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
SAMPLE_TLE_FILE = DATA_DIR / "sample_tles.txt"

CACHE_DIR.mkdir(parents=True, exist_ok=True)

# --- CelesTrak -----------------------------------------------------------
# CelesTrak publishes TLE sets grouped by category. "stations" is a small,
# fast group (ISS, Tiangong, etc.) that is good for local testing.
# Full catalogs like "active" or "starlink" are much larger.
CELESTRAK_URL_TEMPLATE = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP={group}&FORMAT=tle"
)
DEFAULT_GROUP = os.environ.get("ORBITGUARD_GROUP", "stations")

# How long a cached TLE file is considered fresh before re-fetching.
CACHE_TTL_SECONDS = int(os.environ.get("ORBITGUARD_CACHE_TTL", 60 * 60 * 3))  # 3h

# --- Propagation ---------------------------------------------------------
DEFAULT_WINDOW_HOURS = float(os.environ.get("ORBITGUARD_WINDOW_HOURS", 72))
DEFAULT_STEP_SECONDS = float(os.environ.get("ORBITGUARD_STEP_SECONDS", 60))

# --- Conjunction screening -------------------------------------------------
# Any pair whose closest approach is below this distance is flagged.
DEFAULT_THRESHOLD_KM = float(os.environ.get("ORBITGUARD_THRESHOLD_KM", 25))

# Below this distance, treat as "same physical object" (e.g. docked modules) not a real conjunction.
MIN_MEANINGFUL_DISTANCE_KM = float(os.environ.get("ORBITGUARD_MIN_DISTANCE_KM", 0.5))

# Safety cap so a demo run against a huge catalog doesn't hang the API.
MAX_OBJECTS_PER_RUN = int(os.environ.get("ORBITGUARD_MAX_OBJECTS", 60))

# --- Risk scoring ----------------------------------------------------------
# Risk score blends how close the approach is (relative to the threshold)
# with how fast the objects are closing (more energy = more damage
# potential in an actual collision). Weights must sum to 1.0.
RISK_DISTANCE_WEIGHT = 0.7
RISK_VELOCITY_WEIGHT = 0.3
# Relative velocity (km/s) that maps to a "maximum" velocity risk contribution.
# Typical LEO relative velocities for crossing orbits top out around 14-15 km/s.
RISK_VELOCITY_REFERENCE_KMPS = 15.0

# --- CORS (frontend dev server) ------------------------------------------
FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
