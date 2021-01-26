# -*- coding: utf-8 -*-

import os
import sys
import json
import traceback
import uuid
import tempfile
import pdfkit
import slothy
from slothy.decorators import App
from django.conf import settings
from django.apps import apps
from django.db import transaction
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from slothy.db.models import ValidationError, ManyToManyField, ValueSet, QuerySet, Model
from slothy.forms import ModelForm, InputValidationError


slothy.initialize()


class PdfResponse(HttpResponse):

    def __init__(self, html=''):
        file_name = tempfile.mktemp('.pdf')
        html = html.replace('/media', settings.MEDIA_ROOT)
        html = html.replace('/static', '{}/{}/static'.format(settings.BASE_DIR, settings.PROJECT_NAME))
        pdfkit.from_string(html, file_name)
        content = open(file_name, "rb").read()
        os.unlink(file_name)
        super().__init__(content=content, content_type='application/pdf')


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class UploadView(APIView):
    def post(self, request):
        ouput = dict()
        for name in request.FILES:
            uploaded_file = request.FILES[name]
            file_name = '{}.{}'.format(uuid.uuid1().hex, uploaded_file.name.split('.')[-1])
            file_path = os.path.join(settings.MEDIA_ROOT, file_name)
            open(file_path, 'wb').write(uploaded_file.read())
            ouput.update(
                name=file_name,
                field_name=name,
                path='/media/{}'.format(file_name),
                content_type=uploaded_file.content_type,
                size=uploaded_file.size,
                charset=uploaded_file.charset
            )
        return HttpResponse(json.dumps(ouput))


class QuerysetView(APIView):
    def post(self, request, app_label, model_name, subset=None):
        model = apps.get_model(app_label, model_name)
        body = request.body
        s = request.POST or body
        metadata = json.loads(s)
        qs = model.objects.load_query(metadata['query'])
        qs.load(metadata)
        if subset:
            qs = qs if subset == 'all' else getattr(qs, subset)()
        d = qs.serialize()
        return Response(d)

    def get(self, *args, **kwargs):
        return Response({})


class Api(APIView):
    authentication_classes = CsrfExemptSessionAuthentication, TokenAuthentication

    def options(self, request, service, path):
        return self.do(request, service, path, {})

    def get(self, request, service, path):
        body = request.body
        if body and body[0] == 123:
            data = json.loads(body)
        else:
            data = {}
        return self.do(request, service, path, data)

    def post(self, request, service, path):
        body = request.body
        if body and body[0] == 123:
            data = json.loads(body)
        else:
            data = {}
        return self.do(request, service, path, data)

    def do(self, request, service, path, data):
        # print('# {}'.format(path))
        response = {}
        if path.endswith('/'):
            path = path[0:-1]
        tokens = path.split('/')
        data = request.POST or request.GET or data
        try:
            if len(tokens) == 1:
                if path == 'app':  # authenticated user
                    response = App(request)
                elif path == 'user':  # authenticated user
                    if request.user.is_authenticated:
                        response = request.user.view()
                    else:
                        response = dict(type='error', text='Usuário não autenticado')
                elif path == 'login':  # user login
                    if data:
                        user = authenticate(request, username=data['username'], password=data['password'])
                        if user:
                            login(request, user)
                            token = dict(token=request.user.auth_token.key)
                            response = dict(type='message', text='Login realizado com sucesso', data=token)
                        else:
                            response = dict(type='error', text='Usuário e senha não conferem')
                    else:
                        response = dict(
                            type='form',
                            input=dict(username=None, password=None),
                            fieldsets={
                                'Acesso ao Sistema': {
                                    'username': dict(
                                        label='Login', type='char', required=True, mask=None,
                                        value=None,choices=None, help_text=None
                                    ),
                                    'password': dict(
                                        label='Senha', type='password', required=True, mask='',
                                        value=None, choices=None, help_text=None
                                    )
                                }
                            }
                        )
                elif path == 'logout':  # user logout
                    logout(request)
                    response = dict(type='message', text='Logout realizado com sucesso')
                else:
                    response = dict(type='exception', text='Recurso inexistente')
            else:
                if tokens[0] == 'forms':
                    form = slothy.FORMS[tokens[1]](request, data=data)
                    if data:
                        form.submit()
                    response = form.serialize()
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
                                setattr(instance, '_current_display_name', data.get('dimension'))
                                func = instance.view
                            else:

                                if len(tokens) == 4:  # object subset, meta or action
                                    func = getattr(instance, tokens[3])  # object meta or action
                                    caller = dict(
                                        app_label=tokens[0],
                                        model_name=tokens[1],
                                        id=tokens[2],
                                        attr_name=tokens[3],
                                    )
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
                    form_cls = self.build_form(model, func, metadata, exclude_field)
                    if form_cls:
                        form = form_cls(data=data or None, instance=instance)
                        if data:
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
                            elif caller and metadata['type'] == 'attr':
                                if isinstance(output, ValueSet) and output.nested:
                                    response = dict(type='object', name=str(instance), data=output)
                                else:
                                    if isinstance(output, QuerySet):
                                        setattr(output, '_caller', caller)
                                    fieldset = {metadata['verbose_name']: output.serialize() if hasattr(
                                        output, 'serialize') else output}
                                    response = dict(type='object', name=str(instance), data=fieldset)
                            elif isinstance(output, QuerySet):
                                if metadata['name'] == 'all':
                                    name = metadata['verbose_name']
                                else:
                                    name = '{} {}'.format(
                                        model.get_metadata('verbose_name_plural'),
                                        metadata['verbose_name']
                                    )
                                response = output.serialize(name)
                                formatter = metadata.get('formatter')
                                if formatter:
                                    response['formatter'] = formatter
                            elif isinstance(output, Model):
                                response = output.serialize()
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

        if service == 'pdf':
            return PdfResponse()
        else:
            output = Response(response)
            output["Access-Control-Allow-Origin"] = "*"
            return output

    def build_form(self, _model, func, metadata, exclude_field):
        # print(metadata)
        if 'params' in metadata:
            custom_fields = metadata.get('fields', {})
            fields = []
            fieldsets = metadata.get('fieldsets')
            if fieldsets:
                for verbose_name, field_lists in fieldsets.items():
                    for field_list in field_lists:
                        for field_name in field_list:
                            fields.append(field_name)
            if metadata['params']:
                # we are adding or editing an object and all params are custom fields
                if metadata['name'] in ('add', 'edit') and len(metadata['params']) == len(custom_fields):
                    _fields = fields or None
                    _exclude = ()
                # the params are both own and custom fields, so lets explicitally specify the form fields
                else:
                    _fields = [name for name in metadata['params'] if name not in custom_fields]
                    _exclude = None
            else:
                # lets include all model fields
                if metadata['name'] in ('add', 'edit'):
                    _fields = fields or None
                    _exclude = ()
                else:  # lets include no model fields
                    if custom_fields:
                        _fields = ()
                        _exclude = None
                    else:  # no form is needed
                        return None

            class Form(ModelForm):

                class Meta:
                    model = _model
                    fields = _fields
                    exclude = _exclude

                def __init__(self, *args, **kwargs):
                    super().__init__(
                        title=metadata['verbose_name'], func=func, params=metadata['params'], exclude=exclude_field,
                        fields=custom_fields, fieldsets=fieldsets, **kwargs
                    )

            return Form
        return None
