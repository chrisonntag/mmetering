from __future__ import absolute_import
from datetime import datetime, timedelta
from random import randint

from celery.task.schedules import crontab
from celery.task import PeriodicTask
from celery.decorators import periodic_task
from mmetering.models import Meter, TestMeterData

class MeterObject:
    def __init__(self, id, address):
        self.id = id
        self.address = address
        # self.instrument = minimalmodbus.Instrument('/dev/ttyUSB0', address)  # port name, slave address (in decimal)
        # logging.debug("Connecting to Modbus device")
        # logging.debug(self.instrument)

    def getId(self):
        return self.id

    def getValue(self):
        return randint(110, 450)
        """
        while True:
            try:
              return self.instrument.read_float(int('0x48', 16), functioncode=4, numberOfRegisters=2)
            except (IOError, OSError, ValueError):
              continue
            except StandardError, e:
              logging.error("There has been an error")
              logging.error("Exception: ", exc_info=True)
            break
        """

    def printValue(self):
        print("Verbrauch: {} Wh".format(self.getValue()))


class MeterDataLoaderTask(PeriodicTask):
    run_every = crontab(minute="*/15")#timedelta(seconds=6)#

    def __init__(self):
        self.meters = Meter.objects.filter(flat__modus__exact='IM').values_list('id', 'addresse')
        self.meter_objects = [MeterObject(id, address) for id, address in self.meters]

    def loadData(self):
        for meter in self.meter_objects:
            value = TestMeterData(meter_id=meter.getId(),
                                  saved_time=datetime.today(),
                                  value=meter.getValue()
                                  )
            value.save()

    def run(self):
        self.loadData()