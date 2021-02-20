# -*- coding: utf-8 -*-
import inspect
from slothy.db import utils
from collections import UserDict
from slothy.decorators import dashboard

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


def attr(verbose_name, condition=None, formatter=None, lookups=(), icon=None):
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
            icon=icon,
            formatter=formatter,
            lookups=lookups,
            order=order,
        )
        setattr(func, '_metadata', metadata)
        return func

    return decorate


def fieldset(verbose_name, condition=None, formatter=None, lookups=(), icon=None):
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
            icon=icon,
            formatter=formatter,
            lookups=lookups,
            order=order,
        )
        setattr(func, '_metadata', metadata)
        setdata('fieldset', func, lookups)
        return func

    return decorate


def action(verbose_name, condition=None, formatter=None, lookups=(), category=None, icon=None, message=None, atomic=False):
    def decorate(func):
        func_name = func.__name__
        metadata = getattr(func, '_metadata', {})
        params = []
        if func_name == 'add':
            default_message = 'Cadastro realizado com sucesso'
        elif func_name == 'edit':
            default_message = 'Edição realizada com sucesso'
        elif func_name == 'delete':
            default_message = 'Exclusão realizada com sucesso'
        else:
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
            icon=icon,
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


def setdata(key, func, lookups, formatter=None):
    global order
    order += 1
    verbose_name = getattr(func, '_metadata', {}).get('verbose_name')
    data = dict(
        key=key, verbose_name=verbose_name, name=func.__name__, func=func,
        lookups=lookups, formatter=formatter, order=order
    )
    setattr(func, '__page', data)


def fieldsets(data):
    def decorate(func):
        if isinstance(data, dict):
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
        else:
            metadata = getattr(func, '_metadata', {})
            metadata.update(verbose_name=data)
            setattr(func, '_metadata', metadata)
            setdata('tab', func, None)
        return func

    return decorate


class App(UserDict):

    def __init__(self, request):
        from slothy.api.utils import format_ouput
        super().__init__()
        self.update(type='app')
        for key in ('shortcut', 'card', 'top_bar', 'bottom_bar', 'floating'):
            self[key] = []
            for data in dashboard.DATA.get(key, ()):
                if hasattr(data['func'], 'submit') or hasattr(data['func'], 'view'):
                    module_name = 'forms' if hasattr(data['func'], 'submit') else 'views'
                    self[key].append(
                        dict(
                            icon='apps',
                            url='/api/{}/{}'.format(module_name, data['func'].__name__.lower()),
                            label=module_name,
                        )
                    )
                else:
                    func_name = data['func'].__name__
                    metadata = getattr(data['func'], '_metadata')
                    model = utils.get_model(data['func'])
                    self[key].append(
                        dict(
                            icon=metadata.get('icon') or 'apps',
                            url='/api/{}/{}{}'.format(
                                model.get_metadata('app_label'),
                                model.get_metadata('model_name'),
                                '/{}'.format(func_name) if func_name != 'all' else ''
                            ),
                            label=metadata.get('verbose_name'),
                        )
                    )
        for key in ('top', 'left', 'center', 'right', 'bottom'):
            self[key] = []
            for data in dashboard.DATA.get(key, ()):
                if hasattr(data['func'], 'submit') or hasattr(data['func'], 'view'):
                    output = data['func'](request).serialize()
                else:
                    func_name = data['func'].__name__
                    metadata = getattr(data['func'], '_metadata')
                    model = utils.get_model(data['func'])
                    output = getattr(model.objects, func_name)()
                    output = format_ouput(output, metadata)
                    formatter = data.get('formatter', metadata.get('formatter'))
                    if formatter:
                        output['formatter'] = formatter
                self[key].append(output)

        for key in ('calendar',):
            self[key] = []
            for data in dashboard.DATA.get(key, ()):
                func_name = data['func'].__name__
                metadata = getattr(data['func'], '_metadata')
                verbose_name = metadata['verbose_name']
                model = utils.get_model(data['func'])
                qs = getattr(model.objects, func_name)()
                self[key].append(qs.serialize(verbose_name))
