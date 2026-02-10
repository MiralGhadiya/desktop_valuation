from fastapi import APIRouter, BackgroundTasks
from app.tasks.subscription_tasks import run_subscription_maintenance
from app.tasks.currency_tasks import update_exchange_rates

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/run-maintenance")
def run_maintenance(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_subscription_maintenance)
    background_tasks.add_task(update_exchange_rates)
    return {"status": "maintenance started"}
