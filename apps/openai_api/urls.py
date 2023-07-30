from django.urls import path

from .views import filter_keywords, suggest_keywords, suggest_negatives

app_name = "openai"

urlpatterns = [
    path("suggestKeywords/", suggest_keywords, name="suggest_keywords"),
    path("filterKeywords/", filter_keywords, name="filter_keywords"),
    path("suggestNegativeAsins/", suggest_negatives, name="suggest_negatives"),
]
