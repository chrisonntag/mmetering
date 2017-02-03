import datetime

from django.db import models
from django.utils import timezone

class Flat(models.Model):
    MODE_TYPES = (
        ('IM', 'Import'),
        ('EX', 'Export'),
    )
    name = models.CharField(max_length=200, help_text="z.B. Wohnungsnummer", verbose_name="Beschreibung")
    modus = models.CharField(default='IM', max_length=2, choices=MODE_TYPES)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Wohnung"
        verbose_name_plural = "Wohnungen"

class Meter(models.Model):
    flat = models.OneToOneField(Flat, verbose_name="Wohnung")
    addresse = models.IntegerField(default=0, help_text="Addresse, auf der der Zähler erreichbar ist")
    seriennummer = models.CharField(max_length=45, help_text="Seriennummer (hinten auf Zähler)")
    init_datetime = models.DateTimeField()
    start_datum = models.DateField(null=True, blank=True, help_text="wird automatisch ausgefüllt")
    start_zeit = models.TimeField(null=True, blank=True, help_text="wird automatisch ausgefüllt")
    end_datum = models.DateField(null=True, blank=True, help_text="wird automatisch ausgefüllt")
    end_zeit = models.TimeField(null=True, blank=True, help_text="wird automatisch ausgefüllt")

    def __str__(self):
        return 'Zähler in Wohnung ' + self.flat.name

    class Meta:
        verbose_name = "Zähler"
        verbose_name_plural = "Zähler"

class MeterData(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    saved_time = models.DateTimeField()
    value = models.IntegerField()

    def __str__(self):
        return "Datenwert für Wohnung " + self.meter.flat.name

    class Meta:
        permissions = (
            ("can_download", "Can download MeterData"),
            ("can_view", "Can view MeterData"),
        )

class Activities(models.Model):
    title = models.CharField(max_length=70, help_text="Titel")
    text = models.CharField(max_length=300, help_text="Inhalt")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Aktivität'

    class Meta:
        verbose_name = "Aktivität"
        verbose_name_plural = "Aktivitäten"