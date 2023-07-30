from django.urls import path

from .views import get_book_catalog

app_name = "openai"

urlpatterns = [
    path("get-book-catalog/", get_book_catalog, name="get_book_catalog"),
]
