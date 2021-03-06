import sys
import os
import shutil
import urllib.parse
from base64 import b64decode

# ~/Library/Preferences/PyCharmCE2019.3/templates/dp.xml
# ~/.PyCharmCE2019.3
# ~\.PyCharmCE2019.3

if len(sys.argv) < 2:
    print('Type one of the following options: front-end, back-end or server')
    sys.exit(0)

if sys.argv[1] not in ('front-end', 'back-end', 'server'):
    print('The allowed options are: front-end, back-end or server')
    sys.exit(0)


def replace_text(file_path, text, replace):
    with open(file_path, 'r') as f:
        data = f.read().replace(text, replace)
    with open(file_path, 'w') as f:
        f.write(data)


if sys.argv[1] == 'front-end':
    project_name = sys.argv[2]
    project_path = os.path.join(os.path.abspath('.'), project_name)
    test_path = os.path.join(os.path.dirname(__file__), 'test')
    frontend_dir_path = os.path.join(test_path, 'frontend')
    test_pages_dir_path = os.path.join(project_path, 'pages', 'test')
    shutil.copytree(frontend_dir_path, project_path)
    shutil.rmtree(test_pages_dir_path)
    print('Project successfully created! Type "cd {}" to get into project\'s directory and then "python -m slothy server" to start development web server.'.format(project_name))

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
    print('Project successfully created! Type "cd {}" to get into project\'s directory and then "python manage.py sync" to initialize the database. To start development server, type "python manage.py runserver".'.format(project_name))

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

    current_dir = os.path.abspath('.')
    templates_file_path = os.path.join(current_dir, 'js', 'templates.js')
    templates = []
    size = 0
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                size += os.path.getsize(file_path)
                templates.append(file_path[len(current_dir) + 1:])

    class HttpHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            print(self.path)
            if '.' in self.path:
                super().do_GET()
            elif self.path == '/compile':
                compile_code = '''<html>
                        <head>
                            <script src="/js/jquery-3.5.1.min.js"></script>
                            <script src="/js/nunjucks.js"></script>
                            <script src="/js/slothy.js"></script>
                            <script>
                            var text="";
                            for(var path of {}) text+=precompile(path);
                            $.post("/", {{t:btoa(unescape(encodeURIComponent(text)))}}, function( data ) {{
                                document.body.innerHTML = data;
                            }});
                            </script>
                        </head>
                    </html>
                        '''.format(templates)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(compile_code.encode())
            else:
                file_path = os.path.join(os.getcwd(), 'pages/base.html')
                self.send_response(200)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())

        def do_POST(self):
            s = self.rfile.read(int(self.headers.get('Content-Length'))).decode()
            script = b64decode(urllib.parse.unquote(s[2:]))
            with open(templates_file_path, 'w') as templates_file:
                templates_file.write(script.decode())
            self.send_response(200)
            self.end_headers()
            html = '<h1>Compiled Files:</h1><ul>{}</ul><p>Size: {}K</p>'.format(
                ''.join(['<li>{}</li>'.format(t) for t in templates]), int(size/1024)
            )
            self.wfile.write(html.encode())

    port = len(sys.argv) > 2 and int(sys.argv[2]) or 9000
    print('''
 ____  _       _   _           
/ ___|| | ___ | |_| |__  _   _ 
\___ \| |/ _ \| __| '_ \| | | |
 ___) | | (_) | |_| | | | |_| |
|____/|_|\___/ \__|_| |_|\__, |
                         |___/     

Nginx configuration:

server {
    listen         80 default_server;
    listen         [::]:80 default_server;
    server_name    localhost;
    index          index;
    try_files $uri /index;
    root /var/www/;
    location ~* \.(js|html|png|css)$ {}
    location / {rewrite ^ /pages/base.html break;}
}
    ''')
    print('Access http://0.0.0.0:{}/ for navigatings the pages defined in the "pages" directory.'.format(port))
    print('Access http://0.0.0.0:{}/compile for compiling the templates into "js/templates.js" file.'.format(port))
    print('Quit the server with CONTROL-C')
    httpd = HTTPServer(("", port), HttpHandler)

    # with open(templates_file_path, 'w') as templates_file:
    #    templates_file.write('')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
