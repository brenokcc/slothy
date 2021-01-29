# -*- coding: utf-8 -*-

import os
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        file_path = os.path.join(base_dir, 'fixtures/cidades.json.zip')
        print(file_path)
        call_command('loaddata', file_path)
