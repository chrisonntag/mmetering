"""
Driver for the EX9055D digital IO relay.
"""

import minimalmodbus
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EX9055DM(minimalmodbus.Instrument):
    """
    Instrument class for the EX9055D-M Modbus RTU digital IO module.
    """

    def __init__(self, address):
        self.address = address

        if settings.PRODUCTION:
            minimalmodbus.Instrument.__init__(self, '/dev/ttyUSB0', address)
            self.serial.timeout = 3.0  # sec

    def write_output(self, pin, value):
        if value is 0 or 1:
            self.write_bit(pin, value, functioncode=5)
        else:
            raise ValueError('Output value can only be 0 or 1 (int)')

    def read_output(self, pin):
        return self.read_bit(pin, functioncode=1)

    def read_input(self, pin):
        return self.read_bit(pin, functioncode=2)
