# -*- coding: utf-8 -*-
from django.core.management import call_command
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):

        app_labels = []
        for app_label in settings.INSTALLED_APPS:
            if '.' not in app_label:
                app_labels.append(app_label)

        call_command('makemigrations', *app_labels)
        call_command('migrate')
