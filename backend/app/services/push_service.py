"""
Push and fallback delivery helpers for reminder notifications.
"""

from __future__ import annotations

import json
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

from pywebpush import WebPushException, webpush

from app.core.logging import get_logger
from app.core.settings import settings
from app.models.nutrition import NutritionReminder, PushSubscription, ReminderKind
from app.models.user import User

logger = get_logger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def vapid_ready() -> bool:
    return bool(
        settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_SUBJECT
    )


def build_push_payload(reminder: NutritionReminder) -> dict[str, Any]:
    kind = reminder.kind.value if hasattr(reminder.kind, "value") else str(reminder.kind)
    payload = reminder.payload or {}
    title = payload.get("title")
    body = payload.get("body")

    if not title or not body:
        defaults = {
            ReminderKind.MEAL.value: (
                "Meal reminder",
                "It is time for your planned meal.",
            ),
            ReminderKind.PRE_WORKOUT_FUEL.value: (
                "Pre-workout fuel",
                "Fuel up before your session starts.",
            ),
            ReminderKind.IN_WORKOUT_GEL.value: (
                "Fuel mid-run",
                "Take in carbs to stay ahead of the effort.",
            ),
            ReminderKind.POST_WORKOUT_RECOVERY.value: (
                "Recovery window",
                "Refuel and recover while the session is still fresh.",
            ),
        }
        title, body = defaults.get(kind, ("Reminder", "You have an upcoming reminder."))

    return {
        "title": title,
        "body": body,
        "tag": f"reminder-{reminder.id}",
        "url": payload.get("url", "/settings/notifications"),
        "kind": kind,
        "icon": "/favicon.ico",
        "badge": "/favicon.ico",
        "data": {
            "reminder_id": reminder.id,
            "planned_workout_id": reminder.planned_workout_id,
            "meal_id": reminder.meal_id,
            "url": payload.get("url", "/settings/notifications"),
        },
    }


def send_push(
    subscription: PushSubscription,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Attempt to deliver a web push payload.
    """
    if not vapid_ready():
        return {"ok": False, "reason": "vapid_not_configured"}

    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh,
                    "auth": subscription.auth,
                },
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
            ttl=300,
        )
        return {"ok": True}
    except WebPushException as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        return {
            "ok": False,
            "reason": str(exc),
            "status_code": status_code,
            "expired": status_code in {404, 410},
        }
    except Exception as exc:
        logger.warning("Push delivery failed: %s", exc)
        return {"ok": False, "reason": str(exc)}


def send_email_fallback(user: User, payload: dict[str, Any]) -> bool:
    """
    Deliver a simple email fallback for critical reminders.
    """
    if not (
        settings.SMTP_HOST
        and settings.SMTP_PORT
        and settings.EMAILS_FROM_EMAIL
        and user.email
    ):
        logger.info("Skipping email fallback for user %s: SMTP not configured", user.id)
        return False

    message = EmailMessage()
    message["Subject"] = payload["title"]
    sender_name = settings.EMAILS_FROM_NAME or settings.PROJECT_NAME
    message["From"] = f"{sender_name} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = user.email
    message.set_content(f"{payload['body']}\n\nOpen: {payload['data'].get('url', '/settings/notifications')}")

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception as exc:
        logger.warning("Email fallback failed for user %s: %s", user.id, exc)
        return False


def mark_subscription_success(subscription: PushSubscription) -> None:
    subscription.last_success_at = _iso_now()
    subscription.error_count = 0
    subscription.is_active = True


def mark_subscription_failure(subscription: PushSubscription, deactivate: bool) -> None:
    subscription.error_count += 1
    if deactivate:
        subscription.is_active = False
