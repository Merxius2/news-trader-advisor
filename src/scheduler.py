"""APScheduler wrapper for hourly digest."""

from __future__ import annotations

import logging
from typing import Callable

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config_loader import Settings

logger = logging.getLogger(__name__)


class SchedulerService:
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

    def start(self) -> None:
        self.add_hourly_job()
        logger.info("Scheduler started — hourly digest at :%02d", self.settings.schedule.hourly_digest_minute)
        self.scheduler.start()

    def stop(self) -> None:
        self.scheduler.shutdown(wait=False)


def schedule_hourly_digest(service: SchedulerService) -> None:
    service.add_hourly_job()
