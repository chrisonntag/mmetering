import logging
from datetime import datetime, timedelta, date
from django.db.models import Sum, Count
from mmetering.models import Flat, Meter, MeterData, Activities

logger = logging.getLogger(__name__)


class Overview:
    """Offers database queries based on a given filter.

    This class is meant to be a layer between the Django
    database backend and the frontend. It offers several
    methods for representing data to the user.

    Attributes:
        filters (dict): A dictionary defining start and
            end with a datetime object
    """
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
        """Parses a datestring (DD.MM.YYYY) into a datetime object.

        Args:
            string (str): The string which should be parsed.
            end (bool): Will set the time to 23:59:59 if True, and
                to 00:00:00 otherwise.

        Returns:
            The parsed datetime object.

        Raises:
            ValueError: If the datestring is not in the desired format
        """
        try:
            raw = list(map(int, string.split('.')))
            if raw[2] > 1000 and 1 <= raw[1] <= 12 and 1 <= raw[0] <= 31:
                if not end:
                    return datetime(raw[2], raw[1], raw[0], 0, 0, 0, 0)
                else:
                    return datetime(raw[2], raw[1], raw[0], 23, 59, 59, 0)
            else:
                raise ValueError('Days should be between 1 and 31 and months between 1 and 12.')
        except ValueError:
            logger.warning('Expected string format is DD.MM.YYYY. I got %s' % string)

    def get_data_range(self, start, end, mode):
        """Queries the summed up meter values per quarter-hour in a timespan.

        Args:
             start (datetime): The start of the timespan.
             end (datetime): The end of the timespan.
             mode (str): The desired mode of MeterData values,
                'IM' for Import data and
                'EX' for Export data.

        Returns:
            A QuerySet of sum of pairs of value_sum and saved_time::
                [{
                    'value_sum': Sum of all meters of type ``mode`` in Wh,
                    'saved_time': Time of the values
                }, ...
                ]
        """
        data = MeterData.objects.all() \
            .filter(
            meter__active=True,
            meter__flat__modus__exact=mode,
            saved_time__range=[start, end]
        ) \
            .values('saved_time') \
            .annotate(value_sum=Sum('value') * 1000)  # displays data in Wh, DB values are in kWh
        return data

    def get_total(self, until, mode):
        """Queries the total consumption/supply for each meter until a date.

        Args:
            until (datetime): The datetime object up to which will be searched.
            mode (str): The meters mode ('IM': Import, 'EX': Export).

        Returns:
            A list of summed up values, each representing a meter.

        """
        active_meters_num = Meter.objects.filter(active=True, flat__modus__exact=mode).count()
        total = MeterData.objects.all() \
            .filter(meter__flat__modus__exact=mode, saved_time__lt=until, meter__active=True) \
            .values_list('value').order_by('-value')[:active_meters_num]

        # get the first value of each tuple
        return [x[0] for x in total]

    def get_total_consumption(self, until):
        """Queries the total consumption of all meters.

        Args:
            until (datetime): The datetime object up to which will be searched.

        Returns:
            The total consumption from all meters with mode 'IM' in MWh.
        """
        total = self.get_total(until, 'IM')
        return sum(total) / 1000  # /1000 convert to MWh

    def get_day_consumption(self, until):
        """Queries the total consumption in 24h.

        Args:
            until (datetime): The datetime from which to query the last 24h.

        Returns:
            The total consumption of the last 24h from all meters with
            mode 'IM' in kWh.
        """
        day = self.get_total(until, 'IM')
        day_before = self.get_total(until - timedelta(days=1), 'IM')

        return sum(day) - sum(day_before)

    def is_supply_over_threshold(self, threshold: float):
        """Checks if self-produced energy supply is over a specific threshold.

        Args:
            threshold: The threshold to check on.

        Returns:
            True if the total of the self-produced energy supply is over
            the threshold, False otherwise or when no data is available.
        """
        c_data = self.get_data_range(self.times['now-1'], datetime.today(), 'IM').order_by('-value_sum')[:2]
        s_data = self.get_data_range(self.times['now-1'], datetime.today(), 'EX').order_by('-value_sum')[:2]

        if c_data and s_data:
            try:
                consumption = c_data[0].get('value_sum') - c_data[1].get('value_sum')
                supply = s_data[0].get('value_sum') - s_data[1].get('value_sum')
            except IndexError:
                logging.warning('Not enough data for checking if own supply is over a threshold.')
                return False

            if supply >= consumption * threshold:
                return True
            else:
                return False

        return False


class LoadProfileOverview(Overview):
    """Derives from Overview and offers a ```to_dict``` method in order
    to pass consumption and supply values to the frontend's Load Profile view.
    """
    def to_dict(self):
        return {
            'consumption': self.get_data_range(self.timerange[0], self.timerange[1], 'IM'),
            'supply': self.get_data_range(self.timerange[0], self.timerange[1], 'EX')
        }


class DataOverview(Overview):
    """Derives from Overview and offers a ```to_dict``` method in oder
    to pass data values to the frontend's Overview Panel.
    """
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
    """Derives from Overview and offers a ```get_data``` method in order
    to offer meter data values for the Download Sheet.
    """
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
