from django.test import TestCase
from backend.tasks import save_meter_data_task
from mmetering.models import Flat, Meter


class SerialTestCase(TestCase):
    """
    This TestCase loads a fixture with following structure:

    -   Two
    -   One

    It performs following tests:

    -   Put a save_meter_data_task in the queue
    -   Put a save_meter_data_task with a meter with communication error in the queue.
    -   "Change" a flats meter.
    """
    fixtures = ['mmetering_models_testdata.json']

    def test_data(self):
        self.assertEqual(Flat.objects.count(), 6)
        self.assertEqual(Meter.objects.count(), 6)
