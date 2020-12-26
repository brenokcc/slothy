import json
import sys
import pdb
import traceback
from django.apps import apps
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from django.forms import ModelForm
from slothy.api.models import ValidationError
from django.views import View


class InputValidationError(BaseException):
    def __init__(self, errors, metadata):
        self.errors = errors
        self.metadata = metadata


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class QuerysetView(APIView):
    def post(self, request, app_label, model_name):
        model = apps.get_model(app_label, model_name)
        body = request.body
        s = request.POST and request.POST['metadata'] or body
        qs = model.objects.loads(s)
        return Response(qs.serialize())

    def get(self, request, app_label, model_name):
        return Response({})


class Api(APIView):
    authentication_classes = CsrfExemptSessionAuthentication, TokenAuthentication

    def options(self, request, path):
        return self.do(request, path, {}, {})

    def get(self, request, path):
        # data = {}
        # for key in request.GET:
        #     data[key] = request.GET[key]
        return self.do(request, path)

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
        return self.do(request, path)

    def do(self, request, path):
        print('# {}'.format(path))
        response = dict(path=path, message=None, exception=None, errors=[], input=dict(data={}, metadata={}), output=dict(data={}, metadata={}))
        try:
            if path.endswith('/'):
                path = path[0:-1]
            tokens = path.split('/')
            if len(tokens) == 1:
                if path == 'user':  # authenticated user
                    if request.user.is_authenticated:
                        response['output']['data'] = request.user.values()
                    else:
                        response['errors'].append({None: 'Nenhum usuário autenticado'})
                elif path == 'login':  # user login
                    user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
                    if user:
                        login(request, user)
                        response['output']['data'] = dict(token=request.user.auth_token.key)
                        response['message'] = 'Login realizado com sucesso'
                    else:
                        response['output']['data'] = dict(token=None)
                        response['errors'].append({None: 'Usuário não autenticado'})
                elif path == 'logout':  # user logout
                    logout(request)
                    response['message'] = 'Logout realizado com sucesso'
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

                    output, metadata = self.apply(model, func, meta_func or func, instance, request.POST or request.GET)
                    if output is not None:
                        response['output']['data'] = output.serialize()
                    response['input']['metadata'] = metadata
                    for item in metadata:
                        response['input']['data'][item['name']] = None

        except InputValidationError as e:
            response['errors'] = e.errors
            response['input']['metadata'] = e.metadata
        except BaseException as e:
            traceback.print_exc(file=sys.stdout)
            response.update(exception=str(e))
        try:
            print(json.dumps(response, indent=2, sort_keys=False, ensure_ascii=False))
        except BaseException:
            print(response)
            import pdb; pdb.set_trace()
        response = Response(response)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def apply(self, _model, func, meta_func, instance, data):
        metadata = getattr(meta_func, '_metadata')
        custom_fields = metadata.get('fields', {})
        print(metadata)
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
                            raise InputValidationError({None: e.message}, {})

            class Form(ModelForm):

                class Meta:
                    model = _model
                    fields = _fields
                    exclude = _exclude

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    for name, field in custom_fields.items():
                        self.fields[name] = field.formfield()

                def get_field_metadata(self):
                    items = []
                    for name, field in self.fields.items():
                        choices = []
                        item = dict(name=name, label=field.label, required=field.required, mask=None, value='', choices=choices, help_text=field.help_text)
                        items.append(item)
                    return items

            form = Form(data=data or None, instance=instance)
            if form.is_valid():
                # print(data, form.cleaned_data)
                # print(form.fields.keys(), custom_fields.keys(), metadata['params'])
                params = {}
                for param in metadata['params']:
                    params[param] = form.cleaned_data.get(param)
                try:
                    return func(**params), form.get_field_metadata()
                except ValidationError as e:
                    raise InputValidationError({None: e.message}, form.get_field_metadata())
            elif form.errors:
                errors = {}
                for field_name, messages in form.errors.items():
                    errors[field_name] = ','.join(messages)
                raise InputValidationError(errors, form.get_field_metadata())
            else:
                return None, form.get_field_metadata()

        else:
            try:
                pdb.set_trace()
                return func(), {}
            except ValidationError as e:
                raise InputValidationError({None: e.message})
