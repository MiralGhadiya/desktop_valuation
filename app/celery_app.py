# app/celery_app.py

import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"{REDIS_URL}/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", f"{REDIS_URL}/1")

celery = Celery(
    "app",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery.conf.update(
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Explicit task discovery
celery.conf.imports = (
    "app.tasks.subscription_tasks",
    "app.tasks.valuation_tasks",
    "app.tasks.currency_tasks",
)

# Celery Beat schedule
celery.conf.beat_schedule = {
    "expire-subscriptions-daily": {
        "task": "app.tasks.subscription_tasks.expire_subscriptions_task",
        "schedule": crontab(hour=0, minute=0),
    },
    "send-subscription-expiry-reminders-daily": {
        "task": "app.tasks.subscription_tasks.send_expiry_reminders_task",
        "schedule": crontab(hour=9, minute=0),
    },
    "update-exchange-rates": {
        "task": "app.tasks.currency_tasks.update_exchange_rates",
        "schedule": crontab(hour=0, minute=0),
    },
}