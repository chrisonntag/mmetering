from django.test import TestCase

from mmetering.models import Flat, Meter


class SerialTestCase(TestCase):
    fixtures = ['mmetering_models_testdata.json']

    def test_data(self):
        self.assertEqual(Flat.objects.count(), 4, "Create 4 meters")
        self.assertEqual(Meter.objects.count(), 4, "Create 4 meters")
