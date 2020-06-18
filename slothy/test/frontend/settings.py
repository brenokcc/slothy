import os
DEBUG = True
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, 'web')
ROOT_URLCONF = 'slothy.api.frontend.urls'
INSTALLED_APPS = 'slothy.api.frontend',
TEMPLATES = {'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True, 'DIRS': [WEB_DIR]},
STATIC_URL = '/static/'
STATICFILES_DIRS = [WEB_DIR]
SECRET_KEY = '*****'
