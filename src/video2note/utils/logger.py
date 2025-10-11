# src/video2note/utils/logger.py

import logging
import sys

def setup_logging(level: str = "INFO"):
    numeric = getattr(logging, level.upper(), None)
    if numeric is None:
        numeric = logging.INFO
    logging.basicConfig(
        level=numeric,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout
    )
