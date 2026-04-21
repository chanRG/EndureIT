"""
Extracts meal data from an uploaded nutrition PDF using pdfplumber + Claude.
Enqueued by the nutrition upload endpoint after saving the file.
"""

from app.core.logging import get_logger
from app.db.database import SessionLocal
from app.models.nutrition import NutritionPlan, NutritionPlanStatus
from app.services.nutrition.pdf_parser import (
    extract_pdf_text,
    parse_nutrition_pdf as _parse,
    persist_parsed_plan,
)

logger = get_logger(__name__)


async def parse_nutrition_pdf(ctx: dict, nutrition_plan_id: int) -> dict:
    db = SessionLocal()
    try:
        plan = (
            db.query(NutritionPlan)
            .filter(NutritionPlan.id == nutrition_plan_id)
            .first()
        )
        if plan is None:
            logger.warning("NutritionPlan %d not found", nutrition_plan_id)
            return {"status": "not_found"}

        pdf_path = plan.source_pdf_url
        if not pdf_path:
            plan.status = NutritionPlanStatus.FAILED
            db.commit()
            return {"status": "no_pdf_path"}

        raw_text = extract_pdf_text(pdf_path)
        plan.raw_text = raw_text

        try:
            parsed = _parse(raw_text)
        except ValueError as exc:
            logger.error("PDF parse failed for plan %d: %s", nutrition_plan_id, exc)
            plan.status = NutritionPlanStatus.FAILED
            db.commit()
            return {"status": "parse_failed", "error": str(exc)}

        persist_parsed_plan(db, plan, parsed)
        db.commit()
        logger.info("Nutrition plan %d parsed successfully", nutrition_plan_id)
        return {"status": "ok", "meals": len(parsed.meals)}

    except Exception as exc:
        db.rollback()
        logger.exception("parse_nutrition_pdf worker failed: %s", exc)
        raise
    finally:
        db.close()
