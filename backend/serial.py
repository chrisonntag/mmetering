from datetime import datetime

from backend.eastronSDM630 import EastronSDM630
from mmetering.models import Meter, MeterData
import logging

logger = logging.getLogger(__name__)

# TODO: Refactor method naming and docstring style

def save_meter_data():
    """
    Converts database objects into virtual meter
    objects (see EastronSDM630 class)
    """
    # TODO: Don't query meters, but get active meters for each flat
    import_meters = get_meter_objects('IM')
    export_meters = get_meter_objects('EX')

    # TODO: Catch SerialException here if port is busy and/or not available (maybe send mail)
    # TODO: Check other ports (current mode is that port is specified in my.cnf)
    import_meter_objects = [EastronSDM630(id, address, start, end, 'IM') for id, address, start, end in import_meters]
    export_meter_objects = [EastronSDM630(id, address, start, end, 'EX') for id, address, start, end in export_meters]

    load_data(import_meter_objects)
    load_data(export_meter_objects)

    return_string = "Requested devices:\n"
    for meter in import_meter_objects + export_meter_objects:
        return_string += "%s%d, " % (meter.get_modus(), meter.get_address())

    return return_string


def get_meter_objects(modus):
    """
    Returns all active meter django objects with
    corresponding modus
    :param modus:
    :return:
    """
    return Meter.objects \
        .filter(flat__modus__exact=modus, active=True) \
        .values_list('id',
                     'addresse',
                     'start_datetime',
                     'end_datetime'
                     )


def update_start_date(id):
    """
    Updates a meter models startdate field
    :param id: a meters unique id
    """
    meter = Meter.objects.get(pk=id)
    meter.start_datetime = datetime.today()
    meter.save()


def save_value(id, cur_datetime, val):
    """
    Saves a given value and datetime in a django model
    :param id: a meters unique id
    :param cur_datetime: current datetime (datetime.datetime object)
    :param val: the meter reading
    """
    value = MeterData(meter_id=id, saved_time=cur_datetime, value=val)
    value.save()
    logger.debug("%s: Saved device with meter id %d" % (cur_datetime, id))


def load_data(objects):
    """
    Loops through a EastronSDM630 object list, checks wether a startdate
    has already been set or not and requests the current Import/Export
    by calling EastronSDM630s get_value() method
    :param objects: list of instances of the EastronSDM630 class
    """
    for meter in objects:
        if meter.get_start() is None:
            update_start_date(meter.get_id())

        value = meter.get_value()
        logger.debug("%s: Got %s on address %d (ID %d)" %
                     (datetime.today(), str(value), meter.get_address(), meter.get_id()))

        # TODO: Catch IOError here if communication is not possible (no answer)
        if value is not None:
            # TODO: Maybe set datetime.minute hard in order to prevent deviations (check summary workaround)
            save_value(meter.get_id(), datetime.today().replace(microsecond=0, second=0), round(value * 1000) / 1000.0)
