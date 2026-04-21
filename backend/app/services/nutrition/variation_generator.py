"""
Claude-powered meal variation generator.

Generates macro-preserving swap options for a given meal.
Uses tool use to enforce the output schema, with prompt caching on the static system prompt.
Never called on the request path — always via arq job (returns job_id immediately).
"""

from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger
from app.services.claude_client import claude, default_model, make_cached_block

logger = get_logger(__name__)

# Macro drift tolerance (fraction of original value)
_MAX_MACRO_DRIFT = 0.15  # ±15 %

_SYSTEM_PROMPT = """You are a sports dietitian generating macro-preserving meal alternatives.

Given a meal with its nutritional targets, generate 3 alternative variations.
Each variation must:
- Keep calories within ±15% of the original
- Keep protein within ±15% of the original
- Use realistic, commonly available ingredients
- Be appropriate for an athlete's diet

Use the emit_variations tool to output your response."""

_EMIT_TOOL: dict[str, Any] = {
    "name": "emit_variations",
    "description": "Emit the list of meal variations",
    "input_schema": {
        "type": "object",
        "properties": {
            "variations": {
                "type": "array",
                "minItems": 1,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "required": [
                        "name",
                        "ingredients",
                        "calories",
                        "protein_g",
                        "carbs_g",
                        "fat_g",
                    ],
                    "properties": {
                        "name": {"type": "string"},
                        "ingredients": {"type": "array", "items": {"type": "string"}},
                        "calories": {"type": "number"},
                        "protein_g": {"type": "number"},
                        "carbs_g": {"type": "number"},
                        "fat_g": {"type": "number"},
                    },
                },
            }
        },
        "required": ["variations"],
    },
}


def _compute_macro_drift(original: dict, variation: dict) -> dict:
    drift = {}
    for key in ("calories", "protein_g", "carbs_g", "fat_g"):
        orig_val = original.get(key)
        new_val = variation.get(key)
        if orig_val and orig_val > 0 and new_val is not None:
            drift[key] = round((new_val - orig_val) / orig_val, 3)
    return drift


def _validate_variation(original: dict, variation: dict) -> bool:
    """Reject variations with excessive calorie or protein drift."""
    for key in ("calories", "protein_g"):
        orig = original.get(key)
        new = variation.get(key)
        if orig and orig > 0 and new is not None:
            if abs(new - orig) / orig > _MAX_MACRO_DRIFT:
                return False
    return True


def generate_variations(
    meal_name: str,
    meal_slot: str,
    calories: float | None,
    protein_g: float | None,
    carbs_g: float | None,
    fat_g: float | None,
    ingredients: list[str],
    n: int = 3,
) -> list[dict]:
    """
    Generate n macro-preserving variations for a meal.
    Returns list of dicts matching MealVariation fields.
    Raises ValueError on Claude failure.
    """
    original = {
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
    }

    prompt = (
        f"Meal: {meal_name} ({meal_slot})\n"
        f"Calories: {calories} kcal | Protein: {protein_g}g | "
        f"Carbs: {carbs_g}g | Fat: {fat_g}g\n"
        f"Ingredients: {', '.join(ingredients) if ingredients else 'not specified'}\n\n"
        f"Generate {n} variations preserving the macros within ±15%."
    )

    response = claude.messages.create(
        model=default_model(),
        max_tokens=2048,
        system=[make_cached_block(_SYSTEM_PROMPT)],
        tools=[_EMIT_TOOL],
        tool_choice={"type": "tool", "name": "emit_variations"},
        messages=[{"role": "user", "content": prompt}],
    )

    tool_use = next(
        (block for block in response.content if block.type == "tool_use"),
        None,
    )
    if tool_use is None:
        raise ValueError("Claude did not call emit_variations tool")

    raw_variations: list[dict] = tool_use.input.get("variations", [])
    if not raw_variations:
        raise ValueError("emit_variations returned empty list")

    result = []
    for v in raw_variations:
        if not _validate_variation(original, v):
            logger.warning(
                "Variation '%s' exceeds macro drift threshold — skipping", v.get("name")
            )
            continue
        result.append(
            {
                "name": v["name"],
                "ingredients": v.get("ingredients", []),
                "calories": v.get("calories"),
                "protein_g": v.get("protein_g"),
                "carbs_g": v.get("carbs_g"),
                "fat_g": v.get("fat_g"),
                "macro_drift": _compute_macro_drift(original, v),
            }
        )

    if not result:
        raise ValueError("All generated variations failed macro drift validation")

    return result
