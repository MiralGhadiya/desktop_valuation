# app/utils/logger_config.py

import os
import sys
import logging
import queue
from logging.handlers import (
    TimedRotatingFileHandler,
    QueueHandler,
    QueueListener,
)

IS_ALEMBIC = (
    "alembic" in sys.argv[0].lower()
    or "alembic" in os.environ.get("PYTHONEXECUTABLE", "").lower()
)

LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "app.log")

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

logger.handlers.clear()
logger.propagate = False

log_queue = queue.Queue(-1)
queue_handler = QueueHandler(log_queue)
logger.addHandler(queue_handler)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S",
)

handlers = []

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
handlers.append(console_handler)

if not IS_ALEMBIC:
    try:
        file_handler = TimedRotatingFileHandler(
            LOG_FILE,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
            delay=False,      # Disable delay
            utc=True,
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    except Exception as e:
        logger.error(f"Error setting up file handler: {e}")
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)

listener = QueueListener(
    log_queue,
    *handlers,
    respect_handler_level=True,
)

listener.start()

app_logger = logger
