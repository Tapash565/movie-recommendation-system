import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from functools import lru_cache

# Create a custom logger
logger = logging.getLogger("movie_recommendation")

# Default log level (will be updated from config if available)
DEFAULT_LOG_LEVEL = "INFO"


def _init_logger():
    """Initialize logger with settings."""
    log_level = DEFAULT_LOG_LEVEL

    # Try to get from settings if available (without causing circular import)
    try:
        from .config import get_settings
        settings = get_settings()
        log_level = settings.LOG_LEVEL.upper()
    except Exception:
        # Fallback to environment variable
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Create handlers
    c_handler = logging.StreamHandler(sys.stdout)
    # Max size 10MB, keep 5 backups
    f_handler = RotatingFileHandler("app.log", maxBytes=10*1024*1024, backupCount=5)

    # Create formatters and add it to handlers
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)

    # Add handlers to the logger
    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)


# Initialize on module load
_init_logger()


def get_logger(name):
    """Returns a logger with the specified name as a child of the root project logger."""
    return logger.getChild(name)
