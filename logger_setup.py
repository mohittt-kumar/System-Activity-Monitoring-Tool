import os
import logging
from logging.handlers import RotatingFileHandler
import config

_logger_instance = None

def get_logger(name="SystemMonitor"):
    """
    Returns a configured application logger with:
      1. Console logging (live terminal feedback)
      2. Rotating file logging (saves to output/logs/system_monitor.log)
    Automatically rotates log files when they reach MAX_LOG_BYTES.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Ensure log directory exists before creating file handler
    os.makedirs(config.LOG_DIR, exist_ok=True)

    # Formatter: [2026-10-10 22:15:00] [INFO] [ScreenshotThread] Message here
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler (Standard Output)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Rotating File Handler (Keeps file size bounded)
    file_handler = RotatingFileHandler(
        config.APP_LOG_FILE,
        maxBytes=config.MAX_LOG_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _logger_instance = logger
    return _logger_instance
