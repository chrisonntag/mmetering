import logging
from datetime import datetime, timedelta, date
from django.db.models import Sum, Count
from mmetering.models import Flat, Meter, MeterData, Activities
from collections import defaultdict
from itertools import chain
from functools import reduce

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
        meters = [x.pk for x in Meter.objects.filter(flat__modus=mode)]
        values_until = []
        for meter in meters:
            try:
                values_until.append(
                    MeterData.objects.filter(meter__pk=meter, saved_time__lt=until).order_by('-pk')[0].value
                )
            except IndexError:
                logger.info('The requested meter has no values yet.')

        return values_until

    def get_total_consumption(self, until):
        """Queries the total consumption of all meters.

        Args:
            until (datetime): The datetime object up to which will be searched.

        Returns:
            The total consumption from all meters with mode 'IM' in MWh.
        """
        total = self.get_total(until, 'IM')
        return sum(total) / 1000  # convert database kWh values into MWh

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
                'total': self.get_total_consumption(datetime.today()),
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
    NO_DATA = 'keine Daten'

    def get_data(self):
        flats = [x.pk for x in Flat.objects.all().order_by('name')]
        import_values = []
        export_values = []
        consumption = {}
        production = {}

        for flat in flats:
            flat_object = Flat.objects.get(pk=flat)
            meter_data_object = MeterData.objects.filter(
                    meter__flat__pk=flat,
                    saved_time__year=self.end[0].year,
                    saved_time__month=self.end[0].month
            ).order_by('-pk')

            value = {
                'ID': DownloadOverview.NO_DATA,
                'Bezug': DownloadOverview.NO_DATA,
                'SN': DownloadOverview.NO_DATA,
                'Zaehlerstand': DownloadOverview.NO_DATA,
                'Uhrzeit': DownloadOverview.NO_DATA,
            }

            if meter_data_object.exists():
                current_month_exists = True
                meter_data_object = meter_data_object.first()
                value = {
                    'ID': meter_data_object.meter.flat.pk,
                    'Bezug': meter_data_object.meter.flat.name,
                    'SN': meter_data_object.meter.seriennummer,
                    'Zaehlerstand': meter_data_object.value,
                    'Uhrzeit': meter_data_object.saved_time,
                }
            else:
                current_month_exists = False
                flat_object = Flat.objects.get(pk=flat)
                value['ID'] = flat
                value['Bezug'] = flat_object.name

            if flat_object.modus == 'IM':
                if current_month_exists:
                    consumption[flat] = DownloadOverview.get_consumption(flat, self.end[0])
                import_values.append(value)
            else:
                if current_month_exists:
                    production[flat] = DownloadOverview.get_consumption(flat, self.end[0])
                export_values.append(value)

        print("Total consumption-meters in list: %d" % len(consumption))
        print("Export meters: %d" % len(export_values))

        # Calculate the total consumption for each timeslot
        total_consumption = defaultdict(float)
        for flat in consumption:
            for timeslot in consumption[flat]:
                total_consumption[timeslot] += consumption[flat][timeslot]

        # Extend import data
        for i in range(0, len(import_values)):
            pk = import_values[i]['ID']
            meter_value = import_values[i]['Zaehlerstand']
            # TODO: fix this
            try:
                import_values[i].update(self.get_extended_meter_data(pk, total_consumption, production, consumption[pk], meter_value))
            except KeyError:
                logger.info('No data')

        return import_values, export_values

    @staticmethod
    def get_next_value(meter_pk, saved_time):
        next_value = MeterData.objects\
            .filter(meter__flat__pk=meter_pk, saved_time=saved_time + timedelta(minutes=15)).values('saved_time', 'value')
        if len(next_value) > 0:
            return next_value[0]

    @staticmethod
    def get_consumption(meter_pk, timerange):
        time_series = MeterData.objects \
            .filter(meter__flat__pk=meter_pk, saved_time__year=timerange.year, saved_time__month=timerange.month) \
            .values('saved_time', 'value')
        time_series = list(time_series)
        if len(time_series) > 0:
            # Add the first element of the next month in order to get the consumption
            last_item = time_series[len(time_series) - 1]
            time_series.append(DownloadOverview.get_next_value(meter_pk, last_item['saved_time']))

            consumption_series = dict()

            for i in range(0, len(time_series) - 1):
                value = time_series[i]
                delta_value = time_series[i+1]
                # TODO: Check for NoneType
                consumption_series[delta_value['saved_time']] = delta_value['value'] - value['value']

            # Remove the last element
            time_series.pop()
            return consumption_series

    def get_similar_time(self, dictionary, timeslot, threshold=2):
        # TODO: Definitely fix this
        times = 0
        element = None
        while element is None and times < threshold:
            element = dictionary.get(timeslot)
            timeslot = timeslot.replace(minute=timeslot.minute + 1)
            times += 1

        return element

    def get_extended_meter_data(self, pk, total_consumption, production_values, consumption_values, meter_value):
        """
        Gathers further information for a given flat which
        is not contained in a MeterData object.

        :param pk: The pk of the flat.
        :return: A 5-tuple.
        """
        last_month = self.end[0].replace(day=1) - timedelta(days=1)
        last_month_values = MeterData.objects.filter(
            meter__flat__pk=pk,
            saved_time__month=last_month.month,
            saved_time__year=last_month.year).order_by('-saved_time')

        if last_month_values.exists():
            last_month_value = last_month_values.first().value
        else:
            last_month_value = 0

        production_parts = dict.fromkeys(production_values, 0.0)
        consumption = meter_value - last_month_value
        print("Consumption: %f" % consumption)

        for el in consumption_values:
            saved_time = el
            value = consumption_values[el]

            coeff = value / total_consumption[saved_time]
            for meter_id in production_values.keys():
                production_value = self.get_similar_time(production_values.get(meter_id), saved_time)
                if production_value is not None:
                    production_parts[meter_id] += coeff * production_value

        part_distributor = consumption - reduce(lambda x, y: x - y, production_parts.values())
        result = {'Vormonat': last_month_value, 'Verbrauch': consumption, 'Anteil Versorger': part_distributor}
        for key in production_parts.keys():
            name = Flat.objects.get(pk=key).name
            result[name] = production_parts[key]

        print(production_parts)
        return result