"""APScheduler wrappers for digest and news poll."""

from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config_loader import Settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """Blocking scheduler for CLI `run-daemon`."""

    def __init__(self, settings: Settings, job: Callable[[], None]) -> None:
        self.settings = settings
        self.job = job
        self.scheduler = BlockingScheduler()

    def add_hourly_job(self) -> None:
        minute = self.settings.schedule.hourly_digest_minute
        self.scheduler.add_job(
            self.job,
            CronTrigger(minute=minute),
            id="hourly_digest",
            replace_existing=True,
        )

    def add_news_poll_job(self, poll_job: Callable[[], None]) -> None:
        minutes = self.settings.schedule.news_poll_interval_minutes
        self.scheduler.add_job(
            poll_job,
            IntervalTrigger(minutes=minutes),
            id="news_poll",
            replace_existing=True,
        )

    def start(self) -> None:
        self.add_hourly_job()
        logger.info(
            "Scheduler started — hourly digest at :%02d",
            self.settings.schedule.hourly_digest_minute,
        )
        self.scheduler.start()

    def stop(self) -> None:
        self.scheduler.shutdown(wait=False)


class BackgroundSchedulerService:
    """Non-blocking scheduler for FastAPI lifespan."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scheduler = BackgroundScheduler()

    def add_jobs(
        self,
        poll_job: Callable[[], None],
        hourly_job: Callable[[], None],
    ) -> None:
        minutes = self.settings.schedule.news_poll_interval_minutes
        self.scheduler.add_job(
            poll_job,
            IntervalTrigger(minutes=minutes),
            id="news_poll",
            replace_existing=True,
        )
        self.scheduler.add_job(
            hourly_job,
            CronTrigger(minute=self.settings.schedule.hourly_digest_minute),
            id="hourly_digest",
            replace_existing=True,
        )

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info(
                "Background scheduler started — poll every %dm, digest at :%02d",
                self.settings.schedule.news_poll_interval_minutes,
                self.settings.schedule.hourly_digest_minute,
            )

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)


def schedule_hourly_digest(service: SchedulerService) -> None:
    service.add_hourly_job()
