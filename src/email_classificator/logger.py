import os
import sys
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="DEBUG", diagnose=False)
logger.add(
    Path(os.environ.get("EMAIL_STATE_DIR", "data")) / "logs" / "app.log",
    level="DEBUG",
    diagnose=False,
)

__all__ = ["logger"]
