import json
import sys
import traceback
from django.apps import apps
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.forms import ModelForm
from slothy.api.models import ValidationError


class InputValidationError(BaseException):
    def __init__(self, errors):
        self.errors = errors


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class Api(APIView):
    authentication_classes = CsrfExemptSessionAuthentication, TokenAuthentication

    def get(self, request, path):
        # data = {}
        # for key in request.GET:
        #     data[key] = request.GET[key]
        return self.do(request, path, request.GET)

    def options(self, request, path):
        return self.do(request, path, {})

    def post(self, request, path):
        # body = request.body
        # data = {}
        # if request.POST:  # browser
        #     for key in request.POST:
        #         data[key] = request.POST[key]
        #     if request.FILES:
        #         for key in request.FILES:
        #             data[key] = request.FILES[key]
        # else:  # nodejs
        #     data = json.loads(body or '{}')
        return self.do(request, path, request.POST)

    def do(self, request, path, data):
        print('# {}'.format(path))
        response = dict(message=None, exception=None, error=None, data=None, metadata=[], url=None)
        try:
            if path.endswith('/'):
                path = path[0:-1]
            tokens = path.split('/')
            if len(tokens) == 1:
                if path == 'user':  # authenticated user
                    if request.user.is_authenticated:
                        response.update(data=request.user.values())
                    else:
                        response.update(data={}, message='Nenhum usuário autenticado')
                elif path == 'login':  # user login
                    user = authenticate(request, username=data['username'], password=data['password'])
                    if user:
                        login(request, user)
                        data = dict(token=request.user.auth_token.key)
                        response.update(message='Login realizado com sucesso', data=data)
                    else:
                        data = dict(token=None)
                        response.update(message='Usuário não autenticado', data=data)
                elif path == 'logout':  # user logout
                    logout(request)
                    response.update(message='Logout realizado com sucesso')
            else:
                if len(tokens) > 1:
                    meta_func = None
                    instance = None
                    model = apps.get_model(tokens[0], tokens[1])
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
                                func = instance.view
                            else:
                                if len(tokens) == 4:  # object subset, meta or action
                                    func = getattr(instance, tokens[3])  # object meta or action
                                else:  # object relation (add or remove)
                                    qs = getattr(instance, tokens[3])().none()
                                    if tokens[4] == 'add':
                                        field = getattr(getattr(qs, '_related_manager'), 'field', None)
                                        if field:  # one-to-many
                                            value = getattr(qs, '_hints')['instance']
                                            model = qs.model
                                            instance = model()
                                            setattr(instance, field.name, value)
                                            func = instance.add
                                        else:  # many-to-many
                                            def add(**kwargs):
                                                for obj in kwargs[related_attribute]:
                                                    qs.add(obj)
                                            related_attribute = getattr(qs, '_related_attribute')
                                            setattr(add, '_metadata', dict(name='add_m2m', params=(related_attribute,)))
                                            func = add
                                    else:
                                        func = None
                    else:
                        func = model.objects.list
                        meta_func = getattr(model.objects, '_queryset_class').list

                    output = self.apply(model, func, meta_func or func, instance, data)
                    if output is not None:
                        print(output)

        except InputValidationError as e:
            print(9999999, e.errors)
            response.update(errors=e.errors)
        except BaseException as e:
            traceback.print_exc(file=sys.stdout)
            response.update(exception=str(e))
        response = Response(response)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def apply(self, _model, func, meta_func, instance, data):
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
                # lets include all fields
                if metadata['name'] in ('add', 'edit'):
                    _fields = None
                    _exclude = ()
                # lets include no fields
                else:
                    _fields = ()
                    _exclude = None

            class Form(ModelForm):

                class Meta:
                    model = _model
                    fields = _fields
                    exclude = _exclude

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    for name, field in custom_fields.items():
                        self.fields[name] = field.formfield()

            form = Form(data=data, instance=instance)
            if form.is_valid():
                # print(data, form.cleaned_data)
                # print(form.fields.keys(), custom_fields.keys(), metadata['params'])
                params = {}
                for param in metadata['params']:
                    params[param] = form.cleaned_data.get(param)
                return func(**params)

            else:
                errors = {}
                for field_name, messages in form.errors.items():
                    errors[field_name] = ','.join(messages)
                raise InputValidationError(errors)

        else:
            return func()

