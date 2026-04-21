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
        from app.workers.generate_meal_variations import generate_meal_variations
        from app.workers.deliver_push import deliver_due_reminders
        from app.workers.schedule_reminders import schedule_daily_reminders
        from app.workers.weekly_ai_review import ai_weekly_review

        cls.functions = [
            match_planned_workout,
            parse_nutrition_pdf,
            generate_meal_variations,
            deliver_due_reminders,
            schedule_daily_reminders,
            ai_weekly_review,
        ]


WorkerSettings.register()


async def enqueue(job_name: str, **kwargs) -> None:
    """Enqueue a background job by name. Silently no-ops if Redis is unavailable."""
    try:
        from arq import create_pool

        redis = await create_pool(WorkerSettings.redis_settings)
        await redis.enqueue_job(job_name, **kwargs)
        await redis.close()
    except Exception as exc:
        from app.core.logging import get_logger

        get_logger(__name__).warning("Failed to enqueue %s: %s", job_name, exc)
