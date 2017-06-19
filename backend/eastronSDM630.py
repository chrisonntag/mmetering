"""
Driver for the Eastron SDM630 metering device, for communication via the Modbus RTU protocol.
"""

import minimalmodbus
from django.conf import settings
from serial.serialutil import SerialException
import logging

logger = logging.getLogger(__name__)


class EastronSDM630(minimalmodbus.Instrument):
    """
    Instrument class for the Eastron SDM630 modbus meter.
    """

    def __init__(self, id, address, start, end, modus):
        self.id = id
        self.address = address
        self.start = start
        self.end = end
        self.modus = modus

        if settings.PRODUCTION:
            # port name, slave address (in decimal)
            minimalmodbus.Instrument.__init__(self, '/dev/ttyUSB0', address)
            self.serial.timeout = 6.0  # sec

    def get_id(self):
        return self.id

    def get_address(self):
        return self.address

    def get_modus(self):
        return self.modus

    def get_start(self):
        return self.start

    def get_end(self):
        return self.end

    def get_holding_register(self, hexc, length):
        return self.get_register(hexc, 3, length)

    def get_input_register(self, hexc, length):
        return self.get_register(hexc, 4, length)

    def get_register(self, hexc, code, length):
        while True:
            try:
                val = self.read_float(int(hexc, 16), functioncode=code, numberOfRegisters=length)
                if val is not None:
                    return val
            except (IOError, OSError, ValueError):
                continue
            except SerialException as e:
                logger.error("The used serial port is not available:\n%s" % str(e), exc_info=True)
            except RuntimeError:
                logger.error(
                    "Couldn't reach the %s device with address %d" % (self.get_modus(), self.get_address()),
                    exc_info=True
                )

    def get_value(self):
        if settings.PRODUCTION:
            if self.modus is 'EX':
                return self.get_input_register('0x4A', 2)
            else:
                return self.get_input_register('0x48', 2)
        else:
            logger.debug(
                "Celery beat is requesting meter data from the device with address %d" % self.get_address()
            )

    def print_value(self):
        print("Verbrauch: {} Wh".format(self.get_value()))
