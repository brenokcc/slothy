# -*- coding: utf-8 -*-

import datetime


def format_value(value):
    from slothy.db.models import QuerySet
    if value is not None:
        if isinstance(value, datetime.datetime):
            return value.strftime('%d/%m/%Y %H:%M')
        elif isinstance(value, datetime.date):
            return value.strftime('%d/%m/%Y')
        elif isinstance(value, bool):
            return 'Sim' if value else 'Não'
        elif isinstance(value, QuerySet) or isinstance(value, list):
            if value:
                return ','.join([str(obj) for obj in value])
        else:
            return str(value)
    return None


def format_ouput(output, metadata):
    from slothy.db import models
    if isinstance(output, models.QuerySet):
        if metadata['name'] == 'all':
            name = metadata['verbose_name']
        else:
            name = '{} {}'.format(
                output.model.get_metadata('verbose_name_plural'),
                metadata['verbose_name']
            )
        response = output.serialize(name)
    elif isinstance(output, models.QuerySetStatistic):
        response = output.serialize(metadata['verbose_name'])
        response['formatter'] = metadata['formatter']
    elif isinstance(output, models.Model):
        response = output.serialize()
    else:
        response = output
    return response


def make_choices(name, field, custom_choices):
    from django.forms.fields import BooleanField
    if name in custom_choices:
        choices = []
        for obj in custom_choices[name]:
            choices.append([obj.id, str(obj)])
        return choices
    elif hasattr(field, 'choices'):
        if hasattr(field.choices, 'queryset'):
            if field.choices.queryset.count() < 1:
                choices = []
                for obj in field.choices.queryset:
                    choices.append([obj.id, str(obj)])
                return choices
            else:
                return field.choices.queryset.display('__str__').serialize(field.label)
        else:
            return field.choices
    else:
        if isinstance(field, BooleanField):
            return [[True, 'Sim'], [False, 'Não']]
    return None

