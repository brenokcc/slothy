from slothy.api import utils
from collections import UserDict
from slothy.ui import dashboard


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
