from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("hijack_user/", views.hijack_user, name="hijack_user"),
    path("functions/", views.manage_fucntions, name="manage_functions"),
    path("logging/", views.logs_view, name="logging"),
]
