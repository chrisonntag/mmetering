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


  def parseDate(self, string):
    """Converts Datestring(MM/DD/YYYY) into date object."""
    try:
      raw = list(map(int, string.split('/')))
      return datetime(raw[2], raw[0], raw[1], 0, 0, 0, 0)
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
      saved_time__range=[
        start,
        end
      ]
    ) \
      .values('saved_time') \
      .annotate(
      value_sum=Sum('value')
    )
    return data

class LoadProfileOverview(Overview):
  def to_dict(self):
    return {
      'data': self.getDataRange(self.timerange[0], self.timerange[1])
    }