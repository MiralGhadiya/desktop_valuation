from fastapi import APIRouter, BackgroundTasks
from app.tasks.subscription_tasks import run_subscription_maintenance
from app.tasks.currency_tasks import update_exchange_rates

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/run-maintenance")
def run_maintenance():
    run_subscription_maintenance()
    update_exchange_rates()
    return {"status": "maintenance finished"}