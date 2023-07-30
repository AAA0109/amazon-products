import openai
from django.apps import AppConfig

from adsdroid.settings import OPENAI_API_KEY


class OpenaiApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.openai_api"

    def ready(self) -> None:
        openai.api_key = OPENAI_API_KEY
        return super().ready()
