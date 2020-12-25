# -*- coding: utf-8 -*-


def role(field='id'):
    def decorate(cls):
        metadata = getattr(cls, '_metadata', {})
        metadata.update(role_field_name=field)
        setattr(cls, '_metadata', metadata)
        return cls

    return decorate


def meta(verbose_name, formatter=None, lookups=(), add_lookups=(), remove_lookups=()):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='meta',
            verbose_name=verbose_name,
            formatter=formatter,
            lookups=lookups,
            add_lookups=add_lookups,
            remove_lookups=remove_lookups
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def action(verbose_name, lookups=(), condition=None, message=None, category=None, style=None, icon=None, modal=True):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='action',
            scope=None,
            verbose_name=verbose_name,
            condition=condition,
            lookups=lookups,
            message=message,
            category=category,
            style=style,
            icon=icon,
            modal=modal,
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def classaction(verbose_name, lookups=(), condition=None, message=None, category=None, style=None, icon=None, modal=True):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='action',
            scope='class',
            verbose_name=verbose_name,
            condition=condition,
            lookups=lookups,
            message=message,
            category=category,
            style=style,
            icon=icon,
            modal=modal
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


action.input = param
classaction.input = param

