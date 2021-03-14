# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import url
from slothy.api import views
from django.conf.urls.static import static

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    url(r'^api/(?P<path>.*)?$', views.api),
    url(r'^upload/', views.upload),
    url(r'^postman/$', views.postman),
    url(r'^settings/$', views.settingss),
    url(r'^geolocation/$', views.geolocation),
    url(r'^queryset/(?P<app_label>\w+)/(?P<model_name>\w+)/(?P<subset>\w+)$', views.queryset),
    url(r'^queryset/(?P<app_label>\w+)/(?P<model_name>\w+)$', views.queryset),
]
