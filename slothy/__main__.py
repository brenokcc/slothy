import sys
import os
import shutil

# ~/Library/Preferences/PyCharmCE2019.3/templates/dp.xml
# ~/.PyCharmCE2019.3
# ~\.PyCharmCE2019.3

if len(sys.argv) < 2:
    print('Type one of the following options: startproject')
    sys.exit(0)


def replace_text(file_path, text, replace):
    with open(file_path, 'r') as f:
        data = f.read().replace(text, replace)
    with open(file_path, 'w') as f:
        f.write(data)


if sys.argv[1] == 'startproject':
    project_name = sys.argv[2]
    project_path = os.path.join(os.path.abspath('.'), project_name)
    test_path = os.path.join(os.path.dirname(__file__), 'test')
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, project_name), exist_ok=True)
    test_manage_path = os.path.join(test_path, 'project', 'manage.py')
    test_settings_path = os.path.join(test_path, 'project', 'settings.py')
    test_init_path = os.path.join(test_path, 'project', '__init__.py')
    test_models_path = os.path.join(test_path, 'project', 'base', 'models.py')
    shutil.copyfile(test_manage_path, os.path.join(project_path, 'manage.py'))
    shutil.copyfile(test_settings_path, os.path.join(project_path, 'settings.py'))
    shutil.copyfile(test_init_path, os.path.join(project_path, '__init__.py'))
    shutil.copyfile(test_init_path, os.path.join(project_path, project_name, '__init__.py'))
    open(os.path.join(project_path, project_name, 'models.py'), 'w').write('''# -*- coding: utf-8 -*-
from slothy.api import models
from slothy.api.models.decorators import user, role, attr, action, fieldset, param

class PessoaManager(models.DefaultManager):

    @attr('Pessoas')
    def all(self):
        return super().all().display('id', 'nome')


@user('email')
class Pessoa(models.AbstractUser):

    nome = models.CharField(verbose_name='Nome', max_length=255)
    email = models.EmailField(verbose_name='E-mail', unique=True, max_length=255)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

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
        return super().view('dados_gerais', 'dados_acesso')
 
    @action('Alterar Senha')
    def alterar_senha(self, senha):
        super().change_password(senha)

    @attr('Dados Gerais')
    def dados_gerais(self):
        return self.values('nome', ('email', 'foto'))

    @attr('Dados de Acesso')
    def dados_acesso(self):
        return self.values('nome', ('last_login', 'password'))
    
''')
    replace_text(os.path.join(project_path, 'settings.py'), 'base', project_name)
    print('Project successfully created!'.format(project_name))

elif sys.argv[1] == 'configure':
    home_dir = os.path.expanduser('~')
    for path in (home_dir, os.path.join(home_dir, 'Library', 'Preferences')):
        for dir_name in os.listdir(path):
            if 'pycharm' in dir_name.lower():
                template_dir = os.path.join(path, dir_name, 'templates')
                if os.path.exists(template_dir):
                    print(template_dir)
