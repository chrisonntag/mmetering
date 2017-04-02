import sys
from backend.eastronSDM630 import EastronSDM630
from datetime import datetime, timedelta
from mmetering.models import Meter, MeterData, Activities

def save_meter_data():
  """
  Converts database objects into virtual meter
  objects (see EastronSDM630 class)
  """
  meter_IM = get_meter_objects('IM')
  meter_EX = get_meter_objects('EX')

  meter_objects_IM = [EastronSDM630(id, address, start, end, 'IM') for id, address, start, end in meter_IM]
  meter_objects_EX = [EastronSDM630(id, address, start, end, 'EX') for id, address, start, end in meter_EX]

  loadData(meter_objects_IM)
  loadData(meter_objects_EX)

  return_string = "Requested devices:\n"
  for meter in meter_objects_IM + meter_objects_EX:
    return_string += "%s%d, " % (meter.getModus(), meter.getAddress())

  return return_string

def get_meter_objects(modus):
  """
  Returns all active meter django objects with
  corresponding modus
  :param modus:
  :return:
  """
  return Meter.objects\
    .filter(flat__modus__exact=modus, active=True)\
    .values_list('id',
                 'addresse',
                 'start_datetime',
                 'end_datetime'
                 )

def updateStartDate(id):
  """
  Updates a meter models startdate field
  :param id:
  """
  meter = Meter.objects.get(pk=id)
  meter.start_datetime = datetime.today()
  meter.save()

def saveValue(id, cur_datetime, val):
  """
  Saves a given value and datetime in a django model
  :param id:
  :param datetime:
  :param val:
  """
  value = MeterData(meter_id=id, saved_time=cur_datetime, value=val)
  value.save()
  print("%s: Saved device with meter id %d" % (cur_datetime, id), file=sys.stdout)

def loadData(objects):
  """
  Loops through a EastronSDM630 object list, checks wether a startdate
  has already been set or not and requests the current Import/Export
  by calling EastronSDM630s getValue() method
  :param objects:
  """
  for meter in objects:
    if meter.getStart() is None:
      updateStartDate(meter.getId())

    value = None
    try:
      value = meter.getValue()
      print("%s: Got %s on address %d (ID %d)" % (datetime.today(), str(value), meter.getAddress(), meter.getId()), file=sys.stdout)
    except RuntimeError:
      print("There has been an error", file=sys.stderr)
      print("Exception: ", exc_info=True, file=sys.stderr)

    if value is not None:
      saveValue(meter.getId(), datetime.today().replace(microsecond=0, second=0), round(value*1000) / 1000.0)