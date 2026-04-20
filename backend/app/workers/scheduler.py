"""
Cron scheduler: enqueues periodic jobs into the arq queue.
Run as a separate service: python -m app.workers.scheduler
"""
import asyncio
import logging
from datetime import datetime, timezone

from arq import create_pool
from arq.connections import RedisSettings

from app.core.settings import settings

logger = logging.getLogger(__name__)

REDIS = RedisSettings.from_dsn(settings.REDIS_URL or "redis://localhost:6379")


async def run_scheduler() -> None:
    pool = await create_pool(REDIS)
    logger.info("Scheduler started")

    while True:
        now = datetime.now(timezone.utc)

        # Daily 04:00 UTC — schedule reminders for all users with active plans
        # TODO: implement user enumeration in feat/web-push-reminders
        if now.hour == 4 and now.minute == 0:
            logger.info("Enqueuing daily reminder scheduling")

        # Sunday 21:00 UTC — weekly AI review for all active plans
        # TODO: implement plan enumeration in feat/ai-weekly-review
        if now.weekday() == 6 and now.hour == 21 and now.minute == 0:
            logger.info("Enqueuing weekly AI review")

        # Deliver due push reminders every 60 s
        await pool.enqueue_job("deliver_due_reminders")

        await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scheduler())
