"""
Claude-powered weekly plan adjuster.

This module is intentionally minimal in Phase 1 — it provides the interface
and safety validator but the full Claude tool-use implementation ships in
feat/ai-weekly-review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.training_plan import PlannedWorkout, WorkoutType


@dataclass
class AdjustmentProposal:
    workout_id: int
    new_workout_type: Optional[WorkoutType] = None
    new_distance_m: Optional[float] = None
    new_duration_s: Optional[int] = None
    rationale: str = ""


# Safety bounds applied before any DB write
_MAX_VOLUME_INCREASE = 0.10  # +10 %
_MAX_VOLUME_DECREASE = 0.30  # −30 %


def validate_proposal(
    proposal: AdjustmentProposal,
    original: PlannedWorkout,
) -> tuple[bool, str]:
    """
    Return (is_valid, reason).
    Rejects any proposal that violates safety bounds.
    """
    if proposal.new_distance_m is not None and original.target_distance_m:
        ratio = proposal.new_distance_m / original.target_distance_m
        if ratio > 1 + _MAX_VOLUME_INCREASE:
            return False, f"Volume increase {ratio:.0%} exceeds +10% cap"
        if ratio < 1 - _MAX_VOLUME_DECREASE:
            return False, f"Volume decrease {ratio:.0%} exceeds −30% floor"

    return True, ""


def apply_adjustments(
    proposals: list[AdjustmentProposal],
    workouts: dict[int, PlannedWorkout],
) -> list[tuple[PlannedWorkout, AdjustmentProposal]]:
    """
    Apply validated proposals to in-memory workout objects.
    Returns list of (workout, proposal) pairs that passed validation.
    Callers must commit the session.
    """
    applied = []
    for proposal in proposals:
        workout = workouts.get(proposal.workout_id)
        if workout is None:
            continue
        valid, reason = validate_proposal(proposal, workout)
        if not valid:
            continue
        if proposal.new_workout_type is not None:
            workout.workout_type = proposal.new_workout_type
        if proposal.new_distance_m is not None:
            workout.target_distance_m = proposal.new_distance_m
        if proposal.new_duration_s is not None:
            workout.target_duration_s = proposal.new_duration_s
        if proposal.rationale:
            workout.rationale = proposal.rationale
        applied.append((workout, proposal))
    return applied
