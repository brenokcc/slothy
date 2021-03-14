# -*- coding: utf-8 -*-

from slothy.admin import views
from django.conf.urls import url
from slothy.api.urls import urlpatterns as api_urls
from slothy.admin.urls import urlpatterns as admin_urls

urlpatterns = api_urls + admin_urls + [
    url(r"^$", views.index)
]
