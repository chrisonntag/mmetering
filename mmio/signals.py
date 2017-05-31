import os
import configparser
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from mmetering.models import MeterData
from mmio.controlboard import ControlBoard
from mmetering_server.settings import BASE_DIR


config = configparser.RawConfigParser()
config.read(os.path.join(BASE_DIR, 'my.cnf'))

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MeterData)
def meterdata_post_save(sender, **kwargs):
    logger.debug('Saved: {}'.format(kwargs['instance'].__dict__))
    ioboard = ControlBoard(config.getint('controlboard', 'address'))

    # after each signal check if at least 70% of energy production
    # are done by BHKW and PV and switch LED on the ControlBoard
    # TODO: get real values from mmetering.summaries
    check_production_threshold = True

    if check_production_threshold:
        ioboard.set_led('green')
    else:
        ioboard.set_led('red')
