# -*- coding: utf-8 -*-

from django.utils import termcolors
from django.core import management


def call_command(command, *args, **kwargs):
    kwargs.setdefault('interactive', True)
    print(termcolors.make_style(fg='cyan', opts=('bold',))('>>> {} {}{}'.format(
        command, ' '.join(args), ' '.join(['{}={}'.format(k, v) for k, v in list(kwargs.items())]))))
    management.call_command(command, *args, **kwargs)