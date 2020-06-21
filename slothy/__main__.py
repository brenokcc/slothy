import sys
import os
import shutil

# ~/Library/Preferences/PyCharmCE2019.3/templates/dp.xml
# ~/.PyCharmCE2019.3
# ~\.PyCharmCE2019.3


def replace_text(file_path, text, replace):
    with open(file_path, 'r') as f:
        data = f.read().replace(text, replace)
    with open(file_path, 'w') as f:
        f.write(data)


if sys.argv[1] == 'front-end':
    project_name = sys.argv[2]
    project_path = os.path.join(os.path.abspath('.'), project_name)
    test_path = os.path.join(os.path.dirname(__file__), 'test')
    os.makedirs(project_path, exist_ok=True)
    # os.makedirs(os.path.join(project_path, 'static'), exist_ok=True)
    test_base_path = os.path.join(test_path, 'frontend', 'base.html')
    test_index_html = os.path.join(test_path, 'frontend', 'index.html')
    for file_name in ('base.html', 'index.html', 'index.js'):
        file_path = os.path.join(test_path, 'frontend', file_name)
        shutil.copyfile(file_path, os.path.join(project_path, file_name))
    static_dir_path = os.path.join(test_path, 'frontend', 'static')
    shutil.copytree(static_dir_path, os.path.join(project_path, 'static'))

elif sys.argv[1] == 'back-end':
    project_name = sys.argv[2]
    project_path = os.path.join(os.path.abspath('.'), project_name)
    test_path = os.path.join(os.path.dirname(__file__), 'test')
    os.makedirs(project_path, exist_ok=True)
    os.makedirs(os.path.join(project_path, project_name), exist_ok=True)
    test_manage_path = os.path.join(test_path, 'backend', 'manage.py')
    test_settings_path = os.path.join(test_path, 'backend', 'settings.py')
    test_init_path = os.path.join(test_path, 'backend', '__init__.py')
    test_models_path = os.path.join(test_path, 'backend', 'base', 'models.py')
    shutil.copyfile(test_manage_path, os.path.join(project_path, 'manage.py'))
    shutil.copyfile(test_settings_path, os.path.join(project_path, 'settings.py'))
    shutil.copyfile(test_init_path, os.path.join(project_path, '__init__.py'))
    shutil.copyfile(test_init_path, os.path.join(project_path, project_name, '__init__.py'))
    shutil.copyfile(test_models_path, os.path.join(project_path, project_name, 'models.py'))
    replace_text(os.path.join(project_path, 'settings.py'), 'base', project_name)
    os.system('cd {} && python manage.py sync'.format(project_name))

elif sys.argv[1] == 'configure':
    home_dir = os.path.expanduser('~')
    for path in (home_dir, os.path.join(home_dir, 'Library', 'Preferences')):
        for dir_name in os.listdir(path):
            if 'pycharm' in dir_name.lower():
                template_dir = os.path.join(path, dir_name, 'templates')
                if os.path.exists(template_dir):
                    print(template_dir)

elif sys.argv[1] == 'server':
    import os
    from http.server import SimpleHTTPRequestHandler
    from http.server import HTTPServer

    class HttpHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if '.' in self.path:
                super().do_GET()
            else:
                path = os.path.join(os.getcwd(), 'base.html')
                self.send_response(200)
                self.end_headers()
                with open(path, 'rb') as f:
                    self.wfile.write(f.read())

    port = len(sys.argv) > 2 and int(sys.argv[2]) or 9000
    print('http://0.0.0.0:{}/'.format(port))
    httpd = HTTPServer(("", port), HttpHandler)
    httpd.serve_forever()
