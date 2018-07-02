from datetime import datetime
from serial.serialutil import SerialException
from backend.eastronSDM630 import EastronSDM630
from mmetering.models import Meter, MeterData
from mmetering_server.settings.defaults import MODBUS_PORT
import logging

logger = logging.getLogger(__name__)
MAX_RETRY = 6


# TODO: Refactor method naming and docstring style
def save_meter_data():
    """
    Loops through a EastronSDM630 object list, checks wether a startdate
    has already been set or not and requests the current Import/Export
    by calling the corresponding EastronSDM630 method

    Returns:
        A string containing all queried meter ID's
    """
    # TODO: Check other ports (current mode is that port is specified in my.cnf)
    port = MODBUS_PORT
    query_time = datetime.today()
    diagnose_str = 'Requested devices on port %s:\n' % port

    # TODO: Don't query meters, but get active meters for each flat
    for meter in Meter.objects.filter(active=True):
        meter_diagnose_str = 'Slave %d, %s' % (meter.addresse, meter.flat.modus)

        try:
            eastron = EastronSDM630(port, meter.addresse)
        except SerialException:
            logger.error('%s: Port %s not available on meter with address %d' % (datetime.today(), port, meter.addresse))

        # TODO: Check process on how meters are being replaced
        if meter.start_datetime is None:
            meter.set_start_datetime()

        # TODO: Use tenacity in order to handle retries with MAX_RETRIES
        value = None
        try:
            if meter.flat.modus == 'IM':
                value = eastron.read_total_import()
            else:
                value = eastron.read_total_export()
        except IOError:
            logger.error('%s: Could not reach meter with address %d' % (datetime.today(), meter.addresse))

        if value is not None:
            saved_time = query_time.replace(microsecond=0, second=0)
            value = round(value * 1000) / 1000.0

            meter_data = MeterData(meter_id=meter.pk, saved_time=saved_time, value=value)
            if meter_data.save():
                meter_diagnose_str += ': saved'
            else:
                meter_diagnose_str += ': not saved'
        else:
            meter_diagnose_str += ': not saved (no communication)'

        diagnose_str += meter_diagnose_str + '\n'

    return diagnose_str

