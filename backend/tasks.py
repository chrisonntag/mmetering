from celery.task.schedules import crontab
from celery.decorators import periodic_task
from datetime import datetime, timedelta
from celery.utils.log import get_task_logger

from backend.serial import save_meter_data

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