import logging
from datetime import datetime, timedelta, date
from django.db.models import Sum, Count
from mmetering.models import Flat, Meter, MeterData, Activities
from collections import defaultdict
from calendar import monthrange
from itertools import chain
from functools import reduce

logger = logging.getLogger(__name__)


def round_time_quarterly(dt=None, roundTo=900):
    """Round a datetime object to any time lapse in seconds

    Args:
        dt: datetime.datetime object, default now.
        roundTo : Closest number of seconds to round to, default 15 minutes.
    """
    if dt is None:
        dt = datetime.now()

    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = (seconds + roundTo / 2) // roundTo * roundTo
    return dt + timedelta(0, rounding-seconds, -dt.microsecond)


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
            'now': round_time_quarterly(datetime.now()),
            'now-24': round_time_quarterly(datetime.now() - timedelta(hours=24)),
            'now-1': round_time_quarterly(datetime.now() - timedelta(hours=1)),
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

    def perdelta(self, start, end, delta):
        curr = start
        while curr <= end:
            yield curr
            curr += delta

    def get_data_range(self, start, end, mode):
        """Queries the summed up meter values per quarter-hour in a timespan.

        Args:
             start (datetime): The start of the timespan.
             end (datetime): The end of the timespan.
             mode (str): The desired mode of MeterData values,
                'IM' for Import data and
                'EX' for Export data.

        Returns:
            A list of sum of pairs of value_sum and saved_time::
                [{
                    'value_sum': Sum of all meters of type ``mode`` in Wh,
                    'saved_time': Time of the values
                }, ...
                ]
        """
        data = []
        for slot in self.perdelta(start, end, timedelta(minutes=15)):
            meter_data = MeterData.objects.filter(
                meter__flat__modus__exact=mode,
                saved_time=slot
            ).values('value')
            meter_data = [x['value'] * 1000 for x in meter_data]  # DB values are in kWh, output should be Wh (*1000)
            value_sum = sum(meter_data)
            if len(data) > 0:
                if value_sum >= data[-1]['value_sum']:
                    data.append({'saved_time': slot, 'value_sum': value_sum})
                else:
                    # Some values are missing in this timeslot.
                    # Set value_sum to the last valid value in order to be displayed as 0.0 consumption.
                    data.append({'saved_time': slot, 'value_sum': data[-1]['value_sum']})
            else:
                data.append({'saved_time': slot, 'value_sum': value_sum})

        return data

    def get_consumption_range(self, data_range):
        data = []
        for i in range(1, len(data_range)):
            slot_prev = data_range[i - 1]
            slot = data_range[i]
            data.append({'saved_time': slot['saved_time'], 'value_sum': slot['value_sum'] - slot_prev['value_sum']})

        return data

    def get_consumption_extremes(self, start, end, mode):
        data_range = self.get_data_range(start, end, mode)
        consumption = self.get_consumption_range(data_range)

        # Remove 0.0 consumption values due to possibly missing values
        consumption = [x for x in consumption if x['value_sum'] > 0]

        if len(consumption) > 0:
            sorted_consumption = sorted(consumption, key=lambda k: k['value_sum'])
            return sorted_consumption[0], sorted_consumption[-1]
        else:
            dummy = {'saved_time': datetime(1997, 2, 4, 0, 0), 'value_sum': 0}
            return dummy, dummy

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
        consumption_range = self.get_consumption_range(self.get_data_range(self.times['now-1'], datetime.today(), 'IM'))
        supply_range = self.get_consumption_range(self.get_data_range(self.times['now-1'], datetime.today(), 'EX'))

        if len(consumption_range) > 0 and len(supply_range) > 0:
            consumption = sorted(consumption_range, key=lambda k: k['saved_time'])[-1]['value_sum']
            supply = sorted(supply_range, key=lambda k: k['saved_time'])[-1]['value_sum']

            if supply >= consumption * threshold:
                return True
            else:
                return False
        else:
            logging.warning('Not enough data for checking if own supply is over %d percent.' % (threshold * 100))
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
        day_low, day_high = self.get_consumption_extremes(self.times['now-24'], self.times['now'], 'IM')

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
                'day_low': day_low,
                'day_high': day_high
            },
            'day': {
                'current': self.get_day_consumption(self.times['today']),
                'last': self.get_day_consumption(self.times['yesterday']),
                'unit': 'kWh'
            },
            'meter_states': Meter.objects.filter(active=True).order_by('addresse').values('flat__name', 'seriennummer', 'addresse', 'available'),
            'activities': Activities.objects.all().order_by('-timestamp')[:6]
        }


class DownloadOverview(Overview):
    """Derives from Overview and offers a ```get_data``` method in order
    to offer meter data values for the Download Sheet.
    """
    NO_DATA = 'keine Daten'

    def get_data(self):
        """Cycles through all flats and its registered meters in order to get
        meter data for each flat.

        Returns:
            The requested month and two lists of dictionaries containing key-value pairs as initialized
            in the first for-loop and expanded by get_extended_meter_data.
        """
        flats = [x.pk for x in Flat.objects.all().order_by('name')]
        import_values = []
        export_values = []
        consumption = {}
        production = {}

        for flat in flats:
            flat_object = Flat.objects.get(pk=flat)
            meter_data_objects = MeterData.objects.filter(
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

            if meter_data_objects.exists():
                current_month_exists = True
                meter_data_object = meter_data_objects.first()
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
                    value['fehlende Werte'] = self.get_missing_data_points(meter_data_objects)
                import_values.append(value)
            else:
                if current_month_exists:
                    production[flat] = DownloadOverview.get_consumption(flat, self.end[0])
                    value['fehlende Werte'] = self.get_missing_data_points(meter_data_objects)
                export_values.append(value)

        # Calculate the total consumption for each timeslot
        total_consumption = defaultdict(float)
        for flat in consumption:
            for timeslot in consumption[flat]:
                total_consumption[timeslot] += consumption[flat][timeslot]

        # Extend import data
        for i in range(0, len(import_values)):
            pk = import_values[i]['ID']
            meter_value = import_values[i]['Zaehlerstand']
            # TODO: fix program control through exception handling
            try:
                import_values[i].update(self.get_extended_meter_data(pk, total_consumption, production, consumption[pk], meter_value))
            except KeyError:
                logger.warning('No data available.')

        return self.end[0].strftime('%b'), import_values, export_values

    def get_missing_data_points(self, meter_data_objects):
        """Gets the number of missing data points for the selected month

        Args:
            meter_data_objects: The meter data objects for the selected month.

        Returns:
            The number of missing values.
        """
        # Returns a tuple with weekday of first day of the month and the number of days in said month
        days = monthrange(self.end[0].year, self.end[0].month)[1]
        return days*24*4 - meter_data_objects.count()

    @staticmethod
    def get_next_value(meter_pk, saved_time, delta=timedelta(minutes=15)):
        """Queries the temporal successor of a meter data point.

        Args:
            meter_pk: The meters private key.
            saved_time: The wanted time as a datetime object.
            delta: A timedelta object defining what a successor is.

        Returns:
            The temporal successor as a MeterData object.
        """
        next_value = MeterData.objects.filter(
            meter__flat__pk=meter_pk,
            saved_time=saved_time + delta
        ).values('saved_time', 'value')

        if len(next_value) > 0:
            return next_value[0]

    @staticmethod
    def get_consumption(meter_pk, timerange):
        """Calculates the consumption based on meter values for a given meter.

        Args:
            meter_pk: The meters private key.
            timerange: A datetime object where month and year will be extracted.

        Returns:
             A dictionary with datetime objects as keys and consumption values as values.
        """
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
                if value is not None and delta_value is not None:
                    consumption_series[delta_value['saved_time']] = delta_value['value'] - value['value']

            # Remove the last element
            time_series.pop()
            return consumption_series

    @staticmethod
    def get_value_at(dictionary, key: datetime, threshold=3):
        """Timestamps of meter values can sometimes vary between a few minutes so that comparing
        datetime objects might not always come to the same result. In order to solve that one can either
        set a fixed datetime for all meter values queried at the same time slot (quarter-hour) or check
        multiple keys. This method does the latter.

        Args:
            dictionary: The dictionary where we want values from.
            key: The key to look for.
            threshold: A limited region.

        Returns:
            The value ´near´ (according to the :param threshold) the :param key.
        """
        # TODO: Check deprecation since datetime is set on the first query of meter data now.
        times = 0
        element = None
        while element is None and times < threshold:
            element = dictionary.get(key)
            key = key.replace(minute=key.minute + 1)
            times += 1

        return element

    def get_extended_meter_data(self, pk, total_consumption, production_values, consumption_values, meter_value):
        """Gathers further information for a given flat not contained in a
        regular MeterData object.

        Args:
            pk: The private key of the desired flat.
            total_consumption: A dictionary containing the total consumption of all meters like {datetime: float}.
            production_values: A dictionary containing the production values for each
            export flat like {pk: {datetime: float}}.
            consumption_values: A dictionary containing the consumption values of the flat with
            private key :param pk like {datetime: float}.
            meter_value: The meter value of the flat with private key :param pk.

        Returns:
            A dictionary with human-readable keys and corresponding values.
        """
        last_month = self.end[0].replace(day=1) - timedelta(days=1)
        last_month_values = MeterData.objects.filter(
            meter__flat__pk=pk,
            saved_time__month=last_month.month,
            saved_time__year=last_month.year).order_by('-saved_time')

        if last_month_values.exists():
            last_month_value = last_month_values.first().value
            last_month_saved_time = last_month_values.first().saved_time
        else:
            last_month_value = 0
            last_month_saved_time = DownloadOverview.NO_DATA

        production_parts = dict.fromkeys(production_values, 0.0)
        consumption = meter_value - last_month_value
        logger.info("Consumption: %f" % consumption)

        for el in consumption_values:
            saved_time = el
            value = consumption_values[el]
            specific_total_consumption = self.get_value_at(total_consumption, saved_time)
            specific_total_production = 0.0

            for meter_id in production_values.keys():
                val = self.get_value_at(production_values[meter_id], saved_time)
                if val is not None:
                    specific_total_production += val

            if specific_total_consumption is not None:
                coeff = value / specific_total_consumption
                for meter_id in production_values.keys():
                    production_value = self.get_value_at(production_values.get(meter_id), saved_time)

                    if production_value is not None:
                        if specific_total_production > specific_total_consumption:
                            # if all export meters produce more than all others consume
                            # then ignore the surplus.
                            production_value = (production_value/specific_total_production) * specific_total_consumption

                        production_parts[meter_id] += coeff * production_value

        part_distributor = consumption
        for val in production_parts.values():
            part_distributor -= val

        result = {'Vormonat': last_month_value, 'Uhrzeit Vormonat': last_month_saved_time,
                  'Verbrauch': consumption, 'Anteil Versorger': part_distributor}
        for key in production_parts.keys():
            name = Flat.objects.get(pk=key).name
            result[name] = production_parts[key]

        return result
