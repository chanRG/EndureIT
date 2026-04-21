"""
VDOT-based pace calculator (Jack Daniels Running Formula).

VDOT is derived from a recent race performance, then used to generate
training pace zones (easy, marathon, threshold, interval, repetition).

Reference: Daniels, J. (2014). Daniels' Running Formula, 3rd ed.
All paces are in min/km (float). Distances in metres.
"""

from __future__ import annotations

import math
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.strava_activity import StravaActivity
from app.models.training_plan import TrainingPace
from app.models.user import User

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# VDOT lookup table: vdot → 5 pace zones (min/km, as floats)
# Generated from Daniels' tables; covers VDOT 30–85.
# Keys are integer VDOT values; interpolation is used for intermediate values.
# Columns: easy_lo, easy_hi, marathon, threshold, interval, repetition
# ---------------------------------------------------------------------------
_VDOT_TABLE: dict[int, tuple[float, float, float, float, float, float]] = {
    30: (9.18, 10.26, 8.57, 7.58, 7.18, 6.53),
    32: (8.45, 9.45, 8.09, 7.13, 6.44, 6.12),
    34: (8.09, 9.05, 7.40, 6.41, 6.11, 5.44),
    36: (7.44, 8.37, 7.16, 6.20, 5.51, 5.21),
    38: (7.20, 8.10, 6.53, 5.59, 5.31, 5.02),
    40: (6.59, 7.47, 6.32, 5.41, 5.14, 4.45),
    42: (6.39, 7.23, 6.13, 5.24, 4.58, 4.30),
    44: (6.21, 7.02, 5.56, 5.08, 4.43, 4.16),
    46: (6.04, 6.44, 5.41, 4.55, 4.30, 4.03),
    48: (5.50, 6.28, 5.27, 4.42, 4.18, 3.52),
    50: (5.37, 6.14, 5.15, 4.31, 4.07, 3.42),
    52: (5.25, 6.01, 5.04, 4.21, 3.57, 3.33),
    54: (5.14, 5.49, 4.54, 4.12, 3.48, 3.24),
    56: (5.04, 5.38, 4.44, 4.03, 3.40, 3.16),
    58: (4.55, 5.28, 4.36, 3.55, 3.32, 3.09),
    60: (4.47, 5.19, 4.27, 3.47, 3.25, 3.02),
    62: (4.39, 5.10, 4.19, 3.40, 3.18, 2.56),
    64: (4.32, 5.02, 4.12, 3.33, 3.12, 2.50),
    66: (4.25, 4.55, 4.06, 3.27, 3.06, 2.45),
    68: (4.18, 4.48, 3.59, 3.21, 3.01, 2.40),
    70: (4.12, 4.42, 3.54, 3.16, 2.56, 2.35),
    72: (4.07, 4.36, 3.48, 3.11, 2.51, 2.31),
    74: (4.01, 4.31, 3.43, 3.06, 2.47, 2.27),
    76: (3.56, 4.25, 3.38, 3.02, 2.43, 2.23),
    78: (3.51, 4.20, 3.33, 2.57, 2.39, 2.20),
    80: (3.47, 4.15, 3.29, 2.53, 2.35, 2.16),
    82: (3.43, 4.11, 3.25, 2.50, 2.32, 2.13),
    84: (3.39, 4.07, 3.22, 2.46, 2.29, 2.10),
    85: (3.37, 4.05, 3.20, 2.45, 2.27, 2.09),
}


def _pace_str_to_float(pace: float | tuple) -> float:
    """Convert a (min, sec) implicit float like 5.30 → 5.5 (i.e. 5:30/km)."""
    # Values are stored as M.SS where SS is seconds, e.g. 5.30 = 5 min 30 sec
    minutes = int(pace)
    seconds = round((pace - minutes) * 100)
    return minutes + seconds / 60.0


def _build_vdot_table() -> dict[int, dict[str, float]]:
    result = {}
    for vdot, (el, eh, mp, tp, ip, rp) in _VDOT_TABLE.items():
        result[vdot] = {
            "easy_lo": _pace_str_to_float(el),
            "easy_hi": _pace_str_to_float(eh),
            "marathon": _pace_str_to_float(mp),
            "threshold": _pace_str_to_float(tp),
            "interval": _pace_str_to_float(ip),
            "repetition": _pace_str_to_float(rp),
        }
    return result


_PACE_TABLE: dict[int, dict[str, float]] = _build_vdot_table()
_VDOT_KEYS = sorted(_PACE_TABLE.keys())


def _interp(vdot: float, key: str) -> float:
    """Linearly interpolate a pace value from the VDOT table."""
    lo = (
        max(v for v in _VDOT_KEYS if v <= vdot)
        if vdot >= _VDOT_KEYS[0]
        else _VDOT_KEYS[0]
    )
    hi = (
        min(v for v in _VDOT_KEYS if v >= vdot)
        if vdot <= _VDOT_KEYS[-1]
        else _VDOT_KEYS[-1]
    )
    if lo == hi:
        return _PACE_TABLE[lo][key]
    t = (vdot - lo) / (hi - lo)
    return _PACE_TABLE[lo][key] + t * (_PACE_TABLE[hi][key] - _PACE_TABLE[lo][key])


# ---------------------------------------------------------------------------
# VDOT formula (Daniels & Gilbert, 1979)
# ---------------------------------------------------------------------------


def _velocity_at_vo2max(time_min: float, distance_m: float) -> float:
    """VO2 consumed at race pace as a fraction of VO2max, using Daniels formula."""
    speed = distance_m / time_min  # m/min
    vo2 = -4.60 + 0.182258 * speed + 0.000104 * speed**2
    return vo2


def _percent_vo2max(time_min: float) -> float:
    """Percent of VO2max sustainable for a given race duration (minutes)."""
    t = time_min
    pct = (
        0.8 + 0.1894393 * math.exp(-0.012778 * t) + 0.2989558 * math.exp(-0.1932605 * t)
    )
    return pct


def compute_vdot(distance_m: float, time_s: float) -> float:
    """Compute VDOT from a race result (distance in metres, time in seconds)."""
    if time_s <= 0 or distance_m <= 0:
        raise ValueError("distance and time must be positive")
    time_min = time_s / 60.0
    vo2 = _velocity_at_vo2max(time_min, distance_m)
    pct = _percent_vo2max(time_min)
    return vo2 / pct


# ---------------------------------------------------------------------------
# Derive training paces from VDOT
# ---------------------------------------------------------------------------


def derive_training_paces(vdot: float) -> dict[str, float]:
    """Return training paces (min/km) for a given VDOT value."""
    clamped = max(_VDOT_KEYS[0], min(_VDOT_KEYS[-1], vdot))
    easy_lo = _interp(clamped, "easy_lo")
    easy_hi = _interp(clamped, "easy_hi")
    return {
        "easy_pace": (easy_lo + easy_hi) / 2.0,
        "marathon_pace": _interp(clamped, "marathon"),
        "threshold_pace": _interp(clamped, "threshold"),
        "interval_pace": _interp(clamped, "interval"),
        "repetition_pace": _interp(clamped, "repetition"),
    }


# ---------------------------------------------------------------------------
# Best-efforts extractor
# ---------------------------------------------------------------------------

# Strava best-effort names and their distances in metres
_EFFORT_DISTANCES: dict[str, float] = {
    "400m": 400,
    "1/2 mile": 804.67,
    "1K": 1000,
    "1 mile": 1609.34,
    "2 mile": 3218.69,
    "5K": 5000,
    "10K": 10000,
    "15K": 15000,
    "10 mile": 16093.4,
    "20K": 20000,
    "Half-Marathon": 21097.5,
    "Marathon": 42195,
}

# Reliability weight: longer efforts give more accurate VDOT
_EFFORT_WEIGHTS: dict[str, float] = {
    "400m": 0.4,
    "1/2 mile": 0.5,
    "1K": 0.6,
    "1 mile": 0.7,
    "2 mile": 0.75,
    "5K": 0.9,
    "10K": 1.0,
    "15K": 1.0,
    "10 mile": 1.0,
    "20K": 1.0,
    "Half-Marathon": 1.0,
    "Marathon": 1.0,
}


def _extract_best_efforts(activity: StravaActivity) -> dict[str, float]:
    """Return {effort_name: elapsed_seconds} from a Strava activity's best_efforts JSON."""
    efforts: dict[str, float] = {}
    raw = activity.best_efforts
    if not raw or not isinstance(raw, list):
        return efforts
    for effort in raw:
        name = effort.get("name", "")
        elapsed = effort.get("elapsed_time")
        if (
            name in _EFFORT_DISTANCES
            and isinstance(elapsed, (int, float))
            and elapsed > 0
        ):
            # Keep the fastest (smallest) time per distance
            if name not in efforts or elapsed < efforts[name]:
                efforts[name] = float(elapsed)
    return efforts


def compute_vdot_from_activities(activities: list[StravaActivity]) -> Optional[float]:
    """
    Compute a weighted-average VDOT from best efforts across recent activities.
    Returns None if no usable efforts are found.
    """
    weighted_sum = 0.0
    weight_total = 0.0
    source_ids: list[int] = []

    for activity in activities:
        efforts = _extract_best_efforts(activity)
        if not efforts:
            continue
        source_ids.append(activity.strava_id)
        for name, time_s in efforts.items():
            dist_m = _EFFORT_DISTANCES[name]
            try:
                v = compute_vdot(dist_m, time_s)
            except ValueError:
                continue
            w = _EFFORT_WEIGHTS.get(name, 0.8)
            weighted_sum += v * w
            weight_total += w

    if weight_total == 0:
        return None

    return weighted_sum / weight_total


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def compute_vdot_from_db(db: Session, user: User) -> tuple[Optional[float], list[int]]:
    """
    Query the user's recent running activities and compute VDOT.
    Returns (vdot, source_strava_ids).
    """
    activities = (
        db.query(StravaActivity)
        .filter(
            StravaActivity.user_id == user.id,
            StravaActivity.activity_type.ilike("%run%"),
            StravaActivity.best_efforts.isnot(None),
        )
        .order_by(StravaActivity.start_date.desc())
        .limit(50)
        .all()
    )

    if not activities:
        logger.info("No running activities with best efforts for user %d", user.id)
        return None, []

    vdot = compute_vdot_from_activities(activities)
    source_ids = [a.strava_id for a in activities if a.best_efforts]
    return vdot, source_ids


def upsert_training_paces(
    db: Session,
    user: User,
    vdot: float,
    source_activity_ids: list[int],
    max_hr: Optional[int] = None,
    threshold_hr: Optional[int] = None,
    resting_hr: Optional[int] = None,
) -> TrainingPace:
    """Create or update the TrainingPace record for a user."""
    from datetime import datetime

    paces = derive_training_paces(vdot)

    record = db.query(TrainingPace).filter(TrainingPace.user_id == user.id).first()
    if record is None:
        record = TrainingPace(user_id=user.id)
        db.add(record)

    record.vdot = vdot
    record.easy_pace = paces["easy_pace"]
    record.marathon_pace = paces["marathon_pace"]
    record.threshold_pace = paces["threshold_pace"]
    record.interval_pace = paces["interval_pace"]
    record.repetition_pace = paces["repetition_pace"]
    record.source_activity_ids = source_activity_ids
    record.computed_at = datetime.utcnow()

    if max_hr is not None:
        record.max_hr = max_hr
    if threshold_hr is not None:
        record.threshold_hr = threshold_hr
    if resting_hr is not None:
        record.resting_hr = resting_hr

    db.flush()
    return record
