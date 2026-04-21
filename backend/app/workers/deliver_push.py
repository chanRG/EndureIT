"""
Sends pending web push NutritionReminders via pywebpush.
Runs every 60 s in the worker pool.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.nutrition import PushSubscription, NutritionReminder, ReminderKind, ReminderStatus
from app.models.user import User
from app.services.push_service import (
    build_push_payload,
    mark_subscription_failure,
    mark_subscription_success,
    send_email_fallback,
    send_push,
)

logger = get_logger(__name__)


async def deliver_due_reminders(ctx: dict) -> dict:
    db = SessionLocal()
    try:
        now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        reminders = (
            db.query(NutritionReminder)
            .filter(
                NutritionReminder.status == ReminderStatus.PENDING.value,
                NutritionReminder.scheduled_at <= now_iso,
            )
            .order_by(NutritionReminder.scheduled_at.asc())
            .limit(100)
            .all()
        )

        sent = 0
        failed = 0

        for reminder in reminders:
            payload = build_push_payload(reminder)
            subscriptions = (
                db.query(PushSubscription)
                .filter(
                    PushSubscription.user_id == reminder.user_id,
                    PushSubscription.is_active.is_(True),
                )
                .all()
            )

            delivered = False
            for subscription in subscriptions:
                result = send_push(subscription, payload)
                if result.get("ok"):
                    mark_subscription_success(subscription)
                    delivered = True
                else:
                    mark_subscription_failure(subscription, deactivate=result.get("expired", False))

            reminder.attempts += 1

            if delivered:
                reminder.status = ReminderStatus.SENT.value
                sent += 1
                continue

            user = db.query(User).filter(User.id == reminder.user_id).first()
            critical_kinds = {
                ReminderKind.PRE_WORKOUT_FUEL.value,
                ReminderKind.IN_WORKOUT_GEL.value,
                ReminderKind.POST_WORKOUT_RECOVERY.value,
            }
            if user and reminder.kind in critical_kinds and send_email_fallback(user, payload):
                reminder.status = ReminderStatus.SENT.value
                sent += 1
            else:
                reminder.status = ReminderStatus.FAILED.value
                failed += 1

        db.commit()
        return {"status": "processed", "sent": sent, "failed": failed, "checked": len(reminders)}
    except Exception:
        db.rollback()
        logger.exception("deliver_due_reminders failed")
        raise
    finally:
        db.close()
