# -*- coding: utf-8 -*-

import os
import sys
import json
import traceback
import uuid
import slothy
import requests
from slothy.admin import Admin
from django.conf import settings
from django.apps import apps
from django.db import transaction
from django.http import JsonResponse
from django.contrib.auth import logout
from slothy.db.models import ValidationError, ManyToManyField, ValueSet, QuerySet, Model, QuerySetStatistic
from slothy.forms import ModelForm, InputValidationError
from slothy.admin.forms import LoginForm
from slothy.api import export_to_postman
from django.core import signing


slothy.initialize()


def upload(request):
    output = dict()
    for name in request.FILES:
        uploaded_file = request.FILES[name]
        file_name = '{}.{}'.format(uuid.uuid1().hex, uploaded_file.name.split('.')[-1])
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        open(file_path, 'wb').write(uploaded_file.read())
        output.update(
            name=file_name,
            field_name=name,
            path='/media/{}'.format(file_name),
            content_type=uploaded_file.content_type,
            size=uploaded_file.size,
            charset=uploaded_file.charset
        )
    return JsonResponse(output)


def settingss(request):
    output = dict(
        PROJECT_NAME=settings.PROJECT_NAME,
        PROJECT_LOGO=settings.PROJECT_LOGO,
        THEME=settings.THEME,
    )
    return JsonResponse(output)


def queryset(request, app_label, model_name, subset=None):
    model = apps.get_model(app_label, model_name)
    body = request.body
    s = request.POST or body
    metadata = json.loads(s)
    qs = model.objects.load_query(metadata['query'])
    qs.load(metadata)
    # calendar request
    if 'year' in request.GET and 'month' in request.GET:
        if 'day' in request.GET:
            # get data for a specific day of the month
            qs = qs.filter_by_date(int(request.GET['year']), int(request.GET['month']), int(request.GET['day']))
            d = qs.serialize()
        else:
            # count each day of the month
            d = qs.count_by_date(int(request.GET['year']), int(request.GET['month']))
    # simple request
    else:
        if subset:
            qs = qs if subset == 'all' else getattr(qs, subset)()
        d = qs.serialize()
    return JsonResponse(d)


def geolocation(request):
    body = request.body
    s = request.POST or body
    data = json.loads(s)
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={}&inputtype=textquery&fields=formatted_address,name,geometry&key=AIzaSyCcUFnAPOln_KVa6oiQw_DAkvzFd6sSqFw'.format(data['q'])
    response = requests.post(url)
    return JsonResponse(json.loads(response.text))


def postman(request):
    export_to_postman()
    data = dict(
        info=dict(
            _postman_id='b49723c5-ab42-49fc-9b3c-842710e0dc68',
            name='Slothy',
            schema='https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
        ),
        item=[
            dict(
                name='api',
                item=[
                    dict(
                        name='api/admin',
                        request=dict(
                            method='get',
                            header=[],
                            url=dict(
                                raw='http://localhost:8000/api/admin',
                                protocol='http',
                                host=['localhost'],
                                port='8000',
                                path=['api', 'app']
                            )
                        ),
                        response=[]
                    )
                ]
            )
        ],
        variable=dict(
            key='id',
            value='1'
        )
    )
    return JsonResponse(data)


def api(request, path):
    auhtorization = request.headers.get('Authorization', '')
    if auhtorization.startswith('Token'):
        token = auhtorization.split(' ')[-1]
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        request.user = user_model.objects.get(pk=signing.loads(token))
    body = request.body
    if body and body[0] == 123:
        data = json.loads(body)
    else:
        data = None
    # print('# {}'.format(path))
    response = {}
    if path.endswith('/'):
        path = path[0:-1]
    tokens = path.split('/')
    data = request.POST or request.GET or data
    try:
        if len(tokens) == 1:
            if path == 'public':
                response = Admin().public()
            elif path == 'admin':
                response = Admin().admin(request)
            elif path == 'user':  # authenticated user
                if request.user.is_authenticated:
                    response = request.user.view()
                else:
                    response = dict(type='error', text='Usuário não autenticado')
            elif path == 'login':  # user login
                response = LoginForm(request).serialize()
            elif path == 'logout':  # user logout
                logout(request)
                response = dict(type='message', text='Logout realizado com sucesso')
            else:
                response = dict(type='exception', text='Recurso inexistente')
        else:
            if tokens[0] == 'forms':
                form = slothy.FORMS[tokens[1]](request, data=data)
                if data:
                    try:
                        response = form.submit()
                    except ValidationError as ve:
                        error = ''.join(ve.message)
                        raise InputValidationError(error)
                else:
                    response = form.serialize()
            elif tokens[0] == 'markdown':
                markdown = slothy.MARKDOWN[tokens[1]](request)
                response = markdown.serialize()
            elif tokens[0] == 'views':
                view = slothy.VIEWS[tokens[1]](request)
                response = view.serialize()
            elif len(tokens) > 1:
                meta_func = None
                instance = None
                caller = None
                model = apps.get_model(tokens[0], tokens[1])
                exclude_field = None
                if len(tokens) > 2:
                    if tokens[2] == 'add':  # add object
                        instance = model()
                        func = instance.add
                    elif not tokens[2].isdigit():  # manager subset, meta or action
                        meta_func = getattr(getattr(model.objects, '_queryset_class'), tokens[2])
                        try:  # instance method
                            func = getattr(model.objects, tokens[2])
                        except AttributeError:  # class method
                            func = meta_func
                    else:
                        instance = model.objects.get(pk=tokens[2])
                        if len(tokens) == 3:  # view object
                            if data:
                                setattr(instance, '_current_display_name', data.get('dimension'))
                            func = instance.view
                        else:

                            if len(tokens) == 4:  # object attr or action
                                func = getattr(instance, tokens[3])
                                metadata = getattr(func, '_metadata')
                                if metadata['type'] in ('attr', 'attrs'):  # object attr
                                    if metadata['type'] == 'attr':
                                        def func():
                                            return instance.serialize(tokens[3])
                                    else:
                                        def func():
                                            tmp = instance.serialize(tokens[3])
                                            tmp['data'] = tmp['data'][0]['data'][0]['data']
                                            return tmp
                                    setattr(func, '_metadata', metadata)
                            else:  # object relation (add or remove)
                                qs = getattr(instance, tokens[3])()

                                if tokens[4] in ('add', 'remove'):
                                    field = getattr(getattr(qs, '_related_manager'), 'field', None)
                                    if field:  # one-to-many
                                        if tokens[4] == 'add':  # add
                                            value = getattr(qs, '_hints')['instance']
                                            model = qs.model
                                            instance = model()
                                            setattr(instance, field.name, value)
                                            func = instance.add
                                            exclude_field = field.name
                                        else:  # remove
                                            def func():  # remove
                                                qs.remove(int(tokens[5]))
                                            metadata = dict(
                                                name='_',
                                                type='action',
                                                params=[],
                                                verbose_name='Remover',
                                                message='Ação realizada com sucesso',
                                            )
                                            setattr(func, '_metadata', metadata)
                                    else:  # many-to-many
                                        if tokens[4] == 'add':
                                            def func(ids):  # add
                                                for pk in ids:
                                                    qs.add(pk)
                                            metadata = dict(
                                                name='_',
                                                type='action',
                                                params=('ids',),
                                                verbose_name='Adicionar',
                                                message='Ação realizada com sucesso',
                                                fields={'ids': ManyToManyField(
                                                    qs.model,
                                                    verbose_name=qs.model.get_metadata('verbose_name_plural'),
                                                )}
                                            )
                                            setattr(func, '_metadata', metadata)
                                        else:  # remove
                                            def func():
                                                qs.remove(int(tokens[5]))
                                            metadata = dict(
                                                name='_',
                                                type='action',
                                                params=[],
                                                verbose_name='Remover',
                                                message='Ação realizada com sucesso',
                                            )
                                            setattr(func, '_metadata', metadata)
                                else:
                                    func = None
                else:
                    func = model.objects.all
                    meta_func = getattr(model.objects, '_queryset_class').all

                metadata = getattr(meta_func or func, '_metadata')
                if metadata['type'] == 'action' and metadata['name'] != 'view':
                    form_cls = build_form(model, func, metadata, exclude_field)
                    form = form_cls(data=data or None, instance=instance, request=request)
                    if data is not None:
                        if metadata.get('atomic'):
                            with transaction.atomic():
                                form.save()
                        else:
                            form.save()
                        if form.result is None:
                            response = dict(type="message", text=metadata.get('message'))
                        else:
                            response = form.result.serialize()
                    else:
                        response = form.serialize(request.path)
                else:
                    try:
                        output = func()
                        if output is None:
                            response = dict(type="message", text=metadata.get('message'))
                        elif isinstance(output, QuerySet):
                            output = output.apply_lookups(request.user)
                            if metadata['name'] == 'all':
                                name = metadata['verbose_name']
                            else:
                                if model.get_metadata('verbose_name_plural') == metadata['verbose_name']:
                                    name = metadata['verbose_name']
                                else:
                                    name = '{} {}'.format(
                                        model.get_metadata('verbose_name_plural'),
                                        metadata['verbose_name']
                                    )
                            response = output.serialize(name, icon=metadata['icon'])
                            response['formatter'] = metadata.get('formatter')
                        elif isinstance(output, Model):
                            response = output.serialize()
                        elif isinstance(output, ValueSet):
                            response = output.serialize()
                        elif isinstance(output, QuerySetStatistic):
                            response = output.serialize(metadata['verbose_name'])
                            response['formatter'] = metadata.get('formatter')
                        else:
                            response = output

                        if response.get('type') == 'object':
                            response['path'] = request.path

                    except ValidationError as e:
                        response = dict(type='error', text=e.message)
            else:
                response = dict(type='exception', text='Recurso inexistente')

    except InputValidationError as e:
        response = dict(type='error', text=e.error, errors=e.errors)
    except BaseException as e:
        traceback.print_exc(file=sys.stdout)
        response = dict(type='exception', text=str(e))

    output = JsonResponse(response)
    output["Access-Control-Allow-Origin"] = "*"
    output["Access-Control-Allow-Headers"] = "*"
    return output


def build_form(_model, func, metadata, exclude_field):
    params = metadata.get('params', {})
    fields = metadata.get('fields', {})
    fieldsets = metadata.get('fieldsets')
    if func.__name__ == 'edit' and fieldsets is None:
        fieldsets = getattr(getattr(func.__self__, 'add'), '_metadata', {}).get('fieldsets')

    if fieldsets:
        _exclude = None
        _fields = []
        for verbose_name, field_lists in fieldsets.items():
            for field_list in field_lists:
                for field_name in field_list:
                    if field_name not in fields:
                        _fields.append(field_name)
    else:
        if metadata['name'] in ('add', 'edit'):
            _fields = None
            _exclude = ()
        else:
            _fields = [name for name in params if name not in fields]
            _exclude = None

    class Form(ModelForm):

        class Meta:
            model = _model
            fields = _fields
            exclude = _exclude

        def __init__(self, *args, **kwargs):
            super().__init__(
                title=metadata['verbose_name'], func=func, params=metadata['params'], exclude=exclude_field,
                fields=fields, fieldsets=fieldsets, **kwargs
            )

    return Form

