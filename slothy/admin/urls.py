# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = staticfiles_urlpatterns()

urlpatterns += [
    url(r"^static/app/icons/Icon-512.png$", lambda request: redirect(settings.PROJECT_LOGO, permanent=True)),
    url(r"^static/app/icons/Icon-192.png$", lambda request: redirect(settings.PROJECT_LOGO, permanent=True)),
    url(r"^static/favicon.ico$", lambda request: redirect(settings.PROJECT_LOGO, permanent=True)),
]
