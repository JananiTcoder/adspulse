import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
_scheduler = None


def _run_daily():
    from .database import SessionLocal
    from .pipeline import run_all
    db = SessionLocal()
    try:
        results = run_all(db)
        logger.info("Nightly run complete: %d users processed", len(results))
    finally:
        db.close()


def start_scheduler():
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _run_daily,
        trigger=CronTrigger(hour=0, minute=0),
        id="daily_report",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started — daily reports at 00:00 UTC")
