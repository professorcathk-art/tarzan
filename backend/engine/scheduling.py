"""Optional APScheduler heartbeat (persisted job store wiring can plug in Postgres URL)."""

from __future__ import annotations

import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _tick() -> None:
    logger.info("tarzan.scheduler.heartbeat")


def start_scheduler_if_enabled(database_url: str) -> BackgroundScheduler | None:
    """Start only when ENABLE_SCHEDULER=1. Uses in-memory jobs if no SQL URL provided."""
    global _scheduler
    if os.getenv("ENABLE_SCHEDULER", "").lower() not in {"1", "true", "yes"}:
        return None
    if _scheduler is not None:
        return _scheduler
    normalized = database_url.replace("+asyncpg", "+psycopg2")
    if normalized.startswith("postgresql://"):
        normalized = "postgresql+psycopg2://" + normalized.removeprefix("postgresql://")
    if normalized.startswith("postgres://"):
        normalized = "postgresql+psycopg2://" + normalized.removeprefix("postgres://")

    try:
        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

        jobstores = {"default": SQLAlchemyJobStore(url=normalized)}
        sched = BackgroundScheduler(jobstores=jobstores)
        logger.info("APScheduler SQLAlchemy job store enabled.")
    except Exception:  # noqa: BLE001
        sched = BackgroundScheduler()
        logger.warning("Scheduler falling back to in-memory job store.")

    sched.add_job(_tick, trigger="interval", hours=12, id="tarzan.scheduler.heartbeat", replace_existing=True)
    sched.start()
    _scheduler = sched
    return sched


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        finally:
            _scheduler = None
