"""
Unit tests for ai_adjuster: validate_proposal, apply_adjustments,
and WeeklyReviewResult safety bounds — all without hitting the network.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.models.training_plan import PlannedWorkout, WorkoutStatus, WorkoutType
from app.services.training_plan.ai_adjuster import (
    AdjustmentProposal,
    WeeklyReviewResult,
    _is_recovery_week,
    apply_adjustments,
    suggest_week_adjustments,
    validate_proposal,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _workout(
    wid: int,
    wtype: WorkoutType = WorkoutType.EASY,
    distance_m: float = 10_000.0,
    duration_s: int = 3600,
    week_number: int = 1,
    scheduled_date: date | None = None,
) -> PlannedWorkout:
    w = MagicMock(spec=PlannedWorkout)
    w.id = wid
    w.workout_type = wtype
    w.target_distance_m = distance_m
    w.target_duration_s = duration_s
    w.week_number = week_number
    w.scheduled_date = scheduled_date or date(2026, 4, 21)
    w.status = WorkoutStatus.PLANNED
    w.rationale = ""
    return w


# ---------------------------------------------------------------------------
# _is_recovery_week
# ---------------------------------------------------------------------------


class TestIsRecoveryWeek:
    def test_week_4_is_recovery(self):
        assert _is_recovery_week(4) is True

    def test_week_8_is_recovery(self):
        assert _is_recovery_week(8) is True

    def test_week_3_is_not_recovery(self):
        assert _is_recovery_week(3) is False

    def test_week_5_is_not_recovery(self):
        assert _is_recovery_week(5) is False

    def test_week_0_is_not_recovery(self):
        assert _is_recovery_week(0) is False


# ---------------------------------------------------------------------------
# validate_proposal
# ---------------------------------------------------------------------------


class TestValidateProposal:
    def test_valid_volume_decrease(self):
        w = _workout(1, distance_m=10_000)
        proposal = AdjustmentProposal(workout_id=1, new_distance_m=8_000)
        valid, reason = validate_proposal(proposal, w, [w])
        assert valid, reason

    def test_volume_increase_within_cap(self):
        w = _workout(1, distance_m=10_000)
        proposal = AdjustmentProposal(workout_id=1, new_distance_m=11_000)
        valid, reason = validate_proposal(proposal, w, [w])
        assert valid, reason

    def test_volume_increase_over_cap_rejected(self):
        w = _workout(1, distance_m=10_000)
        proposal = AdjustmentProposal(workout_id=1, new_distance_m=12_000)  # +20%
        valid, reason = validate_proposal(proposal, w, [w])
        assert not valid
        assert "+10" in reason or "cap" in reason.lower()

    def test_volume_decrease_over_floor_rejected(self):
        w = _workout(1, distance_m=10_000)
        proposal = AdjustmentProposal(workout_id=1, new_distance_m=6_000)  # -40%
        valid, reason = validate_proposal(proposal, w, [w])
        assert not valid
        assert "30" in reason or "floor" in reason.lower()

    def test_hard_session_in_recovery_week_rejected(self):
        w = _workout(1, wtype=WorkoutType.EASY, week_number=4)
        proposal = AdjustmentProposal(workout_id=1, new_workout_type=WorkoutType.INTERVALS)
        valid, reason = validate_proposal(proposal, w, [w])
        assert not valid
        assert "recovery" in reason.lower() or "week 4" in reason

    def test_hard_session_allowed_in_normal_week(self):
        w = _workout(1, wtype=WorkoutType.EASY, week_number=3)
        proposal = AdjustmentProposal(workout_id=1, new_workout_type=WorkoutType.TEMPO)
        valid, reason = validate_proposal(proposal, w, [w])
        assert valid, reason

    def test_hard_session_spacing_violation_rejected(self):
        # Two hard sessions on consecutive days → reject
        w1 = _workout(1, wtype=WorkoutType.INTERVALS, scheduled_date=date(2026, 4, 21))
        w2 = _workout(2, wtype=WorkoutType.EASY, scheduled_date=date(2026, 4, 22))
        proposal = AdjustmentProposal(workout_id=2, new_workout_type=WorkoutType.TEMPO)
        valid, reason = validate_proposal(proposal, w2, [w1, w2])
        assert not valid
        assert "72" in reason or "hard session" in reason.lower()

    def test_hard_session_spacing_ok_when_far_apart(self):
        # Hard sessions 4 days apart → OK
        w1 = _workout(1, wtype=WorkoutType.INTERVALS, scheduled_date=date(2026, 4, 21))
        w2 = _workout(2, wtype=WorkoutType.EASY, scheduled_date=date(2026, 4, 25))
        proposal = AdjustmentProposal(workout_id=2, new_workout_type=WorkoutType.TEMPO)
        valid, reason = validate_proposal(proposal, w2, [w1, w2])
        assert valid, reason

    def test_downgrade_to_easy_always_valid(self):
        w = _workout(1, wtype=WorkoutType.INTERVALS)
        proposal = AdjustmentProposal(workout_id=1, new_workout_type=WorkoutType.EASY)
        valid, _ = validate_proposal(proposal, w, [w])
        assert valid

    def test_proposal_no_changes_always_valid(self):
        w = _workout(1)
        proposal = AdjustmentProposal(workout_id=1, rationale="just a note")
        valid, _ = validate_proposal(proposal, w, [w])
        assert valid


# ---------------------------------------------------------------------------
# apply_adjustments
# ---------------------------------------------------------------------------


class TestApplyAdjustments:
    def test_valid_distance_applied(self):
        w = _workout(1, distance_m=10_000, duration_s=3600)
        proposal = AdjustmentProposal(workout_id=1, new_distance_m=9_000)
        applied = apply_adjustments([proposal], {1: w}, [w])
        assert len(applied) == 1
        assert w.target_distance_m == 9_000
        # Duration scaled proportionally: 3600 * 0.9 = 3240
        assert w.target_duration_s == 3240

    def test_invalid_proposal_skipped(self):
        w = _workout(1, distance_m=10_000)
        proposal = AdjustmentProposal(workout_id=1, new_distance_m=15_000)  # +50% → rejected
        applied = apply_adjustments([proposal], {1: w}, [w])
        assert len(applied) == 0
        assert w.target_distance_m == 10_000  # unchanged

    def test_unknown_workout_id_skipped(self):
        w = _workout(1)
        proposal = AdjustmentProposal(workout_id=999, new_distance_m=8_000)
        applied = apply_adjustments([proposal], {1: w}, [w])
        assert len(applied) == 0

    def test_type_swap_applied(self):
        w = _workout(1, wtype=WorkoutType.INTERVALS, week_number=3)
        proposal = AdjustmentProposal(workout_id=1, new_workout_type=WorkoutType.EASY)
        applied = apply_adjustments([proposal], {1: w}, [w])
        assert len(applied) == 1
        assert w.workout_type == WorkoutType.EASY

    def test_rationale_updated(self):
        w = _workout(1)
        proposal = AdjustmentProposal(workout_id=1, new_distance_m=9_000, rationale="Load reduction")
        apply_adjustments([proposal], {1: w}, [w])
        assert w.rationale == "Load reduction"

    def test_multiple_proposals_mixed_validity(self):
        w1 = _workout(1, distance_m=10_000)
        w2 = _workout(2, distance_m=10_000)
        proposals = [
            AdjustmentProposal(workout_id=1, new_distance_m=9_000),   # valid
            AdjustmentProposal(workout_id=2, new_distance_m=20_000),  # invalid (+100%)
        ]
        applied = apply_adjustments(proposals, {1: w1, 2: w2}, [w1, w2])
        assert len(applied) == 1
        assert w1.target_distance_m == 9_000
        assert w2.target_distance_m == 10_000  # unchanged


# ---------------------------------------------------------------------------
# suggest_week_adjustments — mocked Claude
# ---------------------------------------------------------------------------


class TestSuggestWeekAdjustments:
    def _make_plan(self):
        plan = MagicMock()
        plan.goal_distance_km = 21.0975
        plan.current_phase = MagicMock()
        plan.current_phase.value = "build"
        plan.vdot = 48.0
        plan.total_weeks = 12
        return plan

    def test_empty_next_week_returns_empty(self):
        plan = self._make_plan()
        result = suggest_week_adjustments(plan, [], [], None)
        assert result.proposals == []
        assert result.injury_flag is None

    def test_claude_error_returns_empty_fallback(self):
        """If Claude raises, we get empty proposals (deterministic fallback)."""
        plan = self._make_plan()
        w = _workout(1)

        with patch(
            "app.services.training_plan.ai_adjuster.claude.messages.create",
            side_effect=Exception("network error"),
        ):
            result = suggest_week_adjustments(plan, [w], [], None)

        assert result.proposals == []
        assert result.injury_flag is None
        assert result.input_tokens == 0

    def test_no_tool_calls_returns_empty(self):
        """Claude responds with text only (no changes needed) → empty proposals."""
        plan = self._make_plan()
        w = _workout(1)

        mock_response = MagicMock()
        mock_response.content = []  # no tool_use blocks
        mock_response.usage.input_tokens = 500
        mock_response.usage.output_tokens = 50
        mock_response.usage.cache_read_input_tokens = 300
        mock_response.usage.cache_creation_input_tokens = 0

        with patch(
            "app.services.training_plan.ai_adjuster.claude.messages.create",
            return_value=mock_response,
        ):
            result = suggest_week_adjustments(plan, [w], [], None)

        assert result.proposals == []
        assert result.injury_flag is None
        assert result.input_tokens == 500

    def test_swap_tool_call_parsed(self):
        plan = self._make_plan()
        w = _workout(1, wtype=WorkoutType.INTERVALS)

        tool_block = MagicMock()
        tool_block.type = "tool_use"
        tool_block.name = "propose_workout_swap"
        tool_block.input = {
            "workout_id": 1,
            "new_type": "easy",
            "rationale": "High load last week",
        }

        mock_response = MagicMock()
        mock_response.content = [tool_block]
        mock_response.usage.input_tokens = 600
        mock_response.usage.output_tokens = 80
        mock_response.usage.cache_read_input_tokens = 400
        mock_response.usage.cache_creation_input_tokens = 0

        with patch(
            "app.services.training_plan.ai_adjuster.claude.messages.create",
            return_value=mock_response,
        ):
            result = suggest_week_adjustments(plan, [w], [], None)

        assert len(result.proposals) == 1
        assert result.proposals[0].workout_id == 1
        assert result.proposals[0].new_workout_type == WorkoutType.EASY
        assert result.injury_flag is None

    def test_injury_flag_clears_proposals(self):
        plan = self._make_plan()
        w = _workout(1)

        swap_block = MagicMock()
        swap_block.type = "tool_use"
        swap_block.name = "propose_workout_swap"
        swap_block.input = {"workout_id": 1, "new_type": "easy", "rationale": "x"}

        flag_block = MagicMock()
        flag_block.type = "tool_use"
        flag_block.name = "flag_injury_risk"
        flag_block.input = {"reason": "Three consecutive missed sessions"}

        mock_response = MagicMock()
        mock_response.content = [swap_block, flag_block]
        mock_response.usage.input_tokens = 700
        mock_response.usage.output_tokens = 100
        mock_response.usage.cache_read_input_tokens = 0
        mock_response.usage.cache_creation_input_tokens = 200

        with patch(
            "app.services.training_plan.ai_adjuster.claude.messages.create",
            return_value=mock_response,
        ):
            result = suggest_week_adjustments(plan, [w], [], None)

        # Injury flag must clear any already-collected proposals
        assert result.proposals == []
        assert result.injury_flag == "Three consecutive missed sessions"

    def test_volume_change_tool_call_parsed(self):
        plan = self._make_plan()
        w = _workout(1, distance_m=10_000)

        vol_block = MagicMock()
        vol_block.type = "tool_use"
        vol_block.name = "propose_volume_change"
        vol_block.input = {
            "workout_id": 1,
            "distance_factor": 0.8,
            "rationale": "Reduce after illness",
        }

        mock_response = MagicMock()
        mock_response.content = [vol_block]
        mock_response.usage.input_tokens = 550
        mock_response.usage.output_tokens = 70
        mock_response.usage.cache_read_input_tokens = 350
        mock_response.usage.cache_creation_input_tokens = 0

        with patch(
            "app.services.training_plan.ai_adjuster.claude.messages.create",
            return_value=mock_response,
        ):
            result = suggest_week_adjustments(plan, [w], [], None)

        assert len(result.proposals) == 1
        assert result.proposals[0].new_distance_m == pytest.approx(8_000)
