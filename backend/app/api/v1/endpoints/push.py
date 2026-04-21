"""
Push subscription endpoints.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api import deps
from app.core.settings import settings
from app.db.database import get_db
from app.models.nutrition import PushSubscription
from app.models.user import User
from app.services.push_service import build_push_payload, send_push, vapid_ready

router = APIRouter()


class PushKeys(BaseModel):
    model_config = ConfigDict(extra="forbid")

    p256dh: str
    auth: str


class SavePushSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: str
    keys: PushKeys
    user_agent: Optional[str] = None
    platform: Optional[str] = None


class DeletePushSubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    endpoint: Optional[str] = None


@router.get("/vapid-public-key")
def get_vapid_public_key() -> Any:
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(
            status_code=503, detail="Push notifications are not configured"
        )
    return {"public_key": settings.VAPID_PUBLIC_KEY, "configured": vapid_ready()}


@router.get("/subscriptions")
def get_push_subscriptions(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    subscriptions = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == current_user.id)
        .order_by(PushSubscription.created_at.desc())
        .all()
    )
    return {
        "configured": vapid_ready(),
        "has_active_subscription": any(sub.is_active for sub in subscriptions),
        "subscriptions": [
            {
                "id": sub.id,
                "platform": sub.platform,
                "user_agent": sub.user_agent,
                "is_active": sub.is_active,
                "last_success_at": sub.last_success_at,
                "error_count": sub.error_count,
                "created_at": sub.created_at.isoformat(),
            }
            for sub in subscriptions
        ],
    }


@router.post("/subscriptions")
def save_push_subscription(
    body: SavePushSubscriptionRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    subscription = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == body.endpoint)
        .first()
    )
    if subscription is None:
        subscription = PushSubscription(
            user_id=current_user.id,
            endpoint=body.endpoint,
            p256dh=body.keys.p256dh,
            auth=body.keys.auth,
            user_agent=body.user_agent,
            platform=body.platform,
            is_active=True,
        )
        db.add(subscription)
    else:
        if subscription.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Subscription belongs to another user"
            )
        subscription.p256dh = body.keys.p256dh
        subscription.auth = body.keys.auth
        subscription.user_agent = body.user_agent
        subscription.platform = body.platform
        subscription.is_active = True

    db.commit()
    db.refresh(subscription)
    return {
        "id": subscription.id,
        "is_active": subscription.is_active,
        "platform": subscription.platform,
    }


@router.delete("/subscriptions")
def delete_push_subscription(
    body: DeletePushSubscriptionRequest = Body(default=DeletePushSubscriptionRequest()),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    query = db.query(PushSubscription).filter(
        PushSubscription.user_id == current_user.id
    )
    if body.endpoint:
        query = query.filter(PushSubscription.endpoint == body.endpoint)

    subscriptions = query.all()
    if not subscriptions:
        return {"deleted": 0}

    for subscription in subscriptions:
        subscription.is_active = False

    db.commit()
    return {"deleted": len(subscriptions)}


@router.post("/test")
def test_push_notification(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Dev-only: fire a test push to all active subscriptions for the current user.
    Useful for verifying end-to-end delivery without waiting for a real reminder.
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")

    if not vapid_ready():
        raise HTTPException(status_code=503, detail="VAPID keys are not configured")

    subscriptions = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.user_id == current_user.id,
            PushSubscription.is_active.is_(True),
        )
        .all()
    )
    if not subscriptions:
        raise HTTPException(
            status_code=404, detail="No active push subscriptions found"
        )

    test_payload = {
        "title": "EndureIT test notification",
        "body": "Push delivery is working correctly.",
        "tag": "push-test",
        "url": "/settings/notifications",
        "icon": "/favicon.ico",
        "badge": "/favicon.ico",
        "data": {"url": "/settings/notifications"},
    }

    results = []
    for subscription in subscriptions:
        result = send_push(subscription, test_payload)
        results.append(
            {
                "subscription_id": subscription.id,
                "platform": subscription.platform,
                "ok": result.get("ok"),
                "reason": result.get("reason"),
            }
        )

    db.commit()
    return {"results": results}
