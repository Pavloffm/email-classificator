import sys

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="DEBUG", diagnose=False)
logger.add("data/logs/app.log", level="DEBUG", diagnose=False)

__all__ = ["logger"]
