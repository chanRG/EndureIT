"""
Claude-powered weekly plan adjuster.

Uses Claude tool-use to suggest bounded adjustments for the upcoming training
week based on recent performance. All proposals are validated against hard
safety bounds before any DB write.

Deterministic fallback: if Claude is unavailable or returns an error, the
function returns an empty WeeklyReviewResult and the template week runs
unmodified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from app.models.training_plan import PlannedWorkout, WorkoutType
from app.services.claude_client import claude, default_model, make_cached_block

if TYPE_CHECKING:
    from app.models.training_plan import TrainingPace, TrainingPlan

# ---------------------------------------------------------------------------
# Safety constants
# ---------------------------------------------------------------------------

_MAX_VOLUME_INCREASE = 0.10  # +10 %
_MAX_VOLUME_DECREASE = 0.30  # −30 %
_HARD_TYPES = {WorkoutType.TEMPO, WorkoutType.INTERVALS, WorkoutType.RACE}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class AdjustmentProposal:
    workout_id: int
    new_workout_type: Optional[WorkoutType] = None
    new_distance_m: Optional[float] = None
    new_duration_s: Optional[int] = None
    rationale: str = ""


@dataclass
class WeeklyReviewResult:
    proposals: list[AdjustmentProposal] = field(default_factory=list)
    # None = no flag raised; str = reason text from Claude
    injury_flag: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _is_recovery_week(week_number: int) -> bool:
    """Every 4th week is a stepback/recovery week (1-indexed)."""
    return week_number > 0 and week_number % 4 == 0


def _check_hard_spacing(
    target: PlannedWorkout,
    all_workouts: list[PlannedWorkout],
    new_type: WorkoutType,
) -> Optional[str]:
    """
    Return an error string if placing a hard session on target.scheduled_date
    would be within 72 h (3 days) of another hard session.  None = OK.
    """
    if new_type not in _HARD_TYPES:
        return None
    for w in all_workouts:
        if w.id == target.id:
            continue
        wtype = w.workout_type
        if isinstance(wtype, str):
            try:
                wtype = WorkoutType(wtype)
            except ValueError:
                continue
        if wtype not in _HARD_TYPES:
            continue
        delta = abs((w.scheduled_date - target.scheduled_date).days)
        if delta < 3:
            return (
                f"Hard session on {w.scheduled_date} is only {delta}d from "
                f"{target.scheduled_date} (72 h minimum required)"
            )
    return None


def validate_proposal(
    proposal: AdjustmentProposal,
    original: PlannedWorkout,
    next_week: list[PlannedWorkout],
) -> tuple[bool, str]:
    """
    Return (is_valid, rejection_reason).
    Enforces: recovery-week hard-session ban, 72 h hard spacing, volume bounds.
    """
    if proposal.new_workout_type is not None:
        new_type = proposal.new_workout_type
        if isinstance(new_type, str):
            try:
                new_type = WorkoutType(new_type)
            except ValueError:
                return False, f"Unknown workout type: {new_type!r}"
        if new_type in _HARD_TYPES and _is_recovery_week(original.week_number):
            return (
                False,
                f"Cannot introduce {new_type} in recovery week {original.week_number}",
            )
        spacing_err = _check_hard_spacing(original, next_week, new_type)
        if spacing_err:
            return False, spacing_err

    if proposal.new_distance_m is not None and original.target_distance_m:
        ratio = proposal.new_distance_m / original.target_distance_m
        if ratio > 1 + _MAX_VOLUME_INCREASE:
            return False, f"Volume increase {ratio:.0%} exceeds +10 % cap"
        if ratio < 1 - _MAX_VOLUME_DECREASE:
            return False, f"Volume decrease {ratio:.0%} exceeds −30 % floor"

    return True, ""


def apply_adjustments(
    proposals: list[AdjustmentProposal],
    workouts: dict[int, PlannedWorkout],
    next_week: Optional[list[PlannedWorkout]] = None,
) -> list[tuple[PlannedWorkout, AdjustmentProposal]]:
    """
    Apply validated proposals to in-memory workout objects.
    Returns (workout, proposal) pairs that passed validation.
    Callers must commit the session.
    """
    context = next_week if next_week is not None else list(workouts.values())
    applied = []
    for proposal in proposals:
        workout = workouts.get(proposal.workout_id)
        if workout is None:
            continue
        valid, _ = validate_proposal(proposal, workout, context)
        if not valid:
            continue
        if proposal.new_workout_type is not None:
            workout.workout_type = proposal.new_workout_type
        if proposal.new_distance_m is not None:
            # Scale duration proportionally when both are set
            if workout.target_duration_s and workout.target_distance_m:
                scale = proposal.new_distance_m / workout.target_distance_m
                workout.target_duration_s = int(workout.target_duration_s * scale)
            workout.target_distance_m = proposal.new_distance_m
        if proposal.new_duration_s is not None:
            workout.target_duration_s = proposal.new_duration_s
        if proposal.rationale:
            workout.rationale = proposal.rationale
        applied.append((workout, proposal))
    return applied


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

_ADJUSTER_SYSTEM_PROMPT = """\
You are an AI running coach assistant for EndureIT.
You review weekly training loads and suggest conservative adjustments for the upcoming week.

HARD RULES — never violate these:
1. Maximum volume INCREASE per workout: +10 %. Maximum volume DECREASE: −30 %.
2. Hard sessions (tempo, intervals, race) must be separated by at least 72 hours.
3. During a recovery/stepback week (every 4th week) you may NOT introduce new hard sessions.
4. Never give medical advice. Use flag_injury_risk only for clear overtraining signals.
5. At most 3 proposals per review. If no changes are needed, call no tools.
6. Only propose changes to PLANNED (upcoming) workouts — never to completed ones.

WHEN TO PROPOSE CHANGES:
- Last-week completion < 60 % of planned volume → reduce next week by ~20 %
- Consecutive hard sessions within 48 h → swap one to easy/recovery
- Three or more missed workouts in a row → use flag_injury_risk
- Otherwise → conservative: prefer no change over a change

Always include a concise rationale (≤ 120 chars) in every tool call.\
"""

_TOOLS: list[dict] = [
    {
        "name": "propose_workout_swap",
        "description": (
            "Change the workout type of a single planned workout. "
            "Use to downgrade a hard session to easy/recovery, or upgrade rest to cross-training."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "workout_id": {
                    "type": "integer",
                    "description": "ID of the PlannedWorkout to modify.",
                },
                "new_type": {
                    "type": "string",
                    "enum": [
                        "easy",
                        "long",
                        "tempo",
                        "intervals",
                        "recovery",
                        "cross",
                        "rest",
                    ],
                },
                "rationale": {
                    "type": "string",
                    "description": "Brief coaching rationale (max 120 chars).",
                },
            },
            "required": ["workout_id", "new_type", "rationale"],
        },
    },
    {
        "name": "propose_volume_change",
        "description": (
            "Scale the distance of a planned workout. "
            "distance_factor is the multiplier: 0.8 = −20 %, 1.1 = +10 %. "
            "Must be between 0.70 and 1.10."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "workout_id": {
                    "type": "integer",
                    "description": "ID of the PlannedWorkout to modify.",
                },
                "distance_factor": {
                    "type": "number",
                    "description": "Multiply current distance by this value (0.70–1.10).",
                },
                "rationale": {
                    "type": "string",
                    "description": "Brief coaching rationale (max 120 chars).",
                },
            },
            "required": ["workout_id", "distance_factor", "rationale"],
        },
    },
    {
        "name": "flag_injury_risk",
        "description": (
            "Flag the training plan as having elevated injury risk. "
            "This auto-pauses the plan and replaces the next 7 days with easy recovery runs. "
            "Only use for clear overtraining or injury signals."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Brief non-clinical reason for the flag (max 200 chars).",
                },
            },
            "required": ["reason"],
        },
    },
]


def _fmt_workouts(workouts: list[PlannedWorkout], label: str) -> str:
    lines = [f"### {label}"]
    if not workouts:
        lines.append("(none)")
        return "\n".join(lines)
    for w in workouts:
        dist = f"{w.target_distance_m / 1000:.1f} km" if w.target_distance_m else "—"
        dur = f"{w.target_duration_s // 60} min" if w.target_duration_s else "—"
        effort = f"RPE {w.perceived_effort}/10" if w.perceived_effort else ""
        status = w.status.value if hasattr(w.status, "value") else str(w.status)
        wtype = (
            w.workout_type.value
            if hasattr(w.workout_type, "value")
            else str(w.workout_type)
        )
        lines.append(
            f"- ID {w.id} | {w.scheduled_date} | {wtype} | {dist} / {dur} | {status} {effort}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def suggest_week_adjustments(
    plan: "TrainingPlan",
    next_week: list[PlannedWorkout],
    recent_completed: list[PlannedWorkout],
    paces: "Optional[TrainingPace]",
) -> WeeklyReviewResult:
    """
    Call Claude to review the upcoming week and return bounded proposals.

    On any Claude error or timeout the function returns an empty
    WeeklyReviewResult so the template week runs unmodified (deterministic
    fallback).
    """
    if not next_week:
        return WeeklyReviewResult()

    # Build dynamic context -----------------------------------------------
    completed_vol_km = sum((w.target_distance_m or 0) for w in recent_completed) / 1000

    phase = (
        plan.current_phase.value
        if plan.current_phase and hasattr(plan.current_phase, "value")
        else str(plan.current_phase or "unknown")
    )
    vdot_str = f"{plan.vdot:.1f}" if plan.vdot else "unknown"

    pace_line = ""
    if paces:
        pace_line = (
            f"Training paces (min/km): easy={paces.easy_pace:.2f}, "
            f"threshold={paces.threshold_pace:.2f}, "
            f"interval={paces.interval_pace:.2f}"
        )

    current_week = next_week[0].week_number if next_week else "?"
    recovery_note = (
        " ⚠️ THIS IS A RECOVERY/STEPBACK WEEK — no new hard sessions allowed"
        if isinstance(current_week, int) and _is_recovery_week(current_week)
        else ""
    )

    upcoming_text = _fmt_workouts(
        next_week, "Upcoming week (PLANNED — these are the only modifiable workouts)"
    )
    recent_text = _fmt_workouts(recent_completed, "Last 7 days (completed workouts)")

    user_message = (
        f"Plan: goal={plan.goal_distance_km} km | phase={phase} | "
        f"VDOT={vdot_str} | week {current_week}/{plan.total_weeks}{recovery_note}\n"
        f"{pace_line}\n\n"
        f"Completed volume last 7 days: {completed_vol_km:.1f} km "
        f"across {len(recent_completed)} sessions.\n\n"
        f"{recent_text}\n\n"
        f"{upcoming_text}\n\n"
        "Review the upcoming week and propose adjustments using the tools. "
        "If no changes are needed, do not call any tools."
    )

    # Call Claude -------------------------------------------------------------
    try:
        response = claude.messages.create(
            model=default_model(),
            max_tokens=1024,
            system=[make_cached_block(_ADJUSTER_SYSTEM_PROMPT)],
            tools=_TOOLS,
            tool_choice={"type": "auto"},
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception:
        # Deterministic fallback — template week runs unmodified
        return WeeklyReviewResult()

    usage = response.usage
    result = WeeklyReviewResult(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
    )

    # Map workouts by id for factor expansion
    workout_by_id = {w.id: w for w in next_week}

    for block in response.content:
        if block.type != "tool_use":
            continue
        inp = block.input

        if block.name == "flag_injury_risk":
            result.injury_flag = str(
                inp.get("reason", "AI flagged elevated injury risk")
            )
            # Injury flag takes precedence — discard any other proposals already collected
            result.proposals.clear()
            break

        elif block.name == "propose_workout_swap":
            try:
                result.proposals.append(
                    AdjustmentProposal(
                        workout_id=int(inp["workout_id"]),
                        new_workout_type=WorkoutType(inp["new_type"]),
                        rationale=str(inp.get("rationale", "")),
                    )
                )
            except (KeyError, ValueError):
                pass

        elif block.name == "propose_volume_change":
            try:
                workout_id = int(inp["workout_id"])
                factor = float(inp["distance_factor"])
                matching = workout_by_id.get(workout_id)
                if matching and matching.target_distance_m:
                    result.proposals.append(
                        AdjustmentProposal(
                            workout_id=workout_id,
                            new_distance_m=matching.target_distance_m * factor,
                            rationale=str(inp.get("rationale", "")),
                        )
                    )
            except (KeyError, ValueError):
                pass

    return result
