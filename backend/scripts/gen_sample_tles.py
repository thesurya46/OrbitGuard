"""
Generates backend/data/sample_tles.txt: a small, self-contained TLE set
used for offline demos and unit tests when live CelesTrak access isn't
available (e.g. no wifi at the venue, or this run has network disabled).

It starts from a well-known, publicly published example TLE for the ISS
(the same one commonly used in SGP4 library documentation/tutorials) and
generates a couple of synthetic "nearby object" TLEs by nudging the RAAN
and mean anomaly slightly, so the bundled sample data actually contains
at least one close-approach pair for OrbitGuard's pipeline to detect.

These synthetic objects are clearly fictional (SIM-1, SIM-2) and only
exist to make the demo self-testing without a network connection. Swap
in `use_sample_data=false` (the default) to screen real, live objects.

Run with:  python scripts/gen_sample_tles.py
"""

from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_tles.txt"

# Publicly published example ISS (ZARYA) TLE, widely used in SGP4
# tutorials/documentation as reference test data.
BASE_NAME = "ISS (ZARYA)"
BASE_LINE1 = "1 25544U 98067A   20233.54791667  .00000622  00000-0  17423-4 0  999"
BASE_LINE2 = "2 25544  51.6455  76.9234 0001428  93.5566  38.9430 15.49386052241639"


def tle_checksum(line_without_checksum: str) -> int:
    """Standard TLE checksum: sum of digits, '-' counts as 1, mod 10."""
    total = 0
    for ch in line_without_checksum:
        if ch.isdigit():
            total += int(ch)
        elif ch == "-":
            total += 1
    return total % 10


def with_checksum(line_68_chars: str) -> str:
    body = line_68_chars[:68]
    return f"{body}{tle_checksum(body)}"


def nudge_line2(line2: str, norad_id: str, raan_delta: float, ma_delta: float) -> str:
    """
    Return a modified line 2 with a different NORAD ID, RAAN, and mean
    anomaly, so the synthetic object is on a slightly different (but
    nearby) track than the base object.
    """
    inclination = line2[8:16]
    raan = float(line2[17:25])
    eccentricity = line2[26:33]
    arg_perigee = line2[34:42]
    mean_anomaly = float(line2[43:51])
    mean_motion_and_rest = line2[52:63]
    rev_number = line2[63:68]

    new_raan = (raan + raan_delta) % 360
    new_ma = (mean_anomaly + ma_delta) % 360

    body = (
        f"2 {norad_id:>5}"
        f" {inclination}"
        f" {new_raan:8.4f}"
        f" {eccentricity}"
        f" {arg_perigee}"
        f" {new_ma:8.4f}"
        f" {mean_motion_and_rest}"
        f"{rev_number}"
    )
    return with_checksum(body)


def nudge_line1(line1: str, norad_id: str) -> str:
    body = f"1 {norad_id:>5}U" + line1[8:68]
    return with_checksum(body)


def main() -> None:
    entries = [(BASE_NAME, with_checksum(BASE_LINE1), with_checksum(BASE_LINE2))]

    # Two synthetic nearby objects: small angular offsets translate into
    # a close (but non-identical) track, so the demo pipeline reliably
    # finds at least one flagged conjunction without needing real,
    # up-to-the-minute orbital data.
    synthetic_specs = [
        ("SIM-DEBRIS-1", "90001", 0.05, 0.15),
        ("SIM-DEBRIS-2", "90002", -0.08, -0.30),
    ]

    for name, norad_id, raan_delta, ma_delta in synthetic_specs:
        line1 = nudge_line1(BASE_LINE1, norad_id)
        line2 = nudge_line2(BASE_LINE2, norad_id, raan_delta, ma_delta)
        entries.append((name, line1, line2))

    lines = []
    for name, line1, line2 in entries:
        lines.append(name)
        lines.append(line1)
        lines.append(line2)

    OUTPUT_PATH.write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(entries)} TLE records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
