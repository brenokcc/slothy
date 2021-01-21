from slothy.api import utils
from collections import UserDict
from slothy.ui import dashboard

order = 0


def setdata(key, func, lookups, priority, formatter=None):
    global order
    order += 1
    verbose_name = getattr(func, '_metadata', {}).get('verbose_name')
    data = dict(key=key, verbose_name=verbose_name, name=func.__name__, func=func, lookups=lookups, priority=priority, formatter=formatter, order=order)
    setattr(func, '__page', data)


def shortcut(lookups=None, priority=0):
    def decorate(func):
        setdata('shortcut', func, lookups, priority)
        return func
    return decorate


def card(lookups=None, priority=0):
    def decorate(func):
        setdata('card', func, lookups, priority)
        return func
    return decorate


def top(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('top', func, lookups, priority, formatter)
        return func
    return decorate


def left(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('left', func, lookups, priority, formatter)
        return func
    return decorate


def center(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('center', func, lookups, priority, formatter)
        return func
    return decorate


def right(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('right', func, lookups, priority, formatter)
        return func
    return decorate


def bottom(lookups=None, priority=0, formatter=None):
    def decorate(func):
        setdata('bottom', func, lookups, priority, formatter)
        return func
    return decorate


def fieldset(lookups=None, priority=0):
    def decorate(func):
        # form fieldset
        if isinstance(lookups, dict):
            metadata = getattr(func, '_metadata', {})
            fieldsets = {}
            for verbose_name, str_or_tuples in lookups.items():
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
        # object fieldset
        else:
            setdata('fieldset', func, lookups, priority)
        return func

    return decorate


def tab(lookups=None, priority=0):
    def decorate(func):
        setdata('tab', func, lookups, priority)
        return func
    return decorate


class App(UserDict):

    def __init__(self, request):
        super().__init__()
        self.update(type='app')
        for key in ('shortcut', 'card', 'top_bar', 'bottom_bar', 'floating'):
            self[key] = []
            for data in dashboard.DATA.get(key, ()):
                if hasattr(data['func'], 'submit') or hasattr(data['func'], 'view'):
                    module_name = 'forms' if hasattr(data['func'], 'submit') else 'views'
                    self[key].append(
                        dict(
                            icon=58788,
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
                            icon=metadata.get('icon') or 58788,
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
                    output = utils.format_ouput(output, metadata)
                    formatter = data.get('formatter', metadata.get('formatter'))
                    if formatter:
                        output['formatter'] = formatter
                self[key].append(output)
