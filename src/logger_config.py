"""Centralized logging configuration for the weather pipeline.

The log level is read dynamically from the LOG_LEVEL variable in the
.env file. Execution details are written to pipeline.log and echoed to
the console.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOG_FILE = "pipeline.log"
_configured = False


def _configure_root_logger() -> None:
    global _configured
    if _configured:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger wired to the shared pipeline configuration."""
    _configure_root_logger()
    return logging.getLogger(name)
