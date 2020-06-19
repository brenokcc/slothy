# -*- coding: utf-8 -*-

import os
from django.conf import settings
from django.utils import termcolors
from django.core.management import call_command
from django.core.management.base import BaseCommand


def print_and_call(command, *args, **kwargs):
    kwargs.setdefault('interactive', True)
    print(termcolors.make_style(fg='cyan', opts=('bold',))('>>> {} {}{}'.format(
        command, ' '.join(args), ' '.join(['{}={}'.format(k, v) for k, v in list(kwargs.items())]))))
    call_command(command, *args, **kwargs)


class Command(BaseCommand):
    def handle(self, *args, **options):

        app_labels = []
        for app_label in settings.INSTALLED_APPS:
            if '.' not in app_label:
                app_labels.append(app_label)

        print_and_call('makemigrations', *app_labels)
        print_and_call('migrate')
