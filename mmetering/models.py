import datetime

from django.db import models
from django.utils import timezone

class Flat(models.Model):
    MODE_TYPES = (
        ('IM', 'Import'),
        ('EX', 'Export'),
    )
    desc = models.CharField(max_length=200, help_text="e.g. apartment number")
    mode = models.CharField(default='IM', max_length=2, choices=MODE_TYPES)

    def __str__(self):
        return self.desc

class Meter(models.Model):
    flat = models.OneToOneField(Flat)
    uuid = models.IntegerField(default=0, help_text="Address on which the meter is accessable")
    serial = models.CharField(max_length=45, help_text="Serialnumber making the meter unique")
    init_datetime = models.DateTimeField()
    start_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return 'Meter in Flat ' + self.flat.desc

class MeterData(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    saved_time = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return "Data for Flat " + self.meter.flat.desc

