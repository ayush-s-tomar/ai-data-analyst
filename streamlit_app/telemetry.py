"""Privacy-safe operational logging: durations and flags only, never questions, data or code."""
import logging
import time

log = logging.getLogger("ada")


def configure_logging() -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


def timed_answer(fn, *args, **kwargs):
    start = time.time()
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        log.warning("answer failed seconds=%.2f error=%s", time.time() - start, type(exc).__name__)
        raise
    log.info("answered seconds=%.2f has_code=%s code_error=%s charts=%d", time.time() - start,
             result.get("has_code"), bool(result.get("code_error")), len(result.get("charts", [])))
    return result
