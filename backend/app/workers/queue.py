"""
arq worker settings and job registry.
All background jobs are imported here so arq can discover them.
"""
from arq.connections import RedisSettings

from app.core.settings import settings


async def startup(ctx: dict) -> None:
    """Initialize shared resources for the worker pool."""
    from app.db.database import SessionLocal

    ctx["db_factory"] = SessionLocal


async def shutdown(ctx: dict) -> None:
    pass


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(
        settings.REDIS_URL or "redis://localhost:6379"
    )
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 300  # 5 minutes max per job

    # Job functions discovered by arq (imported at class parse time)
    functions = []  # populated below via late import to avoid circular deps

    @classmethod
    def register(cls) -> None:
        from app.workers.match_strava import match_planned_workout
        from app.workers.parse_nutrition_pdf import parse_nutrition_pdf
        from app.workers.deliver_push import deliver_due_reminders
        from app.workers.schedule_reminders import schedule_daily_reminders
        from app.workers.weekly_ai_review import ai_weekly_review

        cls.functions = [
            match_planned_workout,
            parse_nutrition_pdf,
            deliver_due_reminders,
            schedule_daily_reminders,
            ai_weekly_review,
        ]


WorkerSettings.register()
