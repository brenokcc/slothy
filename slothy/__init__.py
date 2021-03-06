from django.conf import settings
from slothy import forms

FORMS = {}
VIEWS = {}
MARKDOWN = {}
INITIALIZED = False


def initialize():
    global INITIALIZED
    if not INITIALIZED:
        INITIALIZED = True
        for module_name in ('forms', 'views'):
            for app_label in settings.INSTALLED_APPS[5:]:
                try:
                    module = __import__('{}.{}'.format(
                        app_label, module_name
                    ), fromlist=app_label.split('.'))
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if hasattr(attr, 'submit'):
                            FORMS[attr_name.lower()] = attr
                        if hasattr(attr, 'view'):
                            VIEWS[attr_name.lower()] = attr
                        if hasattr(attr, 'markdown'):
                            MARKDOWN[attr_name.lower()] = attr
                except ImportError as e:
                    if not e.msg.startswith('No module named'):
                        raise e
