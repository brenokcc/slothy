# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import url
from slothy.api.views import Api, QuerysetView, UploadView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

urlpatterns = staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    url(r"^queryset/(?P<app_label>\w+)/(?P<model_name>\w+)/(?P<subset>\w+)/$", QuerysetView.as_view()),
    url(r"^queryset/(?P<app_label>\w+)/(?P<model_name>\w+)/$", QuerysetView.as_view()),
    url(r"^upload/", UploadView.as_view()),
    url(r"^(?P<service>\w+)/(?P<path>.*)?$", Api.as_view())
]
