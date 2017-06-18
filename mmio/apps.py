from django.apps import AppConfig


class MmioConfig(AppConfig):
    name = 'mmio'
    verbose_name = 'MMetering IO Board'

    def ready(self):
        import mmio.signals
