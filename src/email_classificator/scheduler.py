import os
import re
import signal
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from filelock import FileLock, Timeout

from email_classificator.logger import logger


def parse_run_times(value: str) -> set[str]:
    times = {item.strip() for item in value.split(",")}
    if not times or any(
        re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", item) is None for item in times
    ):
        raise ValueError(
            "RUN_TIMES must contain comma-separated HH:MM times (24-hour)."
        )
    return times


def run_once() -> None:
    from email_classificator.pipeline import main

    state_dir = Path(os.environ.get("EMAIL_STATE_DIR", "data"))
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = FileLock(state_dir / "pipeline.lock", timeout=0)
    try:
        lock.acquire()
    except Timeout:
        logger.warning("Pipeline already running; skipping this run.")
        return

    try:
        logger.info("Pipeline started.")
        main()
        logger.info("Pipeline completed.")
    finally:
        lock.release()


def schedule() -> None:
    timezone = ZoneInfo(os.environ.get("TZ", "Europe/Bratislava"))
    run_times = parse_run_times(os.environ.get("RUN_TIMES", "09:00,21:00"))

    # Exit cleanly on Docker stop, including when a pipeline run is in progress.
    def stop(signum, frame):
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    logger.info("Scheduled at {} in {}.", ", ".join(sorted(run_times)), timezone.key)
    current_date = None
    completed_slots: set[str] = set()
    while True:
        now = datetime.now(timezone)
        if now.date() != current_date:
            current_date = now.date()
            completed_slots.clear()
        slot = now.strftime("%H:%M")
        if slot in run_times and slot not in completed_slots:
            completed_slots.add(slot)
            try:
                run_once()
            except Exception as error:
                # Avoid logging exception values that could contain email content.
                logger.error(
                    "Pipeline failed ({}); waiting for the next scheduled run.",
                    type(error).__name__,
                )
        now = datetime.now(timezone)
        time.sleep(60 - now.second - now.microsecond / 1_000_000)
