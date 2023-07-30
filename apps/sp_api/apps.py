from django.apps import AppConfig


class AdsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sp_api"
    label = "sp_api"

    def ready(self):
        from apps.sp_api import book_info
