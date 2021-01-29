# -*- coding: utf-8 -*-


from django.core.management import call_command
import os


def load_fixture(apps, schema_editor):
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(base_dir, 'fixtures/initial_data.json.zip')
    call_command('loaddata', file_path)