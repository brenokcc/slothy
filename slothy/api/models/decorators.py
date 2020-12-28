# -*- coding: utf-8 -*-

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


def fieldset(verbose_name, condition=None, formatter=None, lookups=(), category=None, icon=None):
    def decorate(func):
        global order
        order += 1
        metadata = getattr(func, '_metadata', {})
        metadata.update(
            name=func.__name__,
            type='fieldset',
            verbose_name=verbose_name,
            condition=condition,
            category=category,
            icon=icon,
            formatter=formatter,
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


def action(verbose_name, condition=None, formatter=None, lookups=(), category=None, icon=None):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='action',
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


def param(**kwargs):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        fields = metadata.get('fields', {})
        fields.update(**kwargs)
        metadata.update(fields=fields)
        setattr(func, '_metadata', metadata)
        return func

    return decorate


