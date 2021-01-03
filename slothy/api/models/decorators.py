# -*- coding: utf-8 -*-
from collections import OrderedDict

order = 0


def user(username_field_name):
    def decorate(cls):
        cls.USERNAME_FIELD = username_field_name
        return cls

    return decorate


def role(field='id'):
    def decorate(cls):
        metadata = getattr(cls, '_metadata', {})
        metadata.update(role_field_name=field)
        setattr(cls, '_metadata', metadata)
        return cls

    return decorate


def fieldset(verbose_name, fields):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        fieldsets = metadata.get('fieldsets', OrderedDict())
        fieldsets[verbose_name] = type(fields) != str and [
            type(str_or_tuple) == str and (str_or_tuple,) or str_or_tuple for str_or_tuple in fields
        ] or fields
        metadata.update(
            fieldsets=fieldsets
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def viewset(verbose_name, condition=None, lookups=(), category=None, icon=None):
    def decorate(func):
        global order
        order += 1
        metadata = getattr(func, '_metadata', {})
        metadata.update(
            name=func.__name__,
            type='viewset',
            verbose_name=verbose_name,
            condition=condition,
            category=category,
            icon=icon,
            lookups=lookups,
            order=order
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def attr(verbose_name, condition=None, formatter=None, lookups=(), category=None, icon=None):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='attr',
            verbose_name=verbose_name,
            condition=condition,
            category=category,
            icon=icon,
            formatter=formatter,
            lookups=lookups
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def action(verbose_name, condition=None, formatter=None, lookups=(), category=None, icon=None, message=None, atomic=False):
    def decorate(func):
        name = func.__name__
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        if name == 'add':
            default_message = 'Cadastro realizado com sucesso'
        elif name == 'edit':
            default_message = 'Edição realizada com sucesso'
        elif name == 'remove':
            default_message = 'Exclusão realizada com sucesso'
        else:
            default_message = None
        metadata.update(
            name=name,
            params=params,
            type='action',
            verbose_name=verbose_name,
            condition=condition,
            category=category,
            icon=icon,
            formatter=formatter,
            lookups=lookups,
            message=message or default_message,
            atomic=atomic
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


