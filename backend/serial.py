from datetime import datetime
from serial.serialutil import SerialException
from backend.eastronSDM630 import EastronSDM630
from mmetering.models import Meter, MeterData
from mmetering_server.settings.defaults import MODBUS_PORT
import serial.tools.list_ports
import logging

logger = logging.getLogger(__name__)
MAX_RETRY = 6
PORTS_LIST = [port for port, desc, hwid in serial.tools.list_ports.grep('tty')]

if MODBUS_PORT in PORTS_LIST:
    # Move manually configured port to the front in
    # order to test this one first.
    PORTS_LIST.remove(MODBUS_PORT)
    PORTS_LIST.insert(0, MODBUS_PORT)


# TODO: Refactor method naming and docstring style
def save_meter_data():
    """
    Loops through a EastronSDM630 object list, checks wether a startdate
    has already been set or not and requests the current Import/Export
    by calling the corresponding EastronSDM630 method.
    Gets called by the ```save_meter_data_task```.

    Returns:
        A string containing all queried meter ID's
    """
    port = choose_port(PORTS_LIST)
    query_time = datetime.today()
    diagnose_str = 'Requested devices on port %s:\n' % port

    if port == 0:
        logger.error('Could not find a serial port with connected meters.')
    else:
        # TODO: Don't query meters, but get active meters for each flat
        for meter in Meter.objects.filter(active=True):
            meter_diagnose_str = 'Slave %d, %s' % (meter.addresse, meter.flat.modus)
            eastron = EastronSDM630(port, meter.addresse)

            # TODO: Check process on how meters are being replaced
            if meter.start_datetime is None:
                meter.set_start_datetime()

            # TODO: Use tenacity in order to handle retries with MAX_RETRIES
            try:
                if meter.flat.modus == 'IM':
                    # TODO: Save L1, L2, L3 instead of total import
                    value = eastron.read_total_import()
                else:
                    value = eastron.read_total_export()

                saved_time = query_time.replace(microsecond=0, second=0)
                value = round(value * 1000) / 1000.0
                meter_data = MeterData(meter_id=meter.pk, saved_time=saved_time, value=value)
                if meter_data.save():
                    meter_diagnose_str += ': saved'
                else:
                    meter_diagnose_str += ': not saved'
            except IOError:
                logger.error('%s: Could not reach meter with address %d' % (datetime.today(), meter.addresse))
                meter_diagnose_str += ': not saved (no communication)'

            diagnose_str += meter_diagnose_str + '\n'

    return diagnose_str


def choose_port(ports):
    meter = Meter.objects.filter(active=True).first()

    for port in ports:
        try:
            eastron = EastronSDM630(port, meter.addresse)
            if eastron.is_reachable():
                return port
        except SerialException:
            logger.error('%s: Port %s not available on meter with address %d'
                         % (datetime.today(), port, meter.addresse))
            break

    return 0
