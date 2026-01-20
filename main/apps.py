# main/apps.py
from django.apps import AppConfig

class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        from . import signals            # noqa


class MainConfig(AppConfig):
    name = "main"

    def ready(self):
        import main.signals