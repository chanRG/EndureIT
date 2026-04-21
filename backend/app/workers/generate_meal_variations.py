"""
Generates Claude meal variations for a NutritionPlanMeal.
Enqueued by POST /nutrition/meals/{id}/variations.
"""

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.nutrition import (
    MealVariation,
    NutritionPlan,
    NutritionPlanMeal,
    VariationSource,
)
from app.services.nutrition.variation_generator import generate_variations

logger = get_logger(__name__)


async def generate_meal_variations(ctx: dict, meal_id: int) -> dict:
    db = SessionLocal()
    try:
        meal = (
            db.query(NutritionPlanMeal)
            .join(NutritionPlan)
            .filter(NutritionPlanMeal.id == meal_id)
            .first()
        )
        if meal is None:
            logger.warning("Meal %d not found", meal_id)
            return {"status": "not_found"}

        slot = (
            meal.meal_slot.value if hasattr(meal.meal_slot, "value") else meal.meal_slot
        )
        variations = generate_variations(
            meal_name=meal.name,
            meal_slot=slot,
            calories=meal.calories,
            protein_g=meal.protein_g,
            carbs_g=meal.carbs_g,
            fat_g=meal.fat_g,
            ingredients=meal.ingredients or [],
        )

        from app.services.claude_client import default_model

        for v in variations:
            row = MealVariation(
                meal_id=meal.id,
                name=v["name"],
                ingredients=v["ingredients"],
                calories=v["calories"],
                protein_g=v["protein_g"],
                carbs_g=v["carbs_g"],
                fat_g=v["fat_g"],
                macro_drift=v["macro_drift"],
                generated_by=VariationSource.AI,
                model_version=default_model(),
            )
            db.add(row)

        db.commit()
        logger.info("Generated %d variations for meal %d", len(variations), meal_id)
        return {"status": "ok", "count": len(variations)}

    except Exception as exc:
        db.rollback()
        logger.exception("generate_meal_variations failed: %s", exc)
        raise
    finally:
        db.close()
