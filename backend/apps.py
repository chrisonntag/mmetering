from django.apps import AppConfig


class BackendConfig(AppConfig):
    name = 'backend'
    verbose_name = 'Backend Application'

    def ready(self):
        import backend.signals