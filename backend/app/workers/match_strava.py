"""
Matches a newly synced Strava activity to a PlannedWorkout.
Enqueued by StravaSyncService after a new activity is saved.
Full implementation in feat/training-plans-phase1.
"""


async def match_planned_workout(ctx: dict, strava_activity_id: int, user_id: int) -> dict:
    # TODO: implement in feat/training-plans-phase1
    return {"status": "not_implemented"}
