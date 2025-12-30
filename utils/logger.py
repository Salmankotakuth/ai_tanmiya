# app/utils/logger.py

"""
Centralized Logging Configuration
---------------------------------

This module configures application‑wide logging.

Features:
- Colored logs for local development
- File logging for production
- Easy import: from app.utils.logger import get_logger
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config.settings import settings


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "tanmiya.log"


def _configure_logger():
    logger = logging.getLogger("tanmiya")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers during reload
    if logger.handlers:
        return logger

    # Console Handler (colored)
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        "\033[92m[%(asctime)s] [%(levelname)s]\033[0m %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler (rotating)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2_000_000,  # 2 MB
        backupCount=5
    )
    file_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str):
    base = _configure_logger()
    return base.getChild(name)
