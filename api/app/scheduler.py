"""Local scheduler: APScheduler in-process. Cloud uses Cloud Scheduler -> POST /internal/evaluate instead."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

log = logging.getLogger("scheduler")


def start(container, minutes: int = 15) -> BackgroundScheduler:
    def job():
        try:
            container.engine.evaluate_all()
        except Exception:  # noqa: BLE001
            log.exception("scheduled evaluation failed")

    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(job, "interval", minutes=minutes, id="evaluate", max_instances=1, coalesce=True)
    sched.start()
    return sched
