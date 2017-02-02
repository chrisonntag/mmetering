import logging
from datetime import datetime, timedelta, date
from django.db.models import Max, Sum, Count, F, Avg, Q
from mmetering.models import Flat, Meter, MeterData

class Overview:
  def __init__(self, filters):
    self._filters = filters
    self.times = {
      'now': datetime.now(),
      'now-24': datetime.now() - timedelta(hours=24),
      'today': date.today(),
      'yesterday': date.today() - timedelta(days=1),
      'current_week': (date.today() - timedelta(days=7), date.today()),
      'last_week': (date.today() - timedelta(days=14), date.today() - timedelta(days=7)),
      'current_month': (date.today() - timedelta(days=30), date.today()),
      'last_month': (date.today() - timedelta(days=60), date.today() - timedelta(days=30))
    }
    start = [self.parseDate(self._filters['start']) if 'start' in self._filters else self.times['now-24']]
    end = [self.parseDate(self._filters['end']) if 'end' in self._filters else self.times['now']]
    self.timerange = start + end
    # TODO check for start==end

    self.flats = Flat.objects.all()


  def parseDate(self, string):
    """Converts Datestring(MM/DD/YYYY) into date object."""
    try:
      raw = list(map(int, string.split('.')))
      return datetime(raw[2], raw[1], raw[0], 0, 0, 0, 0)
    except:
      logging.error("Expected string format is MM/DD/YYYY. I got %s" % string)

  def is_empty(structure):
    if structure:
      return False
    else:
      return True

  def getDataRange(self, start, end):
    data = MeterData.objects.all() \
      .filter(
        meter__flat__modus__exact='IM',
        saved_time__range=[start, end]
      ) \
      .values('saved_time') \
      .annotate(value_sum=Sum('value'))
    return data

  def getTotal(self, until):
    total_splitted = MeterData.objects.all() \
      .filter(meter__flat__modus__exact='IM', saved_time__lt=until) \
      .values('meter_id') \
      .annotate(max_value=Sum('value')).order_by() \
      .values_list('max_value')

    total = []
    for flat in total_splitted:
      total.append(flat[0])

    return total

  def getTotalConsumption(self, until):
    total = self.getTotal(until)
    return sum(total) / 1000 / 1000 # /1000 convert to MwH

  def getAverageConsumption(self, until):
    total = self.getTotal(until)
    if not total:
      return sum(total)/len(total) / 1000
    else:
      return 0

class LoadProfileOverview(Overview):
  def to_dict(self):
    return {
      'data': self.getDataRange(self.timerange[0], self.timerange[1])
    }

class DataOverview(Overview):
  def to_dict(self):
    return {
      'consumers': Flat.objects.filter(modus='IM').aggregate(num=Count('name')),
      'suppliers': Flat.objects.filter(modus='EX').aggregate(num=Count('name')),
      'consumption': {
        'total': self.getTotalConsumption(date.today()),
        'total_last_week': self.getTotalConsumption(self.times['last_week'][1]),
        'unit': 'MWh'
      },
      'time': {
        'day_low': self.getDataRange(self.times['yesterday'], self.times['today']).values('saved_time').order_by('value_sum').first(),
        'day_high': self.getDataRange(self.times['yesterday'], self.times['today']).values('saved_time').order_by('-value_sum').first(),
      },
      'average': {
        'current': self.getAverageConsumption(self.times['today']),
        'last': self.getAverageConsumption(self.times['yesterday']),
        'unit': 'kWh'
      }
    }

class CSVResponse:
  def getData(self):
    total_splitted = MeterData.objects.all() \
      .filter(meter__flat__modus__exact='IM', saved_time__lt=datetime.today()) \
      .values_list('meter_id', 'saved_time', 'value')

    total = []
    for flat in total_splitted:
      total.append(flat)

    return total