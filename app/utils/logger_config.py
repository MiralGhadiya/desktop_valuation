# app/utils/logger_config.py
import os
import logging

from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(LOG_DIR, exist_ok=True)

TODAY = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"{TODAY}.log")

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

file_handler = TimedRotatingFileHandler(
    LOG_FILE,
    when="midnight",       # rotate at midnight
    interval=1,            # every 1 day
    backupCount=365,        # keep 365 days of logs
    encoding="utf-8"
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
try:
    console_handler.stream.reconfigure(encoding="utf-8")
except Exception:
    pass

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 🔑 CRITICAL FIX
logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app_logger = logger
