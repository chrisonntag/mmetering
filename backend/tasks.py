from celery.schedules import crontab
from celery.task import periodic_task
from celery.signals import after_setup_task_logger
from backend.serial import save_meter_data
from mmetering.emails import send_data_email
from datetime import datetime, timedelta
import logging


def setup_logging(**kwargs):
    """
      Handler names is a list of handlers from your settings.py you want to
      attach to this
    """

    handler_names = ['mail_admins', 'file', 'console']

    import logging.config
    from django.conf import settings
    logging.config.dictConfig(settings.LOGGING)

    logger = kwargs.get('logger')

    handlers = [x for x in logging.root.handlers if x.name in handler_names]
    for handler in handlers:
        logger.addHandler(handler)
        logger.setLevel(handler.level)
        logger.propagate = False


after_setup_task_logger.connect(setup_logging)


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
    logger = save_meter_data_task.get_logger()
    logger.setLevel(logging.DEBUG)

    saved_meters = save_meter_data()
    logger.debug(saved_meters)


@periodic_task(
    run_every=(crontab(0, 1, day_of_month='1')),
    name="send_meter_data_email_task",
    ignore_result=True
)
def send_meter_data_email_task():
    """
    Sends an email with current meter data
    on the first of each month
    """
    # Subtract the current # of days in this month in order to query the last month.
    today = datetime.today()
    last_month = today - timedelta(days=today.day)
    send_data_email(last_month)
