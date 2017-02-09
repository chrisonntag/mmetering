import minimalmodbus

from celery.task.schedules import crontab
from celery.task import PeriodicTask

import sys
from datetime import datetime, timedelta
from random import randint
from mmetering.models import Meter, MeterData, Activities
from django.conf import settings

class MeterObject:
    def __init__(self, id, address):
        self.id = id
        self.address = address
        self.connected = False

        if(settings.PRODUCTION):
            # port name, slave address (in decimal)
            self.instrument = minimalmodbus.Instrument('/dev/ttyUSB0', address)

            try:
                # check if we can get the baud rate from the device
                if(self.getHoldingRegister('0x1C', 2) == 3.0):
                    self.connected = True
            except OSError:
                self.connected = False

    def getId(self):
        return self.id

    def getHoldingRegister(self, hex, len):
        return self.getRegister(hex, 3, len)

    def getInputRegister(self, hex, len):
        return self.getRegister(hex, 4, len)

    def getRegister(self, hex, code, len):
        try:
            return self.instrument.read_float(int(hex, 16), functioncode=code, numberOfRegisters=len)
        except (IOError, OSError, ValueError):
            pass
        except StandardError as e:
            print("There has been an error", file=sys.stderr)
            print("Exception: ", exc_info=True, file=sys.stderr)

    def getValue(self):
        if(settings.PRODUCTION):
            return self.getInputRegister('0x48', 2)
        else:
            print("%s: Celery beat is requesting meter data from the device." % datetime.today(), file=sys.stderr)

    def printValue(self):
        print("Verbrauch: {} Wh".format(self.getValue()))


class MeterDataLoaderTask(PeriodicTask):
    run_every = crontab(minute="*/15")#timedelta(seconds=6)#

    def __init__(self):
        self.meters = Meter.objects.filter(flat__modus__exact='IM').values_list('id', 'addresse')
        self.meter_objects = [MeterObject(id, address) for id, address in self.meters]

    def loadData(self):
        if (settings.PRODUCTION):
            for meter in self.meter_objects:
                value = MeterData(meter_id=meter.getId(),
                                  saved_time=datetime.today(),
                                  value=meter.getValue()
                                  )
                value.save()
        else:
            activity = Activities(title="DEBUG: Zählerdaten wurden gespeichert",
                                  text="MeterDataLoaderTask() wurde für %d Zähler ausgelöst. "
                                       "Sie sehen diese Nachricht, da sich MMetering "
                                       "im Debug Modus befindet" % len(self.meter_objects),
                                  timestamp=datetime.today()
                                  )
            activity.save()

    def initNew(self):
        print("s")
        # TODO check for new meters, and set init times

    def run(self):
        self.initNew()
        self.loadData()