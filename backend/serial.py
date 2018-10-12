from datetime import datetime
from serial.serialutil import SerialException
from backend.eastronSDM630 import EastronSDM630
from mmetering.models import Meter, MeterData
from mmetering_server.settings.defaults import MODBUS_PORT
import serial.tools.list_ports
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)
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
    query_time = datetime.today().replace(microsecond=0, second=0)
    diagnose_str = 'Requested devices on port %s:\n' % port

    if port == 0:
        diagnose_str = 'Could not find a serial port with connected meters.'
        return diagnose_str
    else:
        for meter in Meter.objects.filter(active=True):
            meter_diagnose_str = 'Slave %d, %s' % (meter.addresse, meter.flat.modus)
            try:
                eastron = EastronSDM630(port, meter.addresse)
            except SerialException:
                logger.error('Port %s not available on meter with address %d' % (port, meter.addresse))
                continue

            if meter.start_datetime is not None:
                if meter.start_datetime > query_time:
                    # start_datetime is in the future, don't query this meter
                    continue
            else:
                meter.set_start_datetime()

            if meter.end_datetime is not None:
                if meter.end_datetime <= query_time:
                    meter.deactivate()

            # TODO: Use tenacity in order to handle retries with MAX_RETRIES
            try:
                if meter.flat.modus == 'IM':
                    value = eastron.read_total_import()
                    value_l1 = eastron.read_import_L1()
                    value_l2 = eastron.read_import_L2()
                    value_l3 = eastron.read_import_L3()
                else:
                    value = eastron.read_total_export()
                    value_l1 = eastron.read_export_L1()
                    value_l2 = eastron.read_export_L2()
                    value_l3 = eastron.read_export_L3()

                meter_data = MeterData(
                    meter_id=meter.pk,
                    saved_time=query_time,
                    value=value,
                    value_l1=value_l1,
                    value_l2=value_l2,
                    value_l3=value_l3
                )
                if meter_data.save():
                    meter_diagnose_str += ': saved'
                else:
                    meter_diagnose_str += ': not saved'
            except IOError:
                logger.exception('%s: Could not reach meter with address %d' % (datetime.today(), meter.addresse))
                meter_diagnose_str += ': not saved (no communication)'

            diagnose_str += meter_diagnose_str + '\n'

        return diagnose_str


def choose_port(ports):
    meter = Meter.objects.filter(active=True).first()

    if meter is None:
        logger.error('There are no active meters registered in the database.')
        return 0

    for port in ports:
        try:
            eastron = EastronSDM630(port, meter.addresse)
            if eastron.is_reachable():
                return port
        except SerialException:
            logger.error('%s: Port %s not available on meter with address %d'
                         % (datetime.today(), port, meter.addresse))
            continue

    return 0
