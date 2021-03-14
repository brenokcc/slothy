# -*- coding: utf-8 -*-

from django.http import JsonResponse
from slothy.db import utils
from slothy.admin import METADATA
from django.shortcuts import redirect


def index(request):
    return redirect('/static/app/index.html', permanent=True)


def public(request):
    data = {}
    links = [dict(icon='apps', url='/api/login/', label='')]
    for metadata in METADATA.get('public', ()):
        links.append(utils.get_link(metadata['func']))
    data['type'] = 'public'
    data['links'] = links
    return JsonResponse(data)

