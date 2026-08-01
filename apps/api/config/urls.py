"""URL configuration. This service is a JSON API; the admin route is the generator's own shape."""

from django.contrib import admin
from django.urls import path

from config.api import api

urlpatterns = [
    path("api/", api.urls),
    path("admin/", admin.site.urls),
]
