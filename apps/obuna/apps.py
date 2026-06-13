from django.apps import AppConfig


class ObunaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.obuna'
    verbose_name = 'Obuna'

    def ready(self):
        from . import signals  # noqa: F401
