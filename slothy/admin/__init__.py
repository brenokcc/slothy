# -*- coding: utf-8 -*-

import inspect
from slothy.db import utils

METADATA = dict()


def store(key, func, lookups, priority, formatter=None):
    if key not in METADATA:
        METADATA[key] = []
    METADATA[key].append(
        dict(func=func, lookups=lookups, priority=priority, formatter=formatter)
    )


class Admin(dict):

    def __init__(self):

        super().__init__()

    def public(self):
        links = [dict(icon='apps', url='/api/login/', label='')]
        for data in METADATA.get('public', ()):
            links.append(utils.get_link(data['func']))
        self.update(type='public')
        self.update(links=links)
        return self

    def admin(self, request):
        self.update(type='admin')
        from slothy.api.utils import format_ouput
        for key in ('shortcut', 'card', 'top_bar', 'bottom_bar', 'floating'):
            self[key] = []
            for data in METADATA.get(key, ()):
                link = utils.get_link(data['func'], user=request.user)
                if link:
                    self[key].append(link)
        for key in ('top', 'left', 'center', 'right', 'bottom'):
            self[key] = []
            for data in METADATA.get(key, ()):
                if inspect.isclass(data['func']):
                    output = data['func'](request).serialize()
                else:
                    func_name = data['func'].__name__
                    metadata = getattr(data['func'], '_metadata')
                    model = utils.get_model(data['func'])
                    output = getattr(model.objects, func_name)()
                    if hasattr(output, 'values_list'):
                        output = output.apply_lookups(request.user)
                        if not output.exists():
                            continue
                    output = format_ouput(output, metadata)
                    formatter = data.get('formatter', metadata.get('formatter'))
                    if formatter:
                        output['formatter'] = formatter
                self[key].append(output)

        for key in ('calendar',):
            self[key] = []
            for data in METADATA.get(key, ()):
                func_name = data['func'].__name__
                metadata = getattr(data['func'], '_metadata')
                verbose_name = metadata['verbose_name']
                model = utils.get_model(data['func'])
                qs = getattr(model.objects, func_name)()
                self[key].append(qs.apply_lookups(request.user).serialize(verbose_name))

        return self
