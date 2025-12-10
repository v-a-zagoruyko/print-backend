from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"
    verbose_name = "Основное"

    def ready(self):
        from .utils.fonts import register_fonts
        register_fonts()
