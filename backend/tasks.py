from celery.schedules import crontab
from celery.task import periodic_task

from backend.serial import save_meter_data
from mmetering.emails import send_attachment_email
import logging

logger = logging.getLogger(__name__)


@periodic_task(
    run_every=(crontab(minute="*/15")),  # timedelta(seconds=6)#
    name="save_meter_data_task",
    ignore_result=True
)
def save_meter_data_task():
    """
    Saves current import and export since last
    reset from all active connected meters
    """
    saved_meters = save_meter_data()
    logger.debug(saved_meters)


@periodic_task(
    run_every=(crontab(0, 0, day_of_month='2')),
    name="send_meter_data_email_task",
    ignore_result=True
)
def send_meter_data_email_task():
    """
    Sends an email with current meter data
    on the first of each month
    """
    send_attachment_email()
