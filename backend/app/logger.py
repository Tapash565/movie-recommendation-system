import logging
import sys
import os

# Create a custom logger
logger = logging.getLogger("movie_recommendation")

# Set the default log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# Create handlers
c_handler = logging.StreamHandler(sys.stdout)
f_handler = logging.FileHandler("app.log")

# Create formatters and add it to handlers
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(log_format)
f_handler.setFormatter(log_format)

# Add handlers to the logger
if not logger.handlers:
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

def get_logger(name):
    """Returns a logger with the specified name as a child of the root project logger."""
    return logger.getChild(name)
