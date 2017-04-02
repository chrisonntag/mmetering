"""
Driver for the Eastron SDM630 metering device, for communication via the Modbus RTU protocol.
"""

import sys
import minimalmodbus
from datetime import datetime
from django.conf import settings

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

    if (settings.PRODUCTION):
      # port name, slave address (in decimal)
      minimalmodbus.Instrument.__init__(self, '/dev/ttyUSB0', address)
      self.serial.timeout = 6.0  # sec

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
    while True:
      try:
        val = self.read_float(int(hexc, 16), functioncode=code, numberOfRegisters=length)
        if val is not None:
          return val
      except (IOError, OSError, ValueError):
        continue
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
