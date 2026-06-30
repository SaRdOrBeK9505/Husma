from django.apps import AppConfig


class MaklerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.makler'
    
    def ready(self):
        """Signal'larni import qilish."""
        import apps.makler.signals  # noqa
