import sys
import json
import traceback
from django.apps import apps
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.forms import ModelForm
from slothy.api import utils
from django.forms import modelform_factory
from collections import OrderedDict
from slothy.api.models import ValidationError, ManyToManyField


class InputValidationError(BaseException):
    def __init__(self, errors, metadata):
        self.errors = errors
        self.metadata = metadata


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class QuerysetView(APIView):
    def post(self, request, app_label, model_name, filter_name=None):
        model = apps.get_model(app_label, model_name)
        body = request.body
        s = request.POST and request.POST['metadata'] or body
        qs = model.objects.loads(s)
        if filter_name:
            field = qs.model.get_field(filter_name)
            list_display = ['id']
            for filter_display in field.filter_display:
                list_display.append(filter_display)
            qs = field.related_model.objects.filter(
                pk__in=qs.values_list(filter_name).distinct()
            ).list_display(*list_display)

            return Response(qs.serialize())
        return Response(qs.serialize()['data'])

    def get(self, request, app_label, model_name, filter_name=None):
        return Response({})


class Api(APIView):
    authentication_classes = CsrfExemptSessionAuthentication, TokenAuthentication

    def options(self, request, path):
        return self.do(request, path, {}, {})

    def get(self, request, path):
        body = request.body
        if body and body[0] == 123:
            data = json.loads(body)
        else:
            data = {}
        # data = {}
        # for key in request.GET:
        #     data[key] = request.GET[key]
        return self.do(request, path, data)

    def post(self, request, path):
        body = request.body
        if body and body[0] == 123:
            data = json.loads(body)
        else:
            data = {}
        # data = {}
        # if request.POST:  # browser
        #     for key in request.POST:
        #         data[key] = request.POST[key]
        #     if request.FILES:
        #         for key in request.FILES:
        #             data[key] = request.FILES[key]
        # else:  # nodejs
        #     data = json.loads(body or '{}')
        return self.do(request, path, data)

    def do(self, request, path, data):
        print('# {}'.format(path))
        data = request.POST or request.GET or data
        input_dict = dict(data={}, metadata={})
        response = dict(path='/{}'.format(path), message=None, exception=None, errors=[], input=input_dict, output=None)
        try:
            if path.endswith('/'):
                path = path[0:-1]
            tokens = path.split('/')
            if len(tokens) == 1:
                if path == 'user':  # authenticated user
                    if request.user.is_authenticated:
                        response['output'] = request.user.values()
                elif path == 'login':  # user login
                    if data:
                        user = authenticate(request, username=data['username'], password=data['password'])
                        if user:
                            login(request, user)
                            response['output'] = dict(token=request.user.auth_token.key)
                            response['message'] = 'Login realizado com sucesso'
                        else:
                            response['output'] = dict(token=None)
                            response['errors'].append({'message': 'Usuário não autenticado', 'field': None})
                    response['input']['data'] = dict(username=None, password=None)
                    response['input']['metadata']['username'] = dict(
                        name='username', label='Login', required=True,
                        mask=None, value=None, choices=None, help_text=None
                    )
                    response['input']['metadata']['password'] = dict(
                        name='password', label='Senha', required=True,
                        mask='*****', value=None, choices=None, help_text=None
                    )
                elif path == 'logout':  # user logout
                    logout(request)
                    response['message'] = 'Logout realizado com sucesso'
            else:
                if len(tokens) > 1:
                    meta_func = None
                    instance = None
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
                                setattr(instance, '_current_category_name', request.GET.get('category'))
                                func = instance.view
                            else:
                                if len(tokens) == 4:  # object subset, meta or action
                                    func = getattr(instance, tokens[3])  # object meta or action
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

                                                def func():  # add or remove
                                                    pk = qs.get(pk=data['id'])
                                                    qs.remove(pk)
                                                metadata = dict(
                                                    name='_',
                                                    message='Ação realizada com sucesso'
                                                )
                                                setattr(func, '_metadata', metadata)
                                                response['input']['data'] = {'id': None}
                                        else:  # many-to-many

                                            def func(ids):  # add or remove
                                                for pk in ids:
                                                    getattr(qs, tokens[4])(pk)
                                            metadata = dict(
                                                name='_',
                                                params=('ids',),
                                                message='Ação realizada com sucesso',
                                                fields={'ids': ManyToManyField(qs.model, 'Pontos Turísticos')}
                                            )
                                            setattr(func, '_metadata', metadata)
                                            response['input']['data'] = {'ids': None}
                                    else:
                                        func = None
                    else:
                        func = model.objects.list
                        meta_func = getattr(model.objects, '_queryset_class').list

                    output, metadata = self.apply(model, func, meta_func or func, instance, data, exclude_field)
                    if output is not None:
                        if isinstance(output, dict):
                            response['output'] = output
                        else:
                            response['output'] = output.serialize()
                    response['input']['metadata'] = metadata
                    for field_name in metadata:
                        value = None
                        if type(metadata[field_name]) == list:
                            value = [{}]
                            for inner_field_name in metadata[field_name][0]:
                                value[0][inner_field_name] = None
                        response['input']['data'][field_name] = value
                    response['message'] = getattr(meta_func or func, '_metadata', {}).get('message')

        except InputValidationError as e:
            response['errors'] = e.errors
            response['input']['metadata'] = e.metadata
        except BaseException as e:
            traceback.print_exc(file=sys.stdout)
            response.update(exception=str(e))
        # try:
        #     print(json.dumps(response, indent=2, sort_keys=False, ensure_ascii=False))
        # except BaseException:
        #     print(response)
        response = Response(response)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def apply(self, _model, func, meta_func, instance, data, exclude_field):
        metadata = getattr(meta_func, '_metadata')
        custom_fields = metadata.get('fields', {})
        # print(metadata)
        if 'params' in metadata:
            if metadata['params']:
                # we are adding or editing an object and all params are custom fields
                if metadata['name'] in ('add', 'edit') and len(metadata['params']) == len(custom_fields):
                    _fields = None
                    _exclude = ()
                # the params are both own and custom fields, so lets explicitally specify the form fields
                else:
                    _fields = [name for name in metadata['params'] if name not in custom_fields]
                    _exclude = None
            else:
                # lets include all model fields
                if metadata['name'] in ('add', 'edit'):
                    _fields = None
                    _exclude = ()
                else:  # lets include no model fields
                    if custom_fields:
                        _fields = ()
                        _exclude = None
                    else:  # lets return because no form is needed
                        try:
                            return func(), {}
                        except ValidationError as e:
                            raise InputValidationError([{'message': e.message, 'field': None}], {})

            class Form(ModelForm):

                class Meta:
                    model = _model
                    fields = _fields
                    exclude = _exclude

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    # custom fields
                    for name, field in custom_fields.items():
                        self.fields[name] = field.formfield()

                    # exclude fields
                    if exclude_field and exclude_field in self.fields:
                        del(self.fields[exclude_field])

                    # set metadata
                    self.metadata = {}
                    for name, field in self.fields.items():
                        choices = None
                        item = OrderedDict(
                            label=field.label, required=field.required,
                            mask=None, value=None, choices=choices, help_text=field.help_text
                        )
                        self.metadata[name] = item

                    self.one_to_many_forms = {}
                    one_to_many_field_names = [
                        name for name in self.fields if hasattr(self.fields[name], '_is_one_to_many')
                    ]
                    for one_to_many_field_name in one_to_many_field_names:
                        one_to_many_items = {}
                        one_to_many_field = self.fields[one_to_many_field_name]
                        del(self.fields[one_to_many_field_name])
                        one_to_many_form = modelform_factory(one_to_many_field.queryset.model, exclude=())
                        self.one_to_many_forms[one_to_many_field_name] = one_to_many_form
                        for name, field in one_to_many_form.base_fields.items():
                            choices = None
                            item = OrderedDict(
                                label=field.label, required=field.required,
                                mask=None, value=None, choices=choices, help_text=field.help_text
                            )
                            one_to_many_items[name] = item
                        self.metadata[one_to_many_field_name] = [one_to_many_items]

                def save(self, *args, **kwargs):
                    # print(data, form.cleaned_data)
                    # print(form.fields.keys(), custom_fields.keys(), metadata['params'])
                    params = {}
                    for param in metadata['params']:
                        params[param] = self.cleaned_data.get(param)
                    result = func(**params)
                    for one_to_many_field_name in self.one_to_many_forms:
                        form_cls = self.one_to_many_forms[one_to_many_field_name]
                        for inner_data in data[one_to_many_field_name]:
                            inner_form = form_cls(data=inner_data)
                            if inner_form.is_valid():
                                inner_form.save()
                                getattr(self.instance, one_to_many_field_name).add(inner_form.instance)
                            elif inner_form.errors:
                                inner_errors = []
                                for i, (inner_field_name, messages) in enumerate(inner_form.errors.items()):
                                    inner_errors.append(
                                        {'message': ','.join(messages), 'field': one_to_many_field_name, 'index': i,
                                         'inner': inner_field_name}
                                    )
                                raise InputValidationError(inner_errors, self.metadata)
                    return result, self.metadata

            form = Form(data=data or None, instance=instance)
            if form.is_valid():
                try:
                    if metadata.get('atomic'):
                        with transaction.atomic():
                            return form.save()
                    else:
                        return form.save()
                except ValidationError as e:
                    raise InputValidationError([{'message': e.message, 'field': None}], form.metadata)
            elif form.errors:
                errors = []
                for field_name, messages in form.errors.items():
                    errors.append({'message': ','.join(messages), 'field': field_name})
                raise InputValidationError(errors, form.metadata)
            else:
                return None, form.metadata

        else:
            try:
                return func(), {}
            except ValidationError as e:
                raise InputValidationError([{'message': e.message, 'field': None}], {})
