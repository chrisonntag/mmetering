from django.db import models
from datetime import datetime


class Flat(models.Model):
    MODE_TYPES = (
        ('IM', 'Import'),
        ('EX', 'Export'),
    )
    name = models.CharField(
        max_length=200,
        help_text="z.B. Wohnungsnummer",
        verbose_name="Beschreibung"
    )
    modus = models.CharField(
        default='IM',
        max_length=2,
        choices=MODE_TYPES
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Bezug"
        verbose_name_plural = "Bezüge"


class Meter(models.Model):
    flat = models.OneToOneField(Flat, verbose_name="Bezug")
    addresse = models.IntegerField(default=0, help_text="Addresse, auf der der Zähler erreichbar ist")
    seriennummer = models.CharField(max_length=45, help_text="Seriennummer")
    init_datetime = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False, verbose_name="Aktivieren")
    start_datetime = models.DateTimeField(null=True,
                                          blank=True,
                                          help_text="wird automatisch ausgefüllt",
                                          verbose_name="Laufzeit Start")
    end_datetime = models.DateTimeField(null=True,
                                        blank=True,
                                        verbose_name="Laufzeit Ende")

    def __str__(self):
        return 'Zähler in ' + self.flat.name

    def set_start_datetime(self):
        self.start_datetime = datetime.today()
        self.save()

    def deactivate(self):
        self.active = False
        self.save()

    class Meta:
        verbose_name = "Zähler"
        verbose_name_plural = "Zähler"


class MeterData(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE)
    saved_time = models.DateTimeField(db_index=True)
    value = models.FloatField()
    value_l1 = models.FloatField()
    value_l2 = models.FloatField()
    value_l3 = models.FloatField()

    def __str__(self):
        return "Datenwert für " + self.meter.flat.name

    def get_mode(self):
        return self.meter.flat.modus

    def get_consumption(self, delta):
        pre = MeterData.objects.filter(
            meter=self.meter,
            saved_time=self.saved_time - delta
        ).exists()
        if pre:
            pre_val = MeterData.objects.get(meter=self.meter, saved_time=self.saved_time - delta).value
            return self.value - pre_val
        else:
            return self.value

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
