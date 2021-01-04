import sys
import json
import traceback
from django.apps import apps
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from slothy.api.models import ValidationError, ManyToManyField, ForeignKey
from slothy.forms import ApiModelForm, InputValidationError


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

    def get(self, *args, **kwargs):
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
        response = dict(type='http_response', path='/{}'.format(path), message=None, exception=None, errors=[], input=dict(data={}, metadata={}), output=None)
        try:
            if path.endswith('/'):
                path = path[0:-1]
            tokens = path.split('/')
            if len(tokens) == 1:
                if path == 'user':  # authenticated user
                    if request.user.is_authenticated:
                        response['output'] = request.user.view()
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
                    message = None
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
                                setattr(instance, '_current_display_name', request.GET.get('display'))
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

                                                def func(id):  # add or remove
                                                    qs.remove(id)
                                                metadata = dict(
                                                    name='_',
                                                    params=('id',),
                                                    verbose_name='Remover',
                                                    message='Ação realizada com sucesso',
                                                    fields={'id': ForeignKey(
                                                        qs.model, verbose_name=qs.model.get_metadata('verbose_name')
                                                    )}
                                                )
                                                setattr(func, '_metadata', metadata)
                                                # response['input']['data'] = {'id': None}
                                        else:  # many-to-many

                                            def func(ids):  # add or remove
                                                for pk in ids:
                                                    getattr(qs, tokens[4])(pk)
                                            metadata = dict(
                                                name='_',
                                                params=('ids',),
                                                verbose_name=tokens[4] == 'add' and 'Adicionar' or 'Remover',
                                                message='Ação realizada com sucesso',
                                                fields={'ids': ManyToManyField(
                                                    qs.model, verbose_name=qs.model.get_metadata('verbose_name_plural')
                                                )}
                                            )
                                            setattr(func, '_metadata', metadata)
                                            # response['input']['data'] = {'ids': None}
                                    else:
                                        func = None
                    else:
                        func = model.objects.list
                        meta_func = getattr(model.objects, '_queryset_class').list

                    metadata = getattr(meta_func or func, '_metadata')
                    form_cls = self.build_form(model, func, metadata, instance, exclude_field)
                    if form_cls:
                        form = form_cls(data=data or None, instance=instance)
                        output = form
                        if form.is_valid():
                            if metadata.get('atomic'):
                                with transaction.atomic():
                                    form.save()
                            else:
                                form.save()
                            message = metadata.get('message')
                    else:
                        try:
                            output = func()
                            message = metadata.get('message')
                        except ValidationError as e:
                            raise InputValidationError([{'message': e.message, 'field': None}], {}, {})

                    if output is not None:
                        # print(type(output))
                        if isinstance(output, dict):
                            response['output'] = output
                        else:
                            response['output'] = output.serialize(as_view=True)
                    response['message'] = message

        except InputValidationError as e:
            response['errors'] = e.errors
        except BaseException as e:
            traceback.print_exc(file=sys.stdout)
            response.update(exception=str(e))

        response = Response(response)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def build_form(self, _model, func, metadata, instance, exclude_field):
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

            class Form(ApiModelForm):

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
