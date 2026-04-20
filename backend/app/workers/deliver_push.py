"""
Sends pending web push NutritionReminders via pywebpush.
Runs every 60 s in the worker pool.
Full implementation in feat/web-push-reminders.
"""


async def deliver_due_reminders(ctx: dict) -> dict:
    # TODO: implement in feat/web-push-reminders
    return {"status": "not_implemented"}
