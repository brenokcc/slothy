# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import url
from slothy.api import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

urlpatterns = staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    url(r"^$", views.index),
    url(r"^queryset/(?P<app_label>\w+)/(?P<model_name>\w+)/(?P<subset>\w+)$", views.queryset),
    url(r"^queryset/(?P<app_label>\w+)/(?P<model_name>\w+)$", views.queryset),
    url(r"^upload/", views.upload),
    url(r"^geolocation/$", views.geolocation),
    url(r"^postman/$", views.postman),
    url(r"^(?P<service>\w+)/(?P<path>.*)?$", views.api)
]
