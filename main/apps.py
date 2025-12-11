from django.apps import AppConfig


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"
    verbose_name = "Основное"

    def ready(self):
        from django.contrib import admin
        from .models import BaseInfo
        from .utils.fonts import register_fonts
        register_fonts()

        info = BaseInfo.get_solo()
        if info:
            admin.site.site_header = info.name
            admin.site.site_title = info.name
            admin.site.site_url = info.site_url
