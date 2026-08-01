"""URL configuration.

This service is a JSON API. The Django admin route below is the generator's own shape and is
kept rather than removed, because whether Mapsift ships an admin at all is a product decision
nobody has taken and the scaffold does not get to take it by deletion.
"""

from django.contrib import admin
from django.urls import path

from config.api import api

urlpatterns = [
    path("api/", api.urls),
    path("admin/", admin.site.urls),
]
