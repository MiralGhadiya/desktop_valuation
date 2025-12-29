from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "app",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/1",
)

celery_app.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.imports = (
    "app.tasks.subscription_tasks",
    "app.tasks.valuation_tasks",
)

celery_app.conf.beat_schedule = {
    "expire-subscriptions-daily": {
        "task": "app.tasks.subscription_tasks.expire_subscriptions_task",
        "schedule": crontab(hour=0, minute=0),
    },
    "send-subscription-expiry-reminders-daily": {
        "task": "app.tasks.subscription_tasks.send_expiry_reminders_task",
        "schedule": crontab(hour=9, minute=0),
    },
}
