# -*- coding: utf-8 -*-
import types


def expose(*args, **kwargs):
    def decorate(target):
        if isinstance(target, types.FunctionType):  # function
            expose_dict = getattr(target, 'expose', {})
            expose_dict.update({target.__name__: args})
            for func_name, lookups in kwargs.items():
                expose_dict.update(**{'{}__{}'.format(target.__name__, func_name): lookups})
            setattr(target, 'expose', expose_dict)
        else:  # class
            for func_name, lookups in kwargs.items():
                expose_dict = target.get_metadata('expose', {})
                expose_dict[func_name] = lookups
                target.set_metadata('expose', expose_dict)
        return target
    return decorate


def meta(verbose_name, formatter=None, lookups=(), actions=(), **kwargs):
    def decorate(func):
        metadata = getattr(func, '_metadata', {})
        metadata.update(
            name=func.__name__,
            type='meta',
            verbose_name=verbose_name,
            formatter=formatter,
            lookups=lookups,
            actions=actions
        )
        metadata.update(kwargs)
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def action(verbose_name, lookups=(), condition=None, message=None, category=None, style=None, icon=None, popup=True):
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
            popup=popup,
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def classaction(verbose_name, lookups=(), condition=None, message=None, category=None, style=None, icon=None, popup=True):
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
            popup=popup
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

