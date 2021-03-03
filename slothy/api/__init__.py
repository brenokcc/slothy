

functions = []


def export_to_postman():
    for func in functions:
        metadata = getattr(func, '_metadata')
        app_label = func.__module__.split('.')[-2]
        cls_name, function_name = func.__qualname__.split('.')
        if cls_name.endswith('Set') or function_name == 'add':
            model_name = cls_name[0:-3].lower()
            url = '/api/{}/{}/{}'.format(app_label, model_name, function_name)
        else:
            model_name = cls_name.lower()
            url = '/api/{}/{}/{{{{id}}}}/{}'.format(app_label, model_name, function_name)
        print(url, metadata.get('params', ()))
    return {}
