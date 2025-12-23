from celery import Celery
from datetime import timedelta

celery_app = Celery(
    "app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
)

# 🔥 EXPLICIT IMPORTS (THIS FIXES IT)
celery_app.conf.imports = (
    "app.tasks.subscription_tasks",
)

celery_app.conf.beat_schedule = {
    "expire-subscriptions-every-30-seconds": {
        "task": "app.tasks.subscription_tasks.expire_subscriptions_task",
        "schedule": timedelta(seconds=30),
    }
}