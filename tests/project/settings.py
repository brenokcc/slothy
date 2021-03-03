import os
from corsheaders.defaults import default_headers

CORS_ALLOW_HEADERS = list(default_headers) + ['X-Proxy']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = __file__.split(os.sep)[-2]
DEBUG = True
ROOT_URLCONF = 'slothy.api.urls'
ALLOWED_HOSTS = '*'
CORS_ORIGIN_ALLOW_ALL = True
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_L10N = True
USE_TZ = False
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]
SECRET_KEY = 'not so secret'
INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'netifaces',
    'corsheaders',
    'slothy.core',
    'slothy.api',
    # 'sslserver',
    'base',
    'slothy.regional.brasil.enderecos',
)
COLORS = '#f1948a', '#af7ac5', '#f7dc6f', '#73c6b6', '#5dade2', '#82e0aa'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    }
]
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
