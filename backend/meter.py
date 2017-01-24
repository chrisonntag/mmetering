import minimalmodbus
import logging
import datetime


# more information: https://docs.python.org/3.6/howto/logging.html
# logging.basicConfig(filename='log/mmetering-debug-{:%Y%m%d%H%M%S}.log'.format(datetime.datetime.now()),level=logging.DEBUG)

class Meter:
  def __init__(self, id, address):
    self.id = id
    self.address = address
    self.lastUpdate = "None"

    self.instrument = minimalmodbus.Instrument('/dev/ttyUSB0', address)  # port name, slave address (in decimal)
    logging.debug("Connecting to Modbus device")
    logging.debug(self.instrument)

  def getId(self):
    return self.id

  def getValue(self):
    while True:
      try:
        return self.instrument.read_float(int('0x48', 16), functioncode=4, numberOfRegisters=2)
      except (IOError, OSError, ValueError):
        continue
      except StandardError, e:
        logging.error("There has been an error")
        logging.error("Exception: ", exc_info=True)
      break

  def printValue(self):
    while True:
      try:
        value = self.instrument.read_float(int('0x48', 16), functioncode=4, numberOfRegisters=2)
        print("Verbrauch: {} kWh".format(value))
      except (IOError, OSError, ValueError):
        continue
      except StandardError, e:
        logging.error("There has been an error")
        logging.error("Exception: ", exc_info=True)
      break

