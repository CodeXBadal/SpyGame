"""Structured logging configuration with rotation."""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from typing import Optional

from bot.config import settings

_CONFIGURED = False


def setup_logging(log_dir: Optional[str] = None, level: Optional[str] = None) -> None:
    """Configure root logger with console + rotating file handlers."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_dir = log_dir or settings.log_dir
    level_name = (level or settings.log_level).upper()
    log_level = getattr(logging, level_name, logging.INFO)

    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(log_level)
    # Clear pre-existing handlers (avoid duplicates on reload)
    for h in list(root.handlers):
        root.removeHandler(h)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(log_level)
    root.addHandler(console)

    app_file = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "bot.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    app_file.setFormatter(formatter)
    app_file.setLevel(log_level)
    root.addHandler(app_file)

    error_file = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, "error.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    error_file.setFormatter(formatter)
    error_file.setLevel(logging.ERROR)
    root.addHandler(error_file)

    # Tame noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger, ensuring config is initialized."""
    if not _CONFIGURED:
        setup_logging()
    return logging.getLogger(name)
