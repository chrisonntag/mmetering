import logging
from datetime import datetime, timedelta, date

from django.db.models import Sum, Count

from mmetering.models import Flat, Meter, MeterData, Activities

logger = logging.getLogger(__name__)


class Overview:
    def __init__(self, filters):
        self._filters = filters
        self.times = {
            'now': datetime.now(),
            'now-24': datetime.now() - timedelta(hours=24),
            'now-1': datetime.now() - timedelta(hours=1),
            'today': date.today(),
            'yesterday': date.today() - timedelta(days=1),
            'current_week': (date.today() - timedelta(days=7), date.today()),
            'last_week': (date.today() - timedelta(days=14), date.today() - timedelta(days=7)),
            'current_month': (date.today() - timedelta(days=30), date.today()),
            'last_month': (date.today() - timedelta(days=60), date.today() - timedelta(days=30))
        }
        if self._filters is not None:
            self.start = [self.parse_date(self._filters['start'], False) if 'start' in self._filters else self.times['now-24']]
            self.end = [self.parse_date(self._filters['end'], True) if 'end' in self._filters else self.times['now']]
            self.timerange = self.start + self.end
            # TODO check for start==end

        self.flats = Flat.objects.all()

    @staticmethod
    def parse_date(string, end):
        """Converts Datestring(DD.MM.YYYY) into date object."""
        try:
            raw = list(map(int, string.split('.')))
            if not end:
                return datetime(raw[2], raw[1], raw[0], 0, 0, 0, 0)
            else:
                return datetime(raw[2], raw[1], raw[0], 23, 59, 59, 0)
        except RuntimeError:
            logger.warning("Expected string format is DD.MM.YYYY. I got %s" % string)

    def get_data_range(self, start, end, mode):
        data = MeterData.objects.all() \
            .filter(
            meter__flat__modus__exact=mode,
            saved_time__range=[start, end]
        ) \
            .values('saved_time') \
            .annotate(value_sum=Sum('value') * 1000)  # displays data in Wh, DB values are in kWh
        return data

    def get_total(self, until, mode):
        active_meters = Meter.objects.filter(active=True, flat__modus__exact=mode).count()
        total = MeterData.objects.all() \
            .filter(meter__flat__modus__exact=mode, saved_time__lt=until, meter__active=True) \
            .values_list('value').order_by('-value')[:active_meters]

        # get the first value of each tuple
        return [x[0] for x in total]

    def get_total_consumption(self, until):
        total = self.get_total(until, 'IM')
        return sum(total) / 1000  # /1000 convert to MwH

    def get_day_consumption(self, until):
        day = self.get_total(until, 'IM')
        day_before = self.get_total(until - timedelta(days=1), 'IM')

        return sum(day) - sum(day_before)

    def is_supply_over_threshold(self, threshold):
        c_data = self.get_data_range(self.times['now-1'], datetime.today(), 'IM').order_by('-value_sum')[:2]
        s_data = self.get_data_range(self.times['now-1'], datetime.today(), 'EX').order_by('-value_sum')[:2]

        print(c_data)
        print(s_data)

        if c_data and s_data:
            consumption = c_data[0].get('value_sum') - c_data[1].get('value_sum')
            supply = s_data[0].get('value_sum') - s_data[1].get('value_sum')

            if supply >= consumption * threshold:
                return True
            else:
                return False

        return False


class LoadProfileOverview(Overview):
    def to_dict(self):
        return {
            'consumption': self.get_data_range(self.timerange[0], self.timerange[1], 'IM'),
            'supply': self.get_data_range(self.timerange[0], self.timerange[1], 'EX')
        }


class DataOverview(Overview):
    def to_dict(self):
        return {
            'consumers': Flat.objects.filter(modus='IM').aggregate(num=Count('name')),
            'active_consumers': Meter.objects.filter(flat__modus='IM', active=True).aggregate(num=Count('addresse')),
            'suppliers': Flat.objects.filter(modus='EX').aggregate(num=Count('name')),
            'active_suppliers': Meter.objects.filter(flat__modus='EX', active=True).aggregate(num=Count('addresse')),
            'consumption': {
                'total': self.get_total_consumption(date.today()),
                'total_last_week': self.get_total_consumption(self.times['last_week'][1]),
                'unit': 'MWh'
            },
            'time': {
                'day_low': self.get_data_range(self.times['yesterday'], self.times['today'], 'IM').values(
                    'saved_time').order_by('value_sum').first(),
                'day_high': self.get_data_range(self.times['yesterday'], self.times['today'], 'IM').values(
                    'saved_time').order_by('-value_sum').first(),
            },
            'day': {
                'current': self.get_day_consumption(self.times['today']),
                'last': self.get_day_consumption(self.times['yesterday']),
                'unit': 'kWh'
            },
            'activities': Activities.objects.all().order_by('-timestamp')[:6]
        }


class DownloadOverview(Overview):
    def get_data(self):
        num_of_meters = Meter.objects.filter(active=True).count()
        total_splitted = MeterData.objects\
            .filter(meter__active=True, saved_time__lte=self.end[0])\
            .values_list('meter__seriennummer', 'meter__flat__name', 'value', 'saved_time')\
            .order_by('-saved_time')[num_of_meters:num_of_meters * 2]

        total = []
        for flat in total_splitted:
            total.append(flat)

        return total
