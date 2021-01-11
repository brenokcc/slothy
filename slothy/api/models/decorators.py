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


def fieldset(dictionary):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        fieldsets = {}
        for verbose_name, str_or_tuples in dictionary.items():
            fieldsets[verbose_name] = []
            if isinstance(str_or_tuples, str):  # sigle field
                fieldsets[verbose_name].append((str_or_tuples,))
            else:  # multiple fields
                for str_or_tuple in str_or_tuples:
                    if isinstance(str_or_tuple, str):  # string
                        fieldsets[verbose_name].append((str_or_tuple,))
                    else:  # tuple
                        fieldsets[verbose_name].append(str_or_tuple)

        metadata.update(
            fieldsets=fieldsets
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def attr(verbose_name, condition=None, formatter=None, lookups=(), category=None, icon=None, display=False):
    def decorate(func):
        global order
        order += 1
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
            lookups=lookups,
            order=order,
            display=display
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
        elif name == 'delete':
            default_message = 'Exclusão realizada com sucesso'
        else:
            default_message = 'Ação realizada com sucesso'
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


def ui(shortcut):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        metadata.update(shortcut=shortcut)
        setattr(func, '_metadata', metadata)
        return func

    return decorate


