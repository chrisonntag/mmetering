import sys
import minimalmodbus
from django.conf import settings
from datetime import datetime, timedelta
from mmetering.models import Meter, MeterData, Activities

def save_meter_data():
  """
  Converts database objects into virtual meter
  objects (see VMeter class)
  """
  meter_IM = get_meter_objects('IM')
  meter_EX = get_meter_objects('EX')

  meter_objects_IM = [VMeter(id, address, start, end, 'IM') for id, address, start, end in meter_IM]
  meter_objects_EX = [VMeter(id, address, start, end, 'EX') for id, address, start, end in meter_EX]

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

def saveValue(id, datetime, val):
  """
  Saves a given value and datetime in a django model
  :param id:
  :param datetime:
  :param val:
  """
  value = MeterData(meter_id=id, saved_time=datetime, value=val)
  value.save()

def loadData(objects):
  """
  Loops through a VMeter object list, checks wether a startdate
  has already been set or not and requests the current Import/Export
  by calling VMeters getValue() method
  :param objects:
  """
  for meter in objects:
    if meter.getStart() is None:
      updateStartDate(meter.getId())

    value = None
    try:
      value = meter.getValue()
    except RuntimeError:
      print("There has been an error", file=sys.stderr)
      print("Exception: ", exc_info=True, file=sys.stderr)

    if value is not None:
      saveValue(meter.getId(), datetime.today().replace(microsecond=0, second=0), round(value*1000) / 1000.0)

class VMeter(object):
  """
  Represents a physical Modbus meter (Eastron SDM630)
  """
  def __init__(self, id, address, start, end, modus):
    self.id = id
    self.address = address
    self.start = start
    self.end = end
    self.modus = modus

    if (settings.PRODUCTION):
      # port name, slave address (in decimal)
      self.instrument = minimalmodbus.Instrument('/dev/ttyUSB0', address)
      self.instrument.serial.timeout = 3.0  # sec

  def getId(self):
    return self.id

  def getAddress(self):
    return self.address

  def getModus(self):
    return self.modus

  def getStart(self):
    return self.start

  def getEnd(self):
    return self.end

  def getHoldingRegister(self, hexc, length):
    return self.getRegister(hexc, 3, length)

  def getInputRegister(self, hexc, length):
    return self.getRegister(hexc, 4, length)

  def getRegister(self, hexc, code, length):
    try:
      return self.instrument.read_float(int(hexc, 16), functioncode=code, numberOfRegisters=length)
    except (IOError, OSError, ValueError):
      self.getRegister(hexc, code, length)
    except RuntimeError:
      print("There has been an error", file=sys.stderr)
      print("Exception: ", exc_info=True, file=sys.stderr)

  def getValue(self):
    if (settings.PRODUCTION):
      if self.modus is 'EX':
        return self.getInputRegister('0x4A', 2)
      else:
        return self.getInputRegister('0x48', 2)
    else:
      print("%s: Celery beat is requesting meter data from the device with address %d" % (datetime.today(), self.getAddress()),
            file=sys.stdout)

  def printValue(self):
    print("Verbrauch: {} Wh".format(self.getValue()))
