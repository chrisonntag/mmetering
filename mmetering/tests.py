from django.test import TestCase
from mmetering.summaries import Overview
from datetime import datetime
from freezegun import freeze_time


class DummyRequest:
    GET = None


class SummariesDataTest(TestCase):
    fixtures = ['mmetering/fixtures/mmetering_models_testdata.json']
    data = Overview(DummyRequest.GET)

    def test_parse_date(self):
        start_of_the_day = datetime(2017, 11, 11, 0, 0, 0, 0)
        end_of_the_day = datetime(2017, 11, 11, 23, 59, 59, 0)
        self.assertEquals(Overview.parse_date('11.11.2017', False), start_of_the_day)
        self.assertEquals(Overview.parse_date('11.11.2017', True), end_of_the_day)
        self.assertRaises(ValueError, Overview.parse_date('11/11/2017', True))
        self.assertRaises(ValueError, Overview.parse_date('40.13.2017', True))
        self.assertRaises(ValueError, Overview.parse_date('11.12.017', True))

    def test_get_data_range(self):
        start_date = datetime(2017, 2, 4, 8, 0)
        end_date = datetime(2017, 2, 4, 8, 45)
        past_date = datetime(2017, 2, 3, 0, 0)

        import_range = SummariesDataTest.data.get_data_range(start_date, end_date, 'IM')
        export_range = SummariesDataTest.data.get_data_range(start_date, end_date, 'EX')
        import_range_empty = SummariesDataTest.data.get_data_range(past_date, past_date, 'IM')

        assert len(import_range) == 4
        assert len(export_range) == 4
        self.assertAlmostEqual(import_range[3]['value_sum'], 21902, 2)  # 08:45
        self.assertAlmostEqual(export_range[2]['value_sum'], 13154860.4, 2)  # 08:30
        self.assertListEqual(list(import_range_empty), [])

    def test_get_total(self):
        end_date_import = datetime(2017, 2, 7, 0, 0, 0)
        end_date_export = datetime(2017, 2, 4, 14, 45, 0)
        asserted_values_import = [86.507, 91.699, 82.495, 41.283]
        asserted_values_export = [15.658, 13163.4786]

        self.assertListEqual(SummariesDataTest.data.get_total(end_date_import, 'IM'), asserted_values_import)
        self.assertListEqual(SummariesDataTest.data.get_total(end_date_export, 'EX'), asserted_values_export)

    def test_get_total_consumption(self):
        end_date = datetime(2017, 2, 7, 0, 0, 0)

        self.assertAlmostEqual(SummariesDataTest.data.get_total_consumption(end_date), 0.301984, 3)

    def test_get_day_consumption(self):
        end_date = datetime(2017, 2, 6, 0, 0, 0)

        self.assertAlmostEqual(SummariesDataTest.data.get_day_consumption(end_date), 109.523, 3)

    def test_supply_over_threshold(self):
        with freeze_time('2017-02-04 12:42:34'):
            data = Overview(DummyRequest.GET)
            self.assertFalse(data.is_supply_over_threshold(0.7))

        with freeze_time('2017-02-04 13:12:34'):
            data = Overview(DummyRequest.GET)
            self.assertTrue(data.is_supply_over_threshold(0.7))

        with freeze_time('2017-02-03 13:12:34'):
            data = Overview(DummyRequest.GET)

            # return False if no data is available
            self.assertFalse(data.is_supply_over_threshold(0.7))
