# -*- coding: utf-8 -*-

from django.core.management.commands import runserver
# from slothy.api.proxy import Client

PRINT_QRCODE = True


class Command(runserver.Command):
    default_addr = '127.0.0.1'
    default_port = '8000'

    def inner_run(self, *args, **options):
        # url = 'http://127.0.0.1:9000#{}'.format(
        #    base64.b64encode(json.dumps(dict(host='http://127.0.0.1:8080', proxy='1234567890')).encode()).decode()
        # )
        # print(url)
        # Client.start()
        super().inner_run(*args, **options)

    def handle(self, *args, **options):
        super().handle(*args, **options)


