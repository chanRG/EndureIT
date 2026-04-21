"""
Nutrition models: diet plans parsed from PDF, meals, variations, reminders, push subscriptions.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.training_plan import PlannedWorkout


class NutritionPlanStatus(str, enum.Enum):
    PARSING = "parsing"
    ACTIVE = "active"
    ARCHIVED = "archived"
    FAILED = "failed"


class MealSlot(str, enum.Enum):
    BREAKFAST = "breakfast"
    SNACK_AM = "snack_am"
    LUNCH = "lunch"
    SNACK_PM = "snack_pm"
    DINNER = "dinner"
    PRE_WORKOUT = "pre_workout"
    DURING_WORKOUT = "during_workout"
    POST_WORKOUT = "post_workout"


class ReminderKind(str, enum.Enum):
    MEAL = "meal"
    PRE_WORKOUT_FUEL = "pre_workout_fuel"
    IN_WORKOUT_GEL = "in_workout_gel"
    POST_WORKOUT_RECOVERY = "post_workout_recovery"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"
    ACTED = "acted"


class VariationSource(str, enum.Enum):
    AI = "ai"
    USER = "user"
    LIBRARY = "library"


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    source_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_json: Mapped[Optional[dict]] = mapped_column(nullable=True)
    status: Mapped[NutritionPlanStatus] = mapped_column(
        String(20), nullable=False, default=NutritionPlanStatus.PARSING
    )
    daily_calories_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_protein_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_carbs_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    daily_fat_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="nutrition_plans")
    meals: Mapped[list["NutritionPlanMeal"]] = relationship(
        "NutritionPlanMeal", back_populates="plan", cascade="all, delete-orphan"
    )


class NutritionPlanMeal(Base):
    __tablename__ = "nutrition_plan_meals"

    nutrition_plan_id: Mapped[int] = mapped_column(
        ForeignKey("nutrition_plans.id"), nullable=False, index=True
    )
    meal_slot: Mapped[MealSlot] = mapped_column(String(20), nullable=False)
    default_time_local: Mapped[Optional[str]] = mapped_column(
        String(5), nullable=True
    )  # HH:MM
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ingredients: Mapped[Optional[list]] = mapped_column(nullable=True)
    ordering: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    plan: Mapped["NutritionPlan"] = relationship(
        "NutritionPlan", back_populates="meals"
    )
    variations: Mapped[list["MealVariation"]] = relationship(
        "MealVariation", back_populates="meal", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["NutritionReminder"]] = relationship(
        "NutritionReminder", back_populates="meal"
    )


class MealVariation(Base):
    __tablename__ = "meal_variations"

    meal_id: Mapped[int] = mapped_column(
        ForeignKey("nutrition_plan_meals.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ingredients: Mapped[Optional[list]] = mapped_column(nullable=True)
    calories: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    protein_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fat_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    macro_drift: Mapped[Optional[dict]] = mapped_column(nullable=True)
    generated_by: Mapped[VariationSource] = mapped_column(
        String(10), nullable=False, default=VariationSource.AI
    )
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    meal: Mapped["NutritionPlanMeal"] = relationship(
        "NutritionPlanMeal", back_populates="variations"
    )


class NutritionReminder(Base):
    __tablename__ = "nutrition_reminders"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    meal_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("nutrition_plan_meals.id"), nullable=True
    )
    planned_workout_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("planned_workouts.id"), nullable=True
    )
    scheduled_at: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # ISO datetime string
    kind: Mapped[ReminderKind] = mapped_column(String(30), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(nullable=True)
    status: Mapped[ReminderStatus] = mapped_column(
        String(20), nullable=False, default=ReminderStatus.PENDING
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    meal: Mapped[Optional["NutritionPlanMeal"]] = relationship(
        "NutritionPlanMeal", back_populates="reminders"
    )


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    last_success_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship("User", back_populates="push_subscriptions")
