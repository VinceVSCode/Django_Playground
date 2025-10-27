from django.apps import AppConfig


class FirstsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'firstsite'

    def ready(self):
        # Import signal handlers
        from . import signals
        