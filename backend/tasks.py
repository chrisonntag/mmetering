import minimalmodbus

from celery.task.schedules import crontab
from celery.task import PeriodicTask

import sys
from datetime import datetime, timedelta
from random import randint
from mmetering.models import Meter, MeterData, Activities
from django.conf import settings


class MeterObject:
  def __init__(self, id, address, start, end, modus):
    self.id = id
    self.address = address
    self.start = start
    self.end = end
    self.modus = modus
    self.connected = False

    if (settings.PRODUCTION):
      # port name, slave address (in decimal)
      self.instrument = minimalmodbus.Instrument('/dev/ttyUSB0', address)
      self.instrument.serial.timeout = 3.0 #sec

      try:
        # check if we can get the baud rate from the device
        if (self.getHoldingRegister('0x1C', 2) == 3.0):
          self.connected = True
      except OSError:
        self.connected = False

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
      if self.modus == 'EX':
        return self.getInputRegister('0x4A', 2)
      else:
        return self.getInputRegister('0x48', 2)
    else:
      print("%s: Celery beat is requesting meter data from the device with address %d" % (datetime.today(), self.getAddress()),
            file=sys.stdout)

  def printValue(self):
    print("Verbrauch: {} Wh".format(self.getValue()))


class MeterDataLoaderTask(PeriodicTask):
  run_every = crontab(minute="*/15")  #timedelta(seconds=6)#

  def __init__(self):
    self.meters_IM = Meter.objects.filter(flat__modus__exact='IM', active=True).values_list('id',
                                                                                            'addresse',
                                                                                            'start_datetime',
                                                                                            'end_datetime')
    self.meters_EX = Meter.objects.filter(flat__modus__exact='EX', active=True).values_list('id',
                                                                                            'addresse',
                                                                                            'start_datetime',
                                                                                            'end_datetime')
    self.meter_objects_IM = [MeterObject(id, address, start, end, 'IM') for id, address, start, end in self.meters_IM]
    self.meter_objects_EX = [MeterObject(id, address, start, end, 'EX') for id, address, start, end in self.meters_EX]

  def updateStartDate(self, id):
    meter = Meter.objects.get(pk=id)
    meter.start_datetime = datetime.today()
    meter.save()

  def saveValue(self, id, datetime, val):
    value = MeterData(meter_id=id, saved_time=datetime, value=val)
    value.save()

  def loadData(self, objects):
    for meter in objects:
      if meter.getStart() is None:
        self.updateStartDate(meter.getId())

      value = None
      try:
        value = meter.getValue()
      except RuntimeError:
        print("There has been an error", file=sys.stderr)
        print("Exception: ", exc_info=True, file=sys.stderr)

      if value is not None:
        self.saveValue(meter.getId(), datetime.today(), value)

  def run(self):
    self.loadData(self.meter_objects_IM)
    self.loadData(self.meter_objects_EX)