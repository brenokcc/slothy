import sys
import os
import shutil

# ~/Library/Preferences/PyCharmCE2019.3/templates/dp.xml
# ~/.PyCharmCE2019.3
# ~\.PyCharmCE2019.3

project_name = sys.argv[2]
project_path = os.path.join(os.path.abspath('.'), project_name)
test_path = os.path.join(os.path.dirname( __file__), 'test')


def replace_text(file_path, text, replace):
    with open(file_path, 'r') as f:
        data = f.read().replace(text, replace)
    with open(file_path, 'w') as f:
        f.write(data)


if sys.argv[1] == 'front-end':
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, 'web'), exist_ok=True)
    test_manage_path = os.path.join(test_path, 'frontend', 'manage.py')
    test_settings_path = os.path.join(test_path, 'frontend', 'settings.py')
    test_base_path = os.path.join(test_path, 'frontend', 'web', 'base.html')
    shutil.copyfile(test_manage_path, os.path.join(project_path, 'manage.py'))
    shutil.copyfile(test_settings_path, os.path.join(project_path, 'settings.py'))
    shutil.copyfile(test_base_path, os.path.join(project_path, 'web', 'base.html'))
    with open(os.path.join(project_path, 'web', 'index.html'), 'w') as file:
        file.write('<h1>Hello {{ name }}!</h1>\n')
    with open(os.path.join(project_path, 'web', 'index.js'), 'w') as file:
        file.write("api.context({name: 'world'})\napi.render()\n")
    os.system('cd {}'.format(project_name))

elif sys.argv[1] == 'back-end':
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, project_name), exist_ok=True)
    test_manage_path = os.path.join(test_path, 'backend', 'manage.py')
    test_settings_path = os.path.join(test_path, 'backend', 'settings.py')
    test_init_path = os.path.join(test_path, 'backend', '__init__.py')
    test_models_path = os.path.join(test_path, 'backend', 'app', 'models.py')
    shutil.copyfile(test_manage_path, os.path.join(project_path, 'manage.py'))
    shutil.copyfile(test_settings_path, os.path.join(project_path, 'settings.py'))
    shutil.copyfile(test_init_path, os.path.join(project_path, '__init__.py'))
    shutil.copyfile(test_init_path, os.path.join(project_path, project_name, '__init__.py'))
    shutil.copyfile(test_models_path, os.path.join(project_path, project_name, 'models.py'))
    replace_text(os.path.join(project_path, 'settings.py'), 'app', project_name)
    os.system('cd {} && python manage.py sync'.format(project_name))

elif sys.argv[1] == 'configure':
    home_dir = os.path.expanduser('~')
    for path in (home_dir, os.path.join(home_dir, 'Library', 'Preferences')):
        for dir_name in os.listdir(path):
            if 'pycharm' in dir_name.lower():
                template_dir = os.path.join(path, dir_name, 'templates')
                if os.path.exists(template_dir):
                    print(template_dir)
