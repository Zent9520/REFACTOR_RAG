import logging
import time
from contextlib import contextmanager

# dùng logger của uvicorn để chắc chắn hiện trong terminal
logger = logging.getLogger("uvicorn.error")


@contextmanager
def timed(label: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        logger.info("[timing] %s: %.2fs", label, time.perf_counter() - start)