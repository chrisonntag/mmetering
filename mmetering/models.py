import datetime

from django.db import models
from django.utils import timezone

class Flat(models.Model):
    MODE_TYPES = (
        ('IM', 'Import'),
        ('EX', 'Export'),
    )
    name = models.CharField(max_length=200, help_text="z.B. Wohnungsnummer")
    modus = models.CharField(default='IM', max_length=2, choices=MODE_TYPES)

    def __str__(self):
        return self.desc

class Meter(models.Model):
    flat = models.OneToOneField(Flat)
    addresse = models.IntegerField(default=0, help_text="Addresse, auf der der Zähler erreichbar ist")
    seriennummer = models.CharField(max_length=45, help_text="Seriennummer (hinten auf Zähler)")
    init_datetime = models.DateTimeField()
    start_datum = models.DateField(null=True, blank=True, help_text="wird automatisch ausgefüllt")
    start_zeit = models.TimeField(null=True, blank=True, help_text="wird automatisch ausgefüllt")
    end_datum = models.DateField(null=True, blank=True, help_text="wird automatisch ausgefüllt")
    end_zeit = models.TimeField(null=True, blank=True, help_text="wird automatisch ausgefüllt")

    def __str__(self):
        return 'Zähler in Wohnung ' + self.flat.name

class MeterData(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    saved_time = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return "Datenwert für Wohnung " + self.meter.flat.name

