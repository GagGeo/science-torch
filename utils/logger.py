"""
utils/logger.py — Logging centralisé
"""

import logging
import sys
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger configuré."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    return logger


def add_file_handler(log_dir: str):
    """Ajoute un handler fichier (appelé après config)."""
    import logging
    from datetime import datetime

    log_path = Path(log_dir) / f"veille_{datetime.now().strftime('%Y_%m')}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_fmt)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
