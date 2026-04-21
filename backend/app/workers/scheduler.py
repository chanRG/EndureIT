"""
Cron scheduler: enqueues periodic jobs into the arq queue.
Run as a separate service: python -m app.workers.scheduler
"""

import asyncio
import logging
from datetime import datetime, timezone

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import distinct

from app.core.settings import settings
from app.db.database import SessionLocal
from app.models.nutrition import NutritionPlan, NutritionPlanStatus
from app.models.training_plan import PlanStatus, TrainingPlan

logger = logging.getLogger(__name__)

REDIS = RedisSettings.from_dsn(settings.REDIS_URL or "redis://localhost:6379")


async def run_scheduler() -> None:
    pool = await create_pool(REDIS)
    logger.info("Scheduler started")

    while True:
        now = datetime.now(timezone.utc)

        # Daily 04:00 UTC — schedule reminders for all users with active plans
        if now.hour == 4 and now.minute == 0:
            db = SessionLocal()
            try:
                user_ids = [
                    row[0]
                    for row in db.query(distinct(NutritionPlan.user_id))
                    .filter(NutritionPlan.status == NutritionPlanStatus.ACTIVE.value)
                    .all()
                ]
            finally:
                db.close()

            logger.info(
                "Enqueuing daily reminder scheduling for %d users", len(user_ids)
            )
            for user_id in user_ids:
                await pool.enqueue_job("schedule_daily_reminders", user_id=user_id)

        # Sunday 21:00 UTC — weekly AI review for all active training plans
        if now.weekday() == 6 and now.hour == 21 and now.minute == 0:
            db = SessionLocal()
            try:
                plan_ids = [
                    row[0]
                    for row in db.query(TrainingPlan.id)
                    .filter(TrainingPlan.status == PlanStatus.ACTIVE.value)
                    .all()
                ]
            finally:
                db.close()

            logger.info("Enqueuing weekly AI review for %d plans", len(plan_ids))
            for plan_id in plan_ids:
                await pool.enqueue_job(
                    "ai_weekly_review",
                    plan_id=plan_id,
                    _job_id=f"ai_weekly_review_{plan_id}",
                )

        # Deliver due push reminders every 60 s.
        # _job_id is fixed so arq deduplicates concurrent enqueues —
        # a new job is only queued once the previous one finishes.
        await pool.enqueue_job("deliver_due_reminders", _job_id="deliver_due_reminders")

        await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scheduler())
