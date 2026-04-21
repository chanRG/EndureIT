"""
PDF nutrition plan parser.

Pipeline:
1. extract_pdf_text()  — pdfplumber → raw text + tables
2. parse_nutrition_pdf() — Claude sonnet structured extraction → ParsedNutritionPlan
3. persist_parsed_plan() — create NutritionPlanMeal rows, archive old active plan

Failures: one correction prompt; still fails → status='failed'.
Claude is never called on the request path — always via arq worker.
"""

from __future__ import annotations

import json
from typing import Optional

import pdfplumber
from pydantic import BaseModel, ValidationError

from app.core.logging import get_logger
from app.services.claude_client import claude, default_model, make_cached_block

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Pydantic schema for Claude's structured output
# ---------------------------------------------------------------------------

_MEAL_SLOTS = [
    "breakfast",
    "snack_am",
    "lunch",
    "snack_pm",
    "dinner",
    "pre_workout",
    "during_workout",
    "post_workout",
]


class ParsedMeal(BaseModel):
    meal_slot: str
    default_time_local: Optional[str] = None  # HH:MM
    name: str
    description: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    ingredients: list[str] = []
    ordering: int = 0


class ParsedNutritionPlan(BaseModel):
    daily_calories_target: Optional[float] = None
    daily_protein_g: Optional[float] = None
    daily_carbs_g: Optional[float] = None
    daily_fat_g: Optional[float] = None
    notes: Optional[str] = None
    meals: list[ParsedMeal]


# ---------------------------------------------------------------------------
# System prompt (static — cached)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a dietitian nutrition plan parser. Extract structured meal data from a PDF nutrition plan.

Output valid JSON matching this exact schema:
{
  "daily_calories_target": <number or null>,
  "daily_protein_g": <number or null>,
  "daily_carbs_g": <number or null>,
  "daily_fat_g": <number or null>,
  "notes": "<any overall notes or null>",
  "meals": [
    {
      "meal_slot": "<one of: breakfast, snack_am, lunch, snack_pm, dinner, pre_workout, during_workout, post_workout>",
      "default_time_local": "<HH:MM or null>",
      "name": "<meal name>",
      "description": "<brief description or null>",
      "calories": <number or null>,
      "protein_g": <number or null>,
      "carbs_g": <number or null>,
      "fat_g": <number or null>,
      "ingredients": ["<ingredient 1>", ...],
      "ordering": <integer starting at 0>
    }
  ]
}

Rules:
- meal_slot MUST be one of the enum values listed above
- If a meal doesn't fit a slot, use the closest match
- Output ONLY the JSON object, no markdown fences or explanation
- All numeric values are floats, never strings
- ingredients is always an array of strings (can be empty)"""


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text and tables from a PDF file using pdfplumber."""
    lines: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.append(text)
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    cleaned = [str(cell).strip() if cell else "" for cell in row]
                    lines.append(" | ".join(c for c in cleaned if c))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Claude extraction
# ---------------------------------------------------------------------------


def _call_claude(raw_text: str, correction_note: str = "") -> str:
    user_content = raw_text
    if correction_note:
        user_content = (
            f"Previous extraction failed: {correction_note}\n\nPDF content:\n{raw_text}"
        )

    response = claude.messages.create(
        model=default_model(),
        max_tokens=4096,
        system=[make_cached_block(_SYSTEM_PROMPT)],
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text.strip()


def parse_nutrition_pdf(raw_text: str) -> ParsedNutritionPlan:
    """
    Call Claude to extract structured nutrition data from raw PDF text.
    Retries once with a correction prompt on validation failure.
    Raises ValueError if both attempts fail.
    """
    # First attempt
    raw_json = _call_claude(raw_text)
    try:
        data = json.loads(raw_json)
        return ParsedNutritionPlan(**data)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        logger.warning("First parse attempt failed: %s", exc)
        correction = str(exc)

    # Second attempt with correction
    raw_json2 = _call_claude(raw_text, correction_note=correction)
    try:
        data2 = json.loads(raw_json2)
        return ParsedNutritionPlan(**data2)
    except (json.JSONDecodeError, ValidationError, TypeError) as exc2:
        raise ValueError(f"Claude extraction failed after retry: {exc2}") from exc2


# ---------------------------------------------------------------------------
# DB persistence helper (called from worker after successful parse)
# ---------------------------------------------------------------------------


def persist_parsed_plan(
    db,
    nutrition_plan,
    parsed: ParsedNutritionPlan,
) -> None:
    """
    Update NutritionPlan with parsed data, create NutritionPlanMeal rows,
    archive any previous active plan for the user, set status='active'.
    """
    from app.models.nutrition import (
        NutritionPlan,
        NutritionPlanMeal,
        NutritionPlanStatus,
    )

    # Archive previous active plan
    db.query(NutritionPlan).filter(
        NutritionPlan.user_id == nutrition_plan.user_id,
        NutritionPlan.status == NutritionPlanStatus.ACTIVE,
        NutritionPlan.id != nutrition_plan.id,
    ).update({"status": NutritionPlanStatus.ARCHIVED})

    # Update plan fields
    nutrition_plan.daily_calories_target = parsed.daily_calories_target
    nutrition_plan.daily_protein_g = parsed.daily_protein_g
    nutrition_plan.daily_carbs_g = parsed.daily_carbs_g
    nutrition_plan.daily_fat_g = parsed.daily_fat_g
    nutrition_plan.notes = parsed.notes
    nutrition_plan.parsed_json = parsed.model_dump()
    nutrition_plan.status = NutritionPlanStatus.ACTIVE

    # Create meal rows
    for meal in parsed.meals:
        row = NutritionPlanMeal(
            nutrition_plan_id=nutrition_plan.id,
            meal_slot=meal.meal_slot,
            default_time_local=meal.default_time_local,
            name=meal.name,
            description=meal.description,
            calories=meal.calories,
            protein_g=meal.protein_g,
            carbs_g=meal.carbs_g,
            fat_g=meal.fat_g,
            ingredients=meal.ingredients,
            ordering=meal.ordering,
        )
        db.add(row)

    db.flush()
    logger.info(
        "Persisted nutrition plan %d with %d meals",
        nutrition_plan.id,
        len(parsed.meals),
    )
