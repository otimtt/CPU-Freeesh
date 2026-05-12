"""
Configure file + console logging for CPU Freeesh.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cpu_freeesh.log")


def setup(level: int = logging.INFO) -> None:
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    file_handler = RotatingFileHandler(
        _LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
