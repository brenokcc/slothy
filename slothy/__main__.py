import sys
import os
import shutil
import urllib.parse

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
    frontend_dir_path = os.path.join(test_path, 'frontend')
    shutil.copytree(frontend_dir_path, project_path)

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

    current_dir = os.path.abspath('.')
    templates_file_path = os.path.join(current_dir, 'js', 'templates.js')

    class HttpHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            print(self.path)
            if '.' in self.path:
                super().do_GET()
            elif self.path == '/compile':
                templates = []
                for root, dirs, files in os.walk(current_dir):
                    for file in files:
                        if file.endswith(".html"):
                            templates.append(os.path.join(root, file)[len(current_dir) + 1:])
                compile_code = '''<html>
                        <head>
                            <script src="/js/jquery-3.5.1.min.js"></script>
                            <script src="/js/nunjucks.js"></script>
                            <script src="/js/slothy.js"></script>
                            <script>
                            var text="";
                            for(var path of {}) text+=precompile(path);
                            $.post("/", {{t:text}}, function( data ) {{alert(data);}});
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
            script = urllib.parse.unquote(self.rfile.read(int(self.headers.get('Content-Length'))).decode()[2:])
            with open(templates_file_path, 'w') as templates_file:
                templates_file.write(script)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Templates sucessfully compiled!')

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
    httpd = HTTPServer(("", port), HttpHandler)

    with open(templates_file_path, 'w') as templates_file:
        templates_file.write('')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
