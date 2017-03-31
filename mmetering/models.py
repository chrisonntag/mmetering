import datetime

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

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
    init_datetime = models.DateTimeField(auto_now_add=True)
    start_datetime = models.DateTimeField(null=True,
                                          blank=True,
                                          help_text="wird automatisch ausgefüllt", verbose_name="Laufzeit Start")
    end_datetime = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name="Laufzeit Ende")
    active = models.BooleanField(default=False, verbose_name="Aktivieren")

    def __str__(self):
        return 'Zähler in ' + self.flat.name

    def clean(self):
        # Make sure expiry or start time cannot be in the past
        if ((not None in [self.start_datetime, self.end_datetime]) and
            (self.start_datetime <= datetime.datetime.today() and self.end_datetime <= datetime.datetime.today())):
            raise ValidationError('Start- und Endzeit dürfen nicht in der Vergangenheit liegen.')

    class Meta:
        verbose_name = "Zähler"
        verbose_name_plural = "Zähler"

class MeterData(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    saved_time = models.DateTimeField()
    value = models.FloatField()

    def __str__(self):
        return "Datenwert für " + self.meter.flat.name

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