# -*- coding: utf-8 -*-

import os
import tempfile

from django.conf import settings

from django.http import HttpResponse


class PdfResponse(HttpResponse):

    def __init__(self, html=''):
        import pdfkit
        file_name = tempfile.mktemp('.pdf')
        html = html.replace('/media', settings.MEDIA_ROOT)
        html = html.replace('/static', '{}/{}/static'.format(settings.BASE_DIR, settings.PROJECT_NAME))
        pdfkit.from_string(html, file_name)
        content = open(file_name, "rb").read()
        os.unlink(file_name)
        super().__init__(content=content, content_type='application/pdf')
