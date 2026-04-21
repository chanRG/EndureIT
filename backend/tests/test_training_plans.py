"""
Tests for training plan services: templates, pace_calculator, matcher.
"""

import pytest

from app.models.training_plan import FitnessLevel, PlanPhase, WorkoutType
from app.services.training_plan.templates import (
    get_template,
    is_stepback_week,
    phase_for_week,
    weekly_km_for_week,
)
from app.services.training_plan.pace_calculator import (
    compute_vdot,
    derive_training_paces,
)

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


class TestTemplates:
    def test_half_marathon_12wk_phases_sum_to_total(self):
        t = get_template(21.0975, 12, FitnessLevel.INTERMEDIATE)
        assert sum(c for _, c in t.phases) == t.weeks

    def test_marathon_16wk_phases_sum_to_total(self):
        t = get_template(42.195, 16, FitnessLevel.INTERMEDIATE)
        assert sum(c for _, c in t.phases) == t.weeks

    def test_10k_8wk_phases_sum_to_total(self):
        t = get_template(10.0, 8, FitnessLevel.INTERMEDIATE)
        assert sum(c for _, c in t.phases) == t.weeks

    def test_5k_6wk_beginner(self):
        t = get_template(5.0, 6, FitnessLevel.BEGINNER)
        assert t.distance_km == 5.0
        assert t.weeks == 6

    def test_phase_for_week_base_is_first(self):
        t = get_template(21.0975, 12, FitnessLevel.INTERMEDIATE)
        assert phase_for_week(t, 0) == PlanPhase.BASE

    def test_phase_for_week_taper_is_last(self):
        t = get_template(21.0975, 12, FitnessLevel.INTERMEDIATE)
        assert phase_for_week(t, t.weeks - 1) == PlanPhase.TAPER

    def test_stepback_weeks_at_4_8_12(self):
        assert is_stepback_week(3) is True  # week 4
        assert is_stepback_week(7) is True  # week 8
        assert is_stepback_week(11) is True  # week 12
        assert is_stepback_week(0) is False
        assert is_stepback_week(1) is False

    def test_weekly_km_taper_decreases(self):
        t = get_template(42.195, 16, FitnessLevel.INTERMEDIATE)
        taper_start = t.weeks - dict(t.phases)[PlanPhase.TAPER]
        km_first_taper = weekly_km_for_week(t, taper_start)
        km_last_taper = weekly_km_for_week(t, t.weeks - 1)
        assert km_last_taper < km_first_taper

    def test_weekly_km_stepback_lower(self):
        t = get_template(21.0975, 12, FitnessLevel.INTERMEDIATE)
        # Week 3 (idx=2) is normal; week 4 (idx=3) is stepback
        normal_km = weekly_km_for_week(t, 2)
        stepback_km = weekly_km_for_week(t, 3)
        assert stepback_km < normal_km

    def test_day_fractions_sum_to_approx_one(self):
        """Non-taper phases should have day fractions summing ≥ 0.70."""
        t = get_template(21.0975, 12, FitnessLevel.INTERMEDIATE)
        for phase, pattern in t.phase_patterns.items():
            if phase == PlanPhase.TAPER:
                continue  # Taper weeks intentionally have reduced volume
            total = sum(d.distance_fraction for d in pattern.days.values())
            assert (
                0.70 <= total <= 1.10
            ), f"Phase {phase}: day fractions sum {total:.2f}"

    def test_fallback_returns_closest_template(self):
        # Ask for a distance/week combo with no exact match
        t = get_template(21.0975, 10, FitnessLevel.INTERMEDIATE)
        assert t is not None

    def test_all_day_plans_have_valid_hr_zone(self):
        t = get_template(42.195, 16, FitnessLevel.INTERMEDIATE)
        for pattern in t.phase_patterns.values():
            for day in pattern.days.values():
                assert 1 <= day.hr_zone <= 5


# ---------------------------------------------------------------------------
# VDOT / Pace Calculator
# ---------------------------------------------------------------------------


class TestVdot:
    # Jack Daniels' table values for reference:
    # 20:00 5K → VDOT ≈ 48
    # 40:00 10K → VDOT ≈ 48
    # 45:00 10K → VDOT ≈ 42

    def test_vdot_5k_20min(self):
        vdot = compute_vdot(5000, 20 * 60)
        assert 46 <= vdot <= 50, f"Expected ~48, got {vdot:.1f}"

    def test_vdot_10k_40min(self):
        # 40:00 10K = 4:00/km, sustained 40 min → Daniels formula ≈ 52
        vdot = compute_vdot(10000, 40 * 60)
        assert 49 <= vdot <= 54, f"Expected ~52, got {vdot:.1f}"

    def test_vdot_half_marathon_1h45(self):
        # 1:45 HM = 5:00/km, sustained 105 min → Daniels formula ≈ 43
        vdot = compute_vdot(21097.5, 105 * 60)
        assert 40 <= vdot <= 46, f"Expected ~43, got {vdot:.1f}"

    def test_vdot_raises_on_zero(self):
        with pytest.raises(ValueError):
            compute_vdot(5000, 0)

    def test_derive_paces_ordering(self):
        # Faster VDOT → faster (lower min/km) paces across all zones
        paces_48 = derive_training_paces(48)
        paces_60 = derive_training_paces(60)
        assert paces_60["easy_pace"] < paces_48["easy_pace"]
        assert paces_60["threshold_pace"] < paces_48["threshold_pace"]
        assert paces_60["interval_pace"] < paces_48["interval_pace"]

    def test_pace_zones_ordered_fastest_to_slowest(self):
        """repetition < interval < threshold < marathon < easy"""
        paces = derive_training_paces(50)
        assert paces["repetition_pace"] < paces["interval_pace"]
        assert paces["interval_pace"] < paces["threshold_pace"]
        assert paces["threshold_pace"] < paces["marathon_pace"]
        assert paces["marathon_pace"] < paces["easy_pace"]

    def test_vdot_clamped_at_table_bounds(self):
        # VDOT=10 (below table min) should not raise
        paces = derive_training_paces(10)
        assert paces["easy_pace"] > 0

        # VDOT=100 (above table max) should not raise
        paces = derive_training_paces(100)
        assert paces["easy_pace"] > 0


# ---------------------------------------------------------------------------
# Matcher scoring (unit — no DB)
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock
from datetime import datetime, date as date_type

from app.services.training_plan.matcher import score_match, AUTO_LINK_THRESHOLD


def _make_activity(
    distance_m: float = 10000,
    moving_time: int = 3000,
    activity_type: str = "Run",
    activity_date: date_type = None,
) -> MagicMock:
    a = MagicMock(
        spec=[
            "distance",
            "moving_time",
            "elapsed_time",
            "activity_type",
            "start_date",
            "strava_id",
        ]
    )
    a.distance = distance_m
    a.moving_time = moving_time
    a.elapsed_time = moving_time
    a.activity_type = activity_type
    a.start_date = datetime.combine(
        activity_date or date_type.today(), datetime.min.time()
    )
    a.strava_id = 12345
    return a


def _make_workout(
    distance_m: float = 10000,
    duration_s: int = 3000,
    workout_type: WorkoutType = WorkoutType.EASY,
    scheduled_date: date_type = None,
) -> MagicMock:
    w = MagicMock(
        spec=[
            "target_distance_m",
            "target_duration_s",
            "workout_type",
            "scheduled_date",
        ]
    )
    w.target_distance_m = distance_m
    w.target_duration_s = duration_s
    w.workout_type = workout_type
    w.scheduled_date = scheduled_date or date_type.today()
    return w


class TestMatcher:
    def test_perfect_match_scores_high(self):
        today = date_type.today()
        a = _make_activity(10000, 3000, "Run", today)
        w = _make_workout(10000, 3000, WorkoutType.EASY, today)
        s = score_match(a, w)
        assert s >= AUTO_LINK_THRESHOLD

    def test_wrong_sport_scores_low(self):
        """A Ride matched against a Run workout should score 0 on sport (0.4 weight),
        capping total at 0.6 even with perfect distance/date/duration."""
        today = date_type.today()
        a = _make_activity(10000, 3000, "Ride", today)
        w = _make_workout(10000, 3000, WorkoutType.EASY, today)
        s = score_match(a, w)
        # Sport contributes 0.0 (0.4 weight) → max possible is 0.6
        assert s <= AUTO_LINK_THRESHOLD

    def test_ride_matches_cross(self):
        today = date_type.today()
        a = _make_activity(20000, 3600, "Ride", today)
        w = _make_workout(20000, 3600, WorkoutType.CROSS, today)
        s = score_match(a, w)
        assert s >= AUTO_LINK_THRESHOLD

    def test_date_one_day_off_penalised(self):
        from datetime import timedelta

        today = date_type.today()
        a = _make_activity(10000, 3000, "Run", today)
        w_same = _make_workout(10000, 3000, WorkoutType.EASY, today)
        w_off = _make_workout(10000, 3000, WorkoutType.EASY, today + timedelta(days=1))
        assert score_match(a, w_same) > score_match(a, w_off)

    def test_distance_way_off_is_penalised(self):
        """A 3 km run matched against a 20 km long run should score zero on distance and duration."""
        from datetime import timedelta

        today = date_type.today()
        yesterday = today - timedelta(days=1)
        # Activity yesterday, workout today — loses date score too
        a = _make_activity(3000, 1500, "Run", yesterday)
        w = _make_workout(20000, 6000, WorkoutType.LONG, today)
        s = score_match(a, w)
        # date=0.5 (±1), distance=0.0, duration=0.0, sport=1.0 → 0.4 + 0.15 = 0.55
        assert s < AUTO_LINK_THRESHOLD
