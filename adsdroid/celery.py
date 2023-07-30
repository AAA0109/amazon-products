import os

from celery import Celery, chain
from celery.schedules import crontab  # type: ignore
from celery.signals import setup_logging

from apps.ads_api.constants import ServerLocation

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adsdroid.settings")

app = Celery("adsdroid")  # type: ignore
chain = chain

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig

    from django.conf import settings

    dictConfig(settings.LOGGING)


app.conf.beat_schedule = {
    "Sets launch status to False on books which publication dates are > 60": {
        "task": "apps.ads_api.tasks.update_books_launch_status",
        "schedule": crontab(hour=0, minute=30),
    },
    "Process Sponsored Products tasks via Ads API": {
        "task": "apps.ads_api.data_exchange.sp_chain",
        "schedule": crontab(hour=0, minute=11),
    },
    "Sync_sp_data for EUROPE and FAR_EAST": {
        "task": "apps.ads_api.tasks.sync_sp_data",
        "schedule": crontab(hour=0, minute=2),
        "args": ([ServerLocation.EUROPE, ServerLocation.FAR_EAST],),
    },
    "Sync_sp_data for NORTH_AMERICA": {
        "task": "apps.ads_api.tasks.sync_sp_data",
        "schedule": crontab(hour=8, minute=2),
        "args": ([ServerLocation.NORTH_AMERICA],),
    },
    "Transferring old report data from RecentReportData to ReportData": {
        "task": "apps.ads_api.tasks.transfere_90_days_recent_report_data_to_report_data",
        "schedule": crontab(hour=14, minute=2),
    },
    "Process Sponsored Products tasks via requests (after cookies sync)": {
        "task": "apps.ads_api.data_exchange.sp_requests_chain",
        "schedule": crontab(hour=1, minute=30),
    },
    "Process Sponsored Brands tasks via requests (after cookies sync)": {
        "task": "apps.ads_api.data_exchange.sb_requests_chain",
        "schedule": crontab(hour=2, minute=30),
    },
    "Sync Profiles": {
        "task": "apps.ads_api.tasks.sync_profiles_chain",
        "schedule": crontab(hour=5, minute=0),
    },
    "Create campaigns from Google Sheet": {
        "task": "apps.ads_api.tasks.create_campaign_from_google_sheet",
        "schedule": crontab(hour="*/3", minute=0),
    },
    "Negate targets from Google Sheet": {
        "task": "apps.ads_api.data_exchange.negate_from_google_sheet",
        "schedule": crontab(hour="*/5", minute=0),
    },
    "Update books managed status": {
        "task": "apps.ads_api.tasks.set_books_managed_status",
        "schedule": crontab(hour=2, minute=30),
    },
    # "Check keywords rank from Google Sheet": {
    #     "task": "apps.ads_api.data_exchange.get_keyword_rank_from_google_sheets",
    #     "schedule": crontab(hour="*/12", minute=0),
    # },
}
