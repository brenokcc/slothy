# -*- coding: utf-8 -*-

import inspect
import django.db.models.options as options
from slothy.db import utils
from slothy.api import functions

order = 0


setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + ('icon',))


def attr(verbose_name, condition=None, formatter=None, lookups=(), icon=None):
    def decorate(func):
        global order
        order += 1
        functions.append(func)
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='attr',
            verbose_name=verbose_name,
            condition=condition,
            icon=icon,
            formatter=formatter,
            lookups=utils.iterable(lookups),
            order=order,
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def attrs(verbose_name, condition=None, formatter=None, lookups=(), icon=None):
    def decorate(func):
        global order
        order += 1
        functions.append(func)
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='attrs',
            verbose_name=verbose_name,
            condition=condition,
            icon=icon,
            formatter=formatter,
            lookups=lookups,
            order=order,
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def action(verbose_name, condition=None, formatter=None, lookups=(), category=None, icon=None, message=None, atomic=False):
    def decorate(func):
        functions.append(func)
        func_name = func.__name__
        metadata = getattr(func, '_metadata', {})
        params = []
        if func_name == 'add':
            default_message = 'Cadastro realizado com sucesso'
            default_icon = 'add'
        elif func_name == 'edit':
            default_message = 'Edição realizada com sucesso'
            default_icon = 'edit'
        elif func_name == 'delete':
            default_message = 'Exclusão realizada com sucesso'
            default_icon = 'delete'
        else:
            default_icon = None
            default_message = 'Ação realizada com sucesso'

        fields = {}
        for name, parameter in inspect.signature(func).parameters.items():
            if not name == 'self':
                is_annotated = parameter.annotation is not None and parameter.annotation != inspect.Parameter.empty
                if is_annotated:
                    fields[name] = parameter.annotation
                params.append(name)

        metadata.update(
            name=func_name,
            params=params,
            type='action',
            verbose_name=verbose_name,
            condition=condition,
            category=category,
            icon=icon or default_icon,
            formatter=formatter,
            lookups=lookups,
            message=message or default_message,
            atomic=atomic,
            fields=fields
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def param(**kwargs):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        fields = metadata.get('fields', {})
        fields.update(**kwargs)
        metadata.update(fields=fields)
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def fieldsets(data):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        _fieldsets = {}
        for verbose_name, str_or_tuples in data.items():
            _fieldsets[verbose_name] = []
            if isinstance(str_or_tuples, str):  # sigle field
                _fieldsets[verbose_name].append((str_or_tuples,))
            else:  # multiple fields
                for str_or_tuple in str_or_tuples:
                    if isinstance(str_or_tuple, str):  # string
                        _fieldsets[verbose_name].append((str_or_tuple,))
                    else:  # tuple
                        _fieldsets[verbose_name].append(str_or_tuple)
        metadata.update(fieldsets=_fieldsets)
        setattr(func, '_metadata', metadata)
        return func

    return decorate
