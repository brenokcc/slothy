# -*- coding: utf-8 -*-
import datetime
import inspect
from django.apps import apps


def iterable(string_or_iterable):
    if string_or_iterable is not None:
        if type(string_or_iterable) not in (list, tuple):
            return string_or_iterable,
    return string_or_iterable


def get_model(func):
    app_label = inspect.getmodule(func).__name__.split('.')[-2]
    model_name = func.__qualname__.split('.')[0].replace('Set', '')
    try:
        return apps.get_model(app_label, model_name)
    except LookupError:
        return None


def get_link(func_or_class, user=None):
    if inspect.isclass(func_or_class):
        module_name = None
        if hasattr(func_or_class, 'submit'):
            module_name = 'forms'
        elif hasattr(func_or_class, 'view'):
            module_name = 'views'
        elif hasattr(func_or_class, 'markdown'):
            module_name = 'markdown'
        url = '/api/{}/{}'.format(module_name, func_or_class.__name__.lower())
        return dict(icon=None, url=url, title='', subtitle='')
    else:
        func_name = func_or_class.__name__
        metadata = getattr(func_or_class, '_metadata')
        model = get_model(func_or_class)
        if model().check_lookups(func_name, user):
            return dict(
                icon=metadata.get('icon') or model.get_metadata('icon'),
                url='/api/{}/{}{}'.format(
                    model.get_metadata('app_label'),
                    model.get_metadata('model_name'),
                    '/{}'.format(func_name) if func_name != 'all' else ''
                ),
                title=model.get_metadata('verbose_name_plural'),
                subtitle=metadata.get('verbose_name')
            )


def getattrr(obj, args, request=None):
    if args == '__str__':
        splitargs = [args]
    else:
        splitargs = args.split('__')
    return _getattr_rec(obj, splitargs, request=request)


def _getattr_rec(obj, attrs, request=None):
    attr_name = attrs.pop(0)
    if obj is not None:
        attr = getattr(obj, attr_name)
        # manager or relation
        if hasattr(attr, 'all'):
            value = attr.all()
        # method in model or manager
        elif callable(attr) and (hasattr(obj, 'pk') or hasattr(obj, '_queryset_class')):
            if hasattr(obj, 'pk'):  # model
                metadata = getattr(attr, '_metadata', {})
            else:  # manager
                metadata = getattr(getattr(getattr(obj, '_queryset_class'), attr_name), '_metadata')

            def value(*args, **kwargs):
                _value = attr(*args, **kwargs)
                return _value

            value._metadata = metadata
        # primitive type
        else:
            value = attr
        return _getattr_rec(value, attrs, request=request) if attrs else value
    return None


def serialize(obj, detail=False):
    from django.db.models.fields.files import FieldFile
    from slothy.db.models import QuerySet, ValueSet, Model, QuerySetStatistic
    if isinstance(obj, bool):
        return obj and 'Sim' or 'Não'
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%d/%m/%Y %H:%M')
    elif isinstance(obj, datetime.date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, QuerySetStatistic):
        return obj.serialize(name='')
    elif isinstance(obj, QuerySet):
        if detail:
            return obj.serialize()
        else:
            return ', '.join((str(instance) for instance in obj)) or None
    elif isinstance(obj, ValueSet):
        if detail:
            return dict(type='valueset', fields=obj.get_nested_values(), actions=obj.action_list)
        else:
            for key in obj:
                obj[key] = serialize(obj[key], detail=False)
            return obj
    elif isinstance(obj, Model):
        return str(obj)
    elif isinstance(obj, FieldFile):
        return obj.name or None
    elif isinstance(obj, dict):
        if detail:
            for key in obj:
                obj[key] = serialize(obj[key], detail=False)
            return dict(
                type='valueset',
                fields=[[dict(name=k, label=k, value=v, formatter=None)] for k, v in obj.items()],
                actions=[]
            )
        else:
            pass
    return obj
