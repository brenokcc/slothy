import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
ROOT_URLCONF = 'slothy.api.backend.urls'
ALLOWED_HOSTS = '*'
CORS_ORIGIN_ALLOW_ALL = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]
SECRET_KEY = 'not so secret'
INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'rest_framework.authtoken',
    'slothy.api.backend',
    'app',
)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    }
]
STATIC_URL = '/static/'

AUTH_USER_MODEL = 'app.usuario'
