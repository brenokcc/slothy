# -*- coding: utf-8 -*-

import json
import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        url = 'https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-24-mun.json'
        data = json.loads(requests.get(url).text)
        output = {}
        for feature in data['features']:
            output[int(feature['properties']['id'])] = feature['geometry']['coordinates'][0]
        print(json.dumps(output))
