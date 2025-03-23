from celery import Celery
from celery.schedules import crontab

from src.config import Config

from .notification import NotificationService

cfg = Config()
celery_app = Celery("tasks", broker=cfg.broker_url, backend=cfg.backend_url)

# Configure Celery including timezone and beat schedule.
celery_app.conf.update(
    timezone="America/Toronto",
    beat_schedule={
        "weekly-summary-job": {
            "task": "src.service.weekly_summary_task",
            # Run every Monday at midnight (00:00)
            "schedule": crontab(day_of_week="mon", hour=0, minute=0),
        },
    },
)


@celery_app.task(name="src.service.weekly_summary_task")
def weekly_summary_task():
    """
    Celery task to run the weekly summary job.
    """
    notification_service = NotificationService(cfg)
    notification_service.weekly_summary_job()
