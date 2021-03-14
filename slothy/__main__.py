import sys
import os
import uuid
import stat

# ~/Library/Preferences/PyCharmCE2019.3/templates/dp.xml
# ~/.PyCharmCE2019.3
# ~\.PyCharmCE2019.3

if len(sys.argv) < 2:
    print('Type one of the following options: startproject')
    sys.exit(0)

INIT_FILE_CONTENT = '# -*- coding: utf-8 -*-'

GIT_IGNORE_FILE_CONTENT = '''*.pyc
.svn
.DS_Store
.DS_Store?
._*
*˜
.idea/
db.sqlite3
.project
.pydevproject
media
logs
'''

MANAGE_FILE_CONTENT = '''#!/usr/bin/env python
import os
import sys
import warnings

warnings.filterwarnings(
    "ignore", module='(rest_framework|ruamel|scipy|reportlab|django|jinja|corsheaders)'
)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
'''

WSGI_FILE_CONTENT = '''import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '%s.settings')

application = get_wsgi_application()
'''

GUNICORN_FILE_CONTENT = '''#!/bin/bash
set -e
if [ ! -d ".virtualenv" ]; then
 python -m pip install virtualenv
 python -m virtualenv .virtualenv
 source .virtualenv/bin/activate
 python -m pip install -r requirements.txt
else
 source .virtualenv/bin/activate
fi

mkdir -p logs
python manage.py sync
echo "Starting gunicorn..."
exec gunicorn %s.wsgi:application -w 1 -b 127.0.0.1:${1:-8000} --timeout=600 --user=${2:-$(whoami)} --log-level=_debug --log-file=logs/gunicorn.log 2>>logs/gunicorn.log
'''

SETTINGS_FILE_CONTENT = '''# -*- coding: utf-8 -*-
import os
from slothy.conf.settings import *

DEBUG = True
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_NAME = 'Finanças'
PROJECT_LOGO = '/static/logo.png'
SECRET_KEY = '%s'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

INSTALLED_APPS = DEFAULT_APPS + (
    '%s',
)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
ROOT_URLCONF = '%s.urls'
'''

URLS_FILE_CONTENT = '''# -*- coding: utf-8 -*-

from slothy.admin import views
from django.conf.urls import url
from slothy.api.urls import urlpatterns as api_urls
from slothy.admin.urls import urlpatterns as admin_urls

urlpatterns = api_urls + admin_urls + [
    url(r"^$", views.index)
]
'''

MODEL_FILE_CONTENT = '''# -*- coding: utf-8 -*-
from slothy.db import models
from slothy.admin.models import User, attr, action, param, fieldsets, 
from slothy.decorators import dashboard, 


class PessoaSet(models.Set):

    @attr('Pessoas')
    def all(self):
        return self.display(
            'foto', 'nome', 'email'
        ).search('nome')


class Pessoa(User):

    nome = models.CharField(verbose_name='Nome')
    email = models.EmailField(verbose_name='E-mail', unique=True, is_username=True)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

    @fieldsets({'Dados Gerais': ('nome', ('email', 'foto'))})
    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view()
 
    @action('Alterar Senha')
    def alterar_senha(self, senha):
        super().change_password(senha)

    @fieldset('Dados Gerais')
    def get_dados_gerais(self):
        return self.values('nome', ('email', 'foto'))

    @fieldset('Dados de Acesso')
    def get_dados_acesso(self):
        return self.values('nome', ('last_login', 'password'))
'''

if sys.argv[1] == 'startproject':
    project_name = sys.argv[2]
    project_path = os.path.join(os.path.abspath('.'), project_name)
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, 'media'), exist_ok=True)
    os.makedirs(os.path.join(project_path, project_name), exist_ok=True)
    os.makedirs(os.path.join(project_path, project_name, 'static'), exist_ok=True)

    with open(os.path.join(project_path, '__init__.py'), 'w') as file:
        file.write(INIT_FILE_CONTENT)

    with open(os.path.join(project_path, 'manage.py'), 'w') as file:
        file.write(MANAGE_FILE_CONTENT % project_name)

    with open(os.path.join(project_path, 'requirements.txt'), 'w') as file:
        if os.path.exists('/Users/breno/'):
            file.write('/Users/breno/Documents/Slothy/Backend/')
        file.write('slothy')

    with open(os.path.join(project_path, '.gitignore'), 'w') as file:
        file.write(GIT_IGNORE_FILE_CONTENT)

    with open(os.path.join(project_path, project_name, 'wsgi.py'), 'w') as file:
        file.write(WSGI_FILE_CONTENT % project_name)

    with open(os.path.join(project_path, '%s.sh' % project_name), 'w') as file:
        file.write(GUNICORN_FILE_CONTENT % project_name)
    st = os.stat(os.path.join(project_path, '%s.sh' % project_name))
    os.chmod(os.path.join(project_path, '%s.sh' % project_name), st.st_mode | stat.S_IEXEC)

    with open(os.path.join(project_path, project_name, 'settings.py'), 'w') as file:
        file.write(SETTINGS_FILE_CONTENT % (uuid.uuid1().hex, project_name, project_name))

    with open(os.path.join(project_path, project_name, '__init__.py'), 'w') as file:
        file.write(INIT_FILE_CONTENT)

    with open(os.path.join(project_path, project_name, 'models.py'), 'w') as file:
        file.write(MODEL_FILE_CONTENT)

    with open(os.path.join(project_path, project_name, 'urls.py'), 'w') as file:
        file.write(URLS_FILE_CONTENT)

    print('Project "{}" successfully created!'.format(project_name))

elif sys.argv[1] == 'configure':
    home_dir = os.path.expanduser('~')
    for path in (home_dir, os.path.join(home_dir, 'Library', 'Preferences')):
        for dir_name in os.listdir(path):
            if 'pycharm' in dir_name.lower():
                template_dir = os.path.join(path, dir_name, 'templates')
                if os.path.exists(template_dir):
                    print(template_dir)
