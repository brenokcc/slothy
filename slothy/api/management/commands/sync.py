# -*- coding: utf-8 -*-
from slothy.admin.models import User
from django.core.management import call_command
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):

        app_labels = ['admin']
        for app_label in settings.INSTALLED_APPS:
            if '.' not in app_label:
                app_labels.append(app_label)

        call_command('makemigrations', *app_labels)
        call_command('migrate')

        if not User.objects.filter(username='admin').exists():
            user = User.objects.create(username='admin')
            user.set_password('password')
            user.is_superuser = True
            user.save()
            print('The user "admin" with password "password" was created.')
