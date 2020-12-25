# -*- coding: utf-8 -*-


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


def meta(verbose_name, condition=None, formatter=None, lookups=(), list_lookups=(), add_lookups=(), remove_lookups=(), category=None, icon=None, modal=True):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        params = func.__code__.co_varnames[1:func.__code__.co_argcount]
        metadata.update(
            name=func.__name__,
            params=params,
            type='meta',
            verbose_name=verbose_name,
            condition=condition,
            category=category,
            icon=icon,
            modal=modal,
            formatter=formatter,
            lookups=lookups,
            add_lookups=add_lookups,
            list_lookups=list_lookups,
            remove_lookups=remove_lookups
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


