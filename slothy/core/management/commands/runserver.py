# -*- coding: utf-8 -*-
import qrcode
import netifaces
from django.core.management.commands import runserver

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
                        url = 'abrir://aplicativo.click?host={}&port={}'.format(ip, self.port)
                        urls.append(url)
            url = 'http://aplicativo.click/#host=127.0.0.1&port=8000'
            urls.append(url)
            for url in urls:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(url)
                qr.make(fit=True)
                qr.print_tty()
                print(url)
                print('\n\n\n')
        super().inner_run(*args, **options)

    def handle(self, *args, **options):
        super().handle(*args, **options)


