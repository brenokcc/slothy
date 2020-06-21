from django.conf import settings
from django.conf.urls import url
from slothy.api.views import Api
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

urlpatterns = staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    url(r"^api/(?P<path>.*)?$", Api.as_view()),
]

