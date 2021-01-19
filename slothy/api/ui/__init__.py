from django.apps import apps
from slothy.api.utils import format_ouput

initialize = True
data = dict(
    type='app',
)


class App:

    def __init__(self):
        self.shortcuts = []

        global initialize
        if initialize:
            initialize = False

            for model in apps.get_models():
                classes = [model]
                if hasattr(model.objects, '_queryset_class'):
                    classes.append(getattr(model.objects, '_queryset_class'))
                for cls in classes:
                    for attr_name in dir(cls):
                        if attr_name[0] != '_':
                            attr = getattr(cls, attr_name)
                            if hasattr(attr, '_metadata'):
                                metadata = getattr(attr, '_metadata')
                                if 'ui' in metadata:
                                    for element in ('shortcut', 'card'):
                                        for lookups in metadata['ui'].get(element, []):
                                            if element not in data:
                                                data[element] = list()
                                            data[element].append(
                                                dict(
                                                    icon=metadata.get('icon') or 58788,
                                                    url='/api/{}/{}{}'.format(
                                                        model.get_metadata('app_label'),
                                                        model.get_metadata('model_name'),
                                                        '/{}'.format(attr_name) if attr_name != 'all' else ''
                                                    ),
                                                    label=metadata.get('verbose_name'),
                                                    lookups=lookups
                                                )
                                            )
                                    for element in ('top', 'bottom'):
                                        if element not in data:
                                            data[element] = list()


    def serialize(self, user):
        return data
