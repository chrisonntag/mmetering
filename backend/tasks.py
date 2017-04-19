from celery.task.schedules import crontab
from celery.decorators import periodic_task
from datetime import datetime, timedelta
from celery.utils.log import get_task_logger

from backend.serial import save_meter_data
from mmetering.emails import send_attachment_email

logger = get_task_logger(__name__)

@periodic_task(
    run_every=(crontab(minute="*/15")), #timedelta(seconds=6)#
    name="save_meter_data_task",
    ignore_result=True
)
def save_meter_data_task():
  """
  Saves current import and export since last
  reset from all active connected meters
  """
  saved_meters = save_meter_data()
  logger.info("Saved values from current active meters")
  logger.info(saved_meters)

@periodic_task(
    run_every=(timedelta(seconds=6)), #crontab(minute="*/15") timedelta(seconds=6)#
    name="send_meter_data_email_task",
    ignore_result=True
)
def send_meter_data_email_task():
  """
  Sends an email with current meter data
  on the first of each month
  """
  send_attachment_email()
  logger.info("Sent mail with current meter data")