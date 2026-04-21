"""
Nutrition endpoints: PDF upload, plan query, meal variations, reminders.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Optional

import magic
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.logging import get_logger
from app.core.settings import settings
from app.db.database import get_db
from app.models.nutrition import (
    MealVariation,
    NutritionPlan,
    NutritionPlanMeal,
    NutritionPlanStatus,
    NutritionReminder,
    ReminderStatus,
    VariationSource,
)
from app.models.user import User

logger = get_logger(__name__)
router = APIRouter()

_MAX_PDF_BYTES = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024
_UPLOAD_DIR = Path(getattr(settings, "UPLOAD_DIR", "uploads"))


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------


def _ser_plan(p: NutritionPlan) -> dict:
    return {
        "id": p.id,
        "status": p.status.value,
        "source_filename": p.source_filename,
        "daily_calories_target": p.daily_calories_target,
        "daily_protein_g": p.daily_protein_g,
        "daily_carbs_g": p.daily_carbs_g,
        "daily_fat_g": p.daily_fat_g,
        "notes": p.notes,
        "created_at": p.created_at.isoformat(),
        "meal_count": len(p.meals) if p.meals else 0,
    }


def _ser_meal(m: NutritionPlanMeal) -> dict:
    return {
        "id": m.id,
        "meal_slot": (
            m.meal_slot.value if hasattr(m.meal_slot, "value") else m.meal_slot
        ),
        "default_time_local": m.default_time_local,
        "name": m.name,
        "description": m.description,
        "calories": m.calories,
        "protein_g": m.protein_g,
        "carbs_g": m.carbs_g,
        "fat_g": m.fat_g,
        "ingredients": m.ingredients or [],
        "ordering": m.ordering,
    }


def _ser_variation(v: MealVariation) -> dict:
    return {
        "id": v.id,
        "name": v.name,
        "ingredients": v.ingredients or [],
        "calories": v.calories,
        "protein_g": v.protein_g,
        "carbs_g": v.carbs_g,
        "fat_g": v.fat_g,
        "macro_drift": v.macro_drift or {},
        "generated_by": (
            v.generated_by.value if hasattr(v.generated_by, "value") else v.generated_by
        ),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_nutrition_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Upload a dietitian PDF. Returns immediately; parsing runs in background.
    """
    raw = await file.read(_MAX_PDF_BYTES + 1)
    if len(raw) > _MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    # Validate MIME via magic bytes
    mime = magic.from_buffer(raw[:2048], mime=True)
    if mime != "application/pdf":
        raise HTTPException(status_code=415, detail="Only PDF files are accepted")

    # Save to disk
    dest_dir = _UPLOAD_DIR / "nutrition" / str(current_user.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid.uuid4()}.pdf"
    dest_path = dest_dir / file_name
    dest_path.write_bytes(raw)
    os.chmod(dest_path, 0o600)

    # Create NutritionPlan record
    plan = NutritionPlan(
        user_id=current_user.id,
        source_filename=file.filename or file_name,
        source_pdf_url=str(dest_path),
        status=NutritionPlanStatus.PARSING,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)

    # Enqueue parse job
    try:
        from app.workers.queue import enqueue

        await enqueue("parse_nutrition_pdf", nutrition_plan_id=plan.id)
    except Exception as exc:
        logger.warning("Failed to enqueue parse job for plan %d: %s", plan.id, exc)

    return {"plan_id": plan.id, "status": "parsing"}


@router.get("/plans/active")
def get_active_plan(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    plan = _active_plan_or_404(db, current_user.id)
    meals = sorted(plan.meals, key=lambda m: m.ordering)
    return {
        **_ser_plan(plan),
        "meals": [_ser_meal(m) for m in meals],
    }


@router.get("/meals/{meal_id}")
def get_meal(
    meal_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    meal = _meal_or_404(db, meal_id, current_user.id)
    return {
        **_ser_meal(meal),
        "variations": [_ser_variation(v) for v in meal.variations],
    }


@router.post("/meals/{meal_id}/variations", status_code=status.HTTP_202_ACCEPTED)
def request_variations(
    meal_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Enqueue a Claude variation generation job. Returns immediately."""
    meal = _meal_or_404(db, meal_id, current_user.id)

    try:
        import asyncio
        from app.workers.queue import enqueue

        asyncio.get_event_loop().run_until_complete(
            enqueue("generate_meal_variations", meal_id=meal.id)
        )
    except Exception as exc:
        logger.warning("Failed to enqueue variation job for meal %d: %s", meal.id, exc)

    return {"meal_id": meal.id, "status": "generating"}


@router.post("/meals/{meal_id}/variations/{variation_id}/select")
def select_variation(
    meal_id: int,
    variation_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Mark a variation as selected (copies its macros onto the parent meal)."""
    meal = _meal_or_404(db, meal_id, current_user.id)
    variation = (
        db.query(MealVariation)
        .filter(MealVariation.id == variation_id, MealVariation.meal_id == meal.id)
        .first()
    )
    if variation is None:
        raise HTTPException(status_code=404, detail="Variation not found")

    meal.name = variation.name
    meal.ingredients = variation.ingredients
    meal.calories = variation.calories
    meal.protein_g = variation.protein_g
    meal.carbs_g = variation.carbs_g
    meal.fat_g = variation.fat_g
    db.commit()
    db.refresh(meal)
    return _ser_meal(meal)


@router.get("/reminders/upcoming")
def get_upcoming_reminders(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    reminders = (
        db.query(NutritionReminder)
        .filter(
            NutritionReminder.user_id == current_user.id,
            NutritionReminder.scheduled_at >= now,
            NutritionReminder.status == ReminderStatus.PENDING,
        )
        .order_by(NutritionReminder.scheduled_at)
        .limit(20)
        .all()
    )
    return [
        {
            "id": r.id,
            "kind": r.kind.value if hasattr(r.kind, "value") else r.kind,
            "scheduled_at": r.scheduled_at,
            "status": r.status.value if hasattr(r.status, "value") else r.status,
            "payload": r.payload,
            "meal_id": r.meal_id,
            "planned_workout_id": r.planned_workout_id,
        }
        for r in reminders
    ]


@router.patch("/reminders/{reminder_id}")
def update_reminder(
    reminder_id: int,
    body: dict,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    r = (
        db.query(NutritionReminder)
        .filter(
            NutritionReminder.id == reminder_id,
            NutritionReminder.user_id == current_user.id,
        )
        .first()
    )
    if r is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    allowed = {s.value for s in ReminderStatus}
    new_status = body.get("status")
    if new_status and new_status in allowed:
        r.status = ReminderStatus(new_status)
    db.commit()
    return {"id": r.id, "status": r.status.value}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _active_plan_or_404(db: Session, user_id: int) -> NutritionPlan:
    plan = (
        db.query(NutritionPlan)
        .filter(
            NutritionPlan.user_id == user_id,
            NutritionPlan.status == NutritionPlanStatus.ACTIVE,
        )
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="No active nutrition plan")
    return plan


def _meal_or_404(db: Session, meal_id: int, user_id: int) -> NutritionPlanMeal:
    meal = (
        db.query(NutritionPlanMeal)
        .join(NutritionPlan)
        .filter(
            NutritionPlanMeal.id == meal_id,
            NutritionPlan.user_id == user_id,
        )
        .first()
    )
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return meal
