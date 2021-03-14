# -*- coding: utf-8 -*-

from django.test import TestCase
import json


class ApiTestCase(TestCase):

    @staticmethod
    def log(response):
        print(json.dumps(response, indent=2, sort_keys=False, ensure_ascii=False))

    def get(self, url, data=None):
        data = json.dumps(data) if data is not None else None
        response = self.client.get(url, data=data, content_type='application/json')
        return json.loads(response.content)

    def post(self, url, data=None):
        data = json.dumps(data) if data is not None else None
        response = self.client.post(url, data=data, content_type='application/json')
        return json.loads(response.content)

