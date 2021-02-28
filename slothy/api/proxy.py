#!/usr/bin/env python3
import threading
import socket
import base64
import json

NGINX_CONF = '''
stream {
    server {
        listen 8080;
        proxy_pass 127.0.0.1:9999;
    }
}
'''

EMPTY = b'''HTTP/1.1 200 OK
Server: WSGIServer/0.2 CPython/3.8.5
Content-Type: application/json
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: *
Vary: Origin
X-Content-Type-Options: nosniff
Referrer-Policy: same-origin

'''.replace(b'\n', b'\r\n')

DELIMITER = b'@@@'


def recvall(c):
    data = b''
    while True:
        chunk = c.recv(1024)
        data += chunk
        if b'\r\n\r\n' in data:
            index = data.index(b'\r\n\r\n')
            header = data[:index]
            length = 0
            if b'Content-Length:' in header:
                start = header.index(b'Content-Length:')
                length = int(header[start + 15:start + 30].split(b'\r\n')[0].strip())
            if len(data) == index + 4 + length:
                return data


def recv(s):
    buffer = b''
    while True:
        data = s.recv(1024)
        if data:
            buffer += data
            if buffer.endswith(DELIMITER):
                buffer = buffer[:-3]
                break
        else:
            break
    return buffer


class Server:

    def __init__(self, host=('127.0.0.1', 9999)):
        self.host = host
        self.clients = {}

    def process(self, conn, addr):
        print('Connected by', addr)
        data = recvall(conn)
        print('<<<<<<<<<<')
        print(data)

        if data.startswith(b'Token'):
            token = data.split()[-1].strip()
            self.clients[token] = conn
            conn.sendall(token)
        else:
            with conn:
                token = None
                tokens = list(self.clients.keys())
                if tokens:
                    try:
                        start = data.index(b'X-Proxy: ') + 9
                        token = data[start:start + 19]
                        self.clients[token].sendall(data+DELIMITER)
                        data = recv(self.clients[token])
                        print('>>>>>>>>>')
                        print(data)
                        conn.sendall(data)
                    except Exception as e:
                        if token:
                            del(self.clients[token])
                        print(e)
                        conn.sendall(EMPTY)
                else:
                    conn.sendall(EMPTY)

    def serve_forever(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(self.host)
            s.listen()
            while True:
                try:
                    connection, address = s.accept()
                    threading.Thread(
                        target=self.process, args=(connection, address), daemon=True
                    ).start()
                except KeyboardInterrupt:
                    print('Bye!')
                    break


class Client:

    def __init__(self, proxy=('aplicativo.click', 8080), backend=('127.0.0.1', 8000), frontend=('aplicativo.click', 80), token='0123456789123456789', debug=False):
        self.proxy = proxy
        self.backend = backend
        self.frontend = frontend
        self.token = token
        self.debug = debug

    def process(self, s, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
            if data.startswith(b'GET /favicon.ico '):
                s.sendall(b'HTTP/1.1 404 Not Found\r\n')
            else:
                c.connect(self.backend)
                c.sendall(data)
                data = recvall(c)
                if self.debug:
                    print('>>>>>>>>>')
                    print(data)
                s.sendall(data + DELIMITER)

    def serve_forever(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(self.proxy)
                s.setblocking(True)
                s.sendall('Token {}\r\n\r\n'.format(self.token).encode())
                token = s.recv(19)

                if self.proxy[1] == 80:
                    host = 'http://{}'.format(self.proxy[0])
                else:
                    host = 'http://{}:{}'.format(self.proxy[0], self.proxy[1])

                if self.frontend[1] == 80:
                    url = 'http://{}'.format(self.frontend[0])
                else:
                    url = 'http://{}:{}'.format(self.frontend[0], self.frontend[1])

                url = '{}#{}'.format(
                    url, base64.b64encode(json.dumps(dict(host=host, proxy=self.token)).encode()).decode()
                )

                print('=== APP PROXY ===')
                print('URL: {}'.format(url))
                print('\n\n')

                print('=== API PROXY ===')
                print('URL: {}'.format(host))
                print('HEADER: {}'.format(json.dumps({'X-Proxy': token.decode()})))
                print('\n\n')

                while True:
                    data = recv(s)
                    if self.debug:
                        print('<<<<<<<<<<')
                        print(data)
                    if data:
                        threading.Thread(
                            target=self.process, args=(s, data,), daemon=True
                        ).start()
                    else:
                        break
            except KeyboardInterrupt:
                if self.debug:
                    print('Bye!')

    @staticmethod
    def start():
        client = Client()
        threading.Thread(target=client.serve_forever, daemon=True).start()


if __name__ == '__main__':
    server = Server()
    server.serve_forever()
