import os
import logging
import queue
from logging.handlers import (
    TimedRotatingFileHandler,
    QueueHandler,
    QueueListener,
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


file_handler = TimedRotatingFileHandler(
    LOG_FILE,
    when="midnight",
    interval=1,
    backupCount=30,     # ✅ last 30 days
    encoding="utf-8",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S",
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)


listener = QueueListener(
    log_queue,
    file_handler,
    console_handler,
    respect_handler_level=True,
)

listener.start()

app_logger = logger