"""APScheduler-based scheduler for periodic data collection."""

from __future__ import annotations

from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger("pipeline.scheduler")


class DataScheduler:
    """Scheduler for periodic data collection pipelines."""

    def __init__(self):
        self._scheduler = BackgroundScheduler(timezone=settings.timezone)
        self._jobs: dict[str, str] = {}  # name -> job_id

    def add_cron(self, name: str, func, cron_expr: str, **kwargs):
        """Add a cron-triggered job.

        Args:
            name: Unique job name.
            func: Callable to execute.
            cron_expr: Standard cron expression (e.g. "*/5 * * * *").
        """
        trigger = CronTrigger.from_crontab(cron_expr)
        job = self._scheduler.add_job(func, trigger, id=name, name=name, **kwargs)
        self._jobs[name] = job.id
        logger.info("Added cron job `%s` with schedule `%s`", name, cron_expr)

    def add_interval(self, name: str, func, minutes: int, **kwargs):
        """Add an interval-triggered job."""
        trigger = IntervalTrigger(minutes=minutes)
        job = self._scheduler.add_job(func, trigger, id=name, name=name, **kwargs)
        self._jobs[name] = job.id
        logger.info("Added interval job `%s` every %d minutes", name, minutes)

    def start(self):
        """Start the scheduler."""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def remove(self, name: str):
        """Remove a job by name."""
        if name in self._jobs:
            self._scheduler.remove_job(self._jobs[name])
            del self._jobs[name]
            logger.info("Removed job `%s`", name)

    def get_jobs(self) -> list[dict]:
        """List all registered jobs."""
        return [
            {
                "id": j.id,
                "name": j.name,
                "next_run": str(j.next_run_time) if j.next_run_time else None,
            }
            for j in self._scheduler.get_jobs()
        ]

    @property
    def running(self) -> bool:
        return self._scheduler.running
