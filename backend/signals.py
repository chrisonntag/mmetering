import os.path
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from mmetering.models import MeterData


@receiver(post_save, sender=MeterData)
def meterdata_post_save(sender, **kwargs):
    print('Saved: {}'.format(kwargs['instance'].__dict__))