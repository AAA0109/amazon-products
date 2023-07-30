from django.apps import AppConfig


class AdsApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ads_api"
    label = "ads_api"

    def ready(self):
        from apps.ads_api import analysis, clickup, data_exchange, models
