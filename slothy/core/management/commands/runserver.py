# -*- coding: utf-8 -*-
import json
import base64
import qrcode
import netifaces
from django.core.management.commands import runserver
from slothy.api.proxy import Client

PRINT_QRCODE = True


class Command(runserver.Command):
    default_addr = '0.0.0.0'
    default_port = '8000'

    def inner_run(self, *args, **options):

        ips = [
            netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
            for iface in netifaces.interfaces() if netifaces.AF_INET in netifaces.ifaddresses(iface)
        ]

        global PRINT_QRCODE
        if PRINT_QRCODE:
            PRINT_QRCODE = False
            urls = []
            for ip in ips:
                if ip != '127.0.0.1':
                    if self.addr == '0.0.0.0' or ip == self.addr:
                        url = 'abrir://aplicativo.click#{}'.format(
                            base64.b64encode(
                                json.dumps(
                                    dict(host='http://{}:{}'.format(ip, self.port))
                                ).encode()
                            ).decode()
                        )
                        urls.append((ip, url))
            for ip, url in urls:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(url)
                qr.make(fit=True)
                # print(ip)
                # qr.print_tty()
                # print(url)
                # print('\n\n\n')
            #url = 'http://127.0.0.1:9000#{}'.format(
            #    base64.b64encode(json.dumps(dict(host='http://127.0.0.1:8080', proxy='1234567890')).encode()).decode()
            #)
            #print(url)

            url = 'http://aplicativo.click#{}'.format(
                base64.b64encode(json.dumps(dict(host='http://127.0.0.1:8000')).encode()).decode()
            )
            print(url)

        # Client.start()
        super().inner_run(*args, **options)

    def handle(self, *args, **options):
        super().handle(*args, **options)


