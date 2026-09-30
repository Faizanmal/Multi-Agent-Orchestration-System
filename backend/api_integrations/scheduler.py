"""APScheduler background runner for scheduled automations."""

import logging
import os

logger = logging.getLogger(__name__)
_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return
    if os.environ.get("DISABLE_AUTOMATION_SCHEDULER", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning("APScheduler not available — scheduled automations disabled")
        return

    from django.utils import timezone

    from .automation_runner import run_automation
    from .models import ScheduledAutomation

    def tick():
        from django.db import close_old_connections

        close_old_connections()
        due = ScheduledAutomation.objects.filter(
            is_active=True, next_run_at__lte=timezone.now()
        )
        for automation in due:
            logger.info(
                f"Running automation: {automation.name} ({automation.automation_type})"
            )
            run_automation(automation)

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        tick, "interval", minutes=1, id="automation_tick", replace_existing=True
    )
    _scheduler.start()
    logger.info("Automation scheduler started (1-minute tick)")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
