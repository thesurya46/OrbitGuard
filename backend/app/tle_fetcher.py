"""
Pulls Two-Line Element (TLE) sets from CelesTrak, with a local disk cache
so repeated runs don't hammer the API, and a bundled sample file so the
whole pipeline can be demoed offline (e.g. on a hackathon show floor with
no reliable wifi).

CelesTrak's TLE text format repeats in 3-line blocks:
    <object name>
    <line 1>
    <line 2>
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import List

import requests

from . import config
from .models import TLERecord


class TLEFetchError(RuntimeError):
    """Raised when TLE data can't be obtained from any source."""


def _parse_tle_text(text: str) -> List[TLERecord]:
    lines = [ln.rstrip("\n") for ln in text.strip().splitlines() if ln.strip()]
    records: List[TLERecord] = []

    i = 0
    while i + 2 < len(lines) + 1 and i + 2 <= len(lines):
        name = lines[i].strip()
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()
        if not (line1.startswith("1 ") and line2.startswith("2 ")):
            # Malformed block - skip forward one line and try to resync.
            i += 1
            continue
        norad_id = line1[2:7].strip()
        records.append(
            TLERecord(name=name, norad_id=norad_id, line1=line1, line2=line2)
        )
        i += 3

    return records


def _cache_path(group: str) -> Path:
    return config.CACHE_DIR / f"{group}.tle"


def _cache_is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = time.time() - path.stat().st_mtime
    return age < config.CACHE_TTL_SECONDS


def fetch_live(group: str) -> List[TLERecord]:
    """Fetch fresh TLE data from CelesTrak for the given group."""
    url = config.CELESTRAK_URL_TEMPLATE.format(group=group)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    records = _parse_tle_text(response.text)
    if not records:
        raise TLEFetchError(f"CelesTrak returned no usable TLE records for '{group}'")
    return records


def load_sample() -> List[TLERecord]:
    """Load the bundled sample TLE set for offline demos/tests."""
    if not config.SAMPLE_TLE_FILE.exists():
        raise TLEFetchError(f"Sample TLE file not found at {config.SAMPLE_TLE_FILE}")
    text = config.SAMPLE_TLE_FILE.read_text()
    return _parse_tle_text(text)


def get_tles(
    group: str = config.DEFAULT_GROUP,
    use_sample_data: bool = False,
    force_refresh: bool = False,
) -> List[TLERecord]:
    """
    Main entry point used by the API layer.

    Resolution order:
      1. explicit sample-data request -> bundled sample file
      2. fresh cache on disk (unless force_refresh) -> cached file
      3. live CelesTrak fetch -> cache it for next time
      4. live fetch fails -> fall back to sample data so the demo never
         hard-fails just because the venue wifi is down
    """
    if use_sample_data:
        return load_sample()

    cache_file = _cache_path(group)

    if not force_refresh and _cache_is_fresh(cache_file):
        return _parse_tle_text(cache_file.read_text())

    try:
        if group == "stations":
            # CelesTrak's "stations" group alone contains modules of the ISS/Tiangong complexes
            # that are docked together (<0.5 km). To screen space stations against independent
            # objects, combine station records with debris records.
            station_records = fetch_live("stations")
            try:
                debris_records = fetch_live("debris")
            except Exception:
                debris_records = []
            seen_ids = set()
            records: List[TLERecord] = []
            for r in station_records + debris_records:
                if r.norad_id not in seen_ids:
                    seen_ids.add(r.norad_id)
                    records.append(r)
        else:
            records = fetch_live(group)

        cache_file.write_text(
            "\n".join(f"{r.name}\n{r.line1}\n{r.line2}" for r in records)
        )
        return records
    except (requests.RequestException, TLEFetchError):
        # Offline fallback: stale cache is still better than sample data
        # if it exists, otherwise fall back to the bundled sample set.
        if cache_file.exists():
            return _parse_tle_text(cache_file.read_text())
        return load_sample()
