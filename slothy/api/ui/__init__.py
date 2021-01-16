from django.apps import apps

initialize = True
shortcuts = []


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
                                if metadata.get('shortcut'):
                                    shortcuts.append(
                                        dict(
                                            icon=metadata.get('icon') or 58788,
                                            url='/api/{}/{}{}'.format(
                                                model.get_metadata('app_label'),
                                                model.get_metadata('model_name'),
                                                '/{}'.format(attr_name) if attr_name != 'all' else ''
                                            ),
                                            label=metadata.get('verbose_name')
                                        )
                                    )

    def serialize(self, user):
        self.shortcuts = shortcuts
        return dict(
            type='app',
            shortcuts=shortcuts
        )
