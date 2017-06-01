import os
import configparser
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from mmetering.models import MeterData
from mmetering.summaries import Overview
from mmio.controlboard import ControlBoard
from mmetering_server.settings import BASE_DIR


config = configparser.RawConfigParser()
config.read(os.path.join(BASE_DIR, 'my.cnf'))

logger = logging.getLogger(__name__)


class DummyRequest:
    GET = None


@receiver(post_save, sender=MeterData)
def meterdata_post_save(sender, **kwargs):
    io_address = config.getint('controlboard', 'address')

    logger.debug('Connecting to control board on address %i' % io_address)

    io_board = ControlBoard(io_address)
    threshold = config.getint('controlboard', 'supply-threshold') / 100

    # after each signal, check if at least 70% of energy
    # supply are produced by BHKW and PV
    data = Overview(DummyRequest.GET)

    if data.is_supply_over_threshold(threshold):
        logger.debug("Over 70% of energy supply are produced by BHKW and PV")
        io_board.set_led('green')
    else:
        logger.debug("Under 70% of energy supply are produced by BHKW and PV")
        io_board.set_led('red')
