# -*- coding: utf-8 -*-
import os
from slothy.conf.settings import *

DEBUG = True
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_NAME = 'Finanças'
ROOT_URLCONF = 'slothy.api.urls'
SECRET_KEY = '1eb66f2e7a0311eb9e473c15c2da2c92'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

INSTALLED_APPS = DEFAULT_APPS + (
    'financeiro',
)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

COLORS = '#58D68D', '#D35400'
