from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.subscription_service import expire_subscriptions

@celery_app.task(name="app.tasks.subscription_tasks.expire_subscriptions_task")
def expire_subscriptions_task():
    db = SessionLocal()
    try:
        return expire_subscriptions(db)
    finally:
        db.close()