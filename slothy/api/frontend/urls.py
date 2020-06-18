from django.conf import settings
from django.conf.urls import url
from slothy.api.frontend.views import Base
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static

urlpatterns = staticfiles_urlpatterns()
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += [
    url(r"^(?P<path>.*)?$", Base.as_view()),
]

