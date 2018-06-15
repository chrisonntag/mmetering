"""
Driver for the Eastron SDM630 metering device, for communication via the Modbus RTU protocol.
"""

import minimalmodbus
from time import sleep
import logging

logger = logging.getLogger(__name__)


MAX_RETRY = 6
FUNC_CODE_INPUT_REG = 4
FUNC_CODE_HOLDING_REG = 3

# Register addresses as defined by Eastron.
# See http://bg-etech.de/download/manual/SDM630Register.pdf
# Please note that this is the superset of all SDM devices - some
# addresses might not work on some devices.
REG_SDML1Voltage = '0x0000'
REG_SDML2Voltage = '0x0002'
REG_SDML3Voltage = '0x0004'
REG_SDML1Current = '0x0006'
REG_SDML2Current = '0x0008'
REG_SDML3Current = '0x000A'
REG_SDML1Power = '0x000C'
REG_SDML2Power = '0x000E'
REG_SDML3Power = '0x0010'
REG_SDML1Import = '0x015a'
REG_SDML2Import = '0x015c'
REG_SDML3Import = '0x015e'
REG_SDMTotalImport = '0x0048'
REG_SDML1Export = '0x0160'
REG_SDML2Export = '0x0162'
REG_SDML3Export = '0x0164'
REG_SDMTotalExport = '0x004a'
REG_SDML1THDVoltageNeutral = '0x00ea'
REG_SDML2THDVoltageNeutral = '0x00ec'
REG_SDML3THDVoltageNeutral = '0x00ee'
REG_SDMAvgTHDVoltageNeutral = '0x00F8'
REG_SDMFrequency = '0x0046'


class EastronSDM630(minimalmodbus.Instrument):
    """Instrument class for EastronSDM630 meter.

    Communicates via Modbus RTU protocol (via RS232 or RS485), using the *MinimalModbus* Python module.

    Args:
        portname (str): port name
        slaveaddress (int): slave address in the range 1 to 247

    Implemented with these function codes (in decimal):

    =======================  ====================
    Description              Modbus function code
    =======================  ====================
    Read holding registers   3
    Read input registers     4
    =======================  ====================

    Raises:
        serial.serialutil.SerialException

    """

    def __init__(self, portname, slaveaddress):
        self.portname = portname
        self.slaveaddress = slaveaddress

        minimalmodbus.Instrument.__init__(self, portname, slaveaddress)
        self.serial.timeout = 0.5  # sec

    def get_slaveaddress(self):
        return self.slaveaddress

    def get_portname(self):
        return self.portname

    def read_holding_register(self, hexc, length):
        """Reads MODBUS input registers.

        Args:
            hexc: The slaves register number
            length: The number of registers allocated for the value.

        Returns:
            The numerical value.
        """
        return self.read_float_register(hexc, 3, length)

    def read_input_register(self, hexc, length):
        """Reads MODBUS input registers.

        Args:
            hexc: The slaves register number
            length: The number of registers allocated for the value.

        Returns:
            The numerical value.
        """
        return self.read_float_register(hexc, 4, length)

    def read_float_register(self, hexc, code, length):
        """Read a floating point number from the slave.
        The Modbus RTU standard prescribes a silent period corresponding to 3.5 characters
        between each message, to be able fo figure out where one message ends and
        the next one starts. On a baud rate of 19200 (19200 bits/s) a 3.5 characters silent
        period corresponds to 2.0ms.

        Args:
            hexc: The slaves register number as a hex.
            code: The MODBUS function code.
            length: The number of registers allocated for the float.

        Returns:
             The numerical value (float).

        Raises:
            ValueError, TypeError, IOError
        """
        # In order to avoid overlapping messages, wait 2.0ms as described above.
        # TODO: Retry with MAX_RETRIES until we have something
        sleep(0.002)
        return self.read_float(int(hexc, 16), functioncode=code, numberOfRegisters=length)

    def read_total_import(self):
        """Reads the Import Wh since last reset.

        Returns:
            The numerical value.
        """
        return self.read_input_register(REG_SDMTotalImport, 2)

    def read_import_L1(self):
        return self.read_input_register(REG_SDML1Import, 2)

    def read_import_L2(self):
        return self.read_input_register(REG_SDML2Import, 2)

    def read_import_L3(self):
        return self.read_input_register(REG_SDML3Import, 2)

    def read_total_export(self):
        """Reads the Export Wh since last reset.

        Returns:
            The numerical value.
        """
        return self.read_input_register(REG_SDMTotalExport, 2)

    def read_export_L1(self):
        return self.read_input_register(REG_SDML1Export, 2)

    def read_export_L2(self):
        return self.read_input_register(REG_SDML2Export, 2)

    def read_export_L3(self):
        return self.read_input_register(REG_SDML3Export, 2)

    def read_network_baud_rate(self):
        """Reads the network port baud rate for MODBUS Protocol, where:

        * 0 = 2400 baud.
        * 1 = 4800 baud.
        * 2 = 9600 baud, default.
        * 3 = 19200 baud.
        * 4 = 38400 baud.

        Returns:
             The numerical value as a float.
        """
        return self.read_holding_register('0x1C', 2)

    def __str__(self, *args, **kwargs):
        diagnose_string = 'EastronSDM630(%s, %d)\n\n' % (self.portname, self.slaveaddress)

        if self.debug is True:
            diagnose_string += 'Total Import: %f\n' % self.read_total_import()
            diagnose_string += 'Import L1: %f\n' % self.read_import_L1()
            diagnose_string += 'Import L2: %f\n' % self.read_import_L2()
            diagnose_string += 'Import L3: %f\n' % self.read_import_L3()
            diagnose_string += 'Total Export: %f\n' % self.read_total_export()
            diagnose_string += 'Export L1: %f\n' % self.read_export_L1()
            diagnose_string += 'Export L2: %f\n' % self.read_export_L2()
            diagnose_string += 'Export L3: %f\n' % self.read_export_L3()
            diagnose_string += 'Network Baud Rate: %d\n' % self.read_network_baud_rate()

            return diagnose_string
        else:
            return diagnose_string

