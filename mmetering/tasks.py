from __future__ import absolute_import
from celery import task
from celery.utils.log import get_task_logger

from mmetering.emails import send_contact_email, send_system_email

logger = get_task_logger(__name__)


@task(name='send_contact_email_task')
def send_contact_email_task(name, email, message):
    """Sends an email when contact form is filled successfully."""
    logger.info("Send contact email...")
    return send_contact_email(name, email, message)


@task(name='send_system_email_task')
def send_system_email_task(message):
    """Sends a mail from the system."""
    logger.info("Send system email...")
    return send_system_email(message)
