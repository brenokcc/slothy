# -*- coding: utf-8 -*-

ALLOWED_HOSTS = '*'
CORS_ORIGIN_ALLOW_ALL = True

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Recife'
USE_I18N = True
USE_L10N = True
USE_TZ = False


DEFAULT_APPS = (
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'corsheaders',
    'slothy.admin',
    'slothy.api',
)


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    }
]
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

THEME = dict(
    TEXT_COLOR='#000000',
    DARK_TEXT_COLOR='#9f9f9f',
    BACKGROUND_COLOR='#f9f9f9',
    PRIMARY_COLOR='#000000',
    BAR_FONT_COLOR='#000000',
    BAR_BACKGROUND_COLOR='#FFFFFF',
    BAR_GRADIENT_COLOR='#FFFFFF',
    CARD_ICON_COLOR='#000000',
    CARD_TEXT_COLOR='#000000',
    CARD_BACKGROUND_COLOR='#FFFFFF',
    SHORTCUT_ICON_COLOR='#000000',
    SHORTCUT_TEXT_COLOR='#000000',
    SHORTCUT_BACKGROUND_COLOR='#f9f9f9',
    COLORS=('#f7dc6f', '#73c6b6', '#f1948a', '#af7ac5', '#5dade2', '#82e0aa'),
)

LOCATION_SHARING_INTERVAL = 0

AUTH_USER_MODEL = 'admin.user'

