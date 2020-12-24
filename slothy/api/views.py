import json
import sys
import traceback
from django.apps import apps
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from slothy.api.models import ValidationError
from slothy.api import utils


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class Api(APIView):
    authentication_classes = CsrfExemptSessionAuthentication, TokenAuthentication

    def get(self, request, path):
        data = {}
        for key in request.GET:
            data[key] = key
        return self.do(request, path, data)

    def options(self, request, path):
        return self.do(request, path, {})

    def post(self, request, path):
        body = request.body
        if request.POST:  # browser
            data = {}
            for key in request.POST:
                data[key] = request.POST[key]
            if request.FILES:
                for key in request.FILES:
                    data[key] = request.FILES[key]
        else:  # nodejs
            data = json.loads(body or '{}')
        return self.do(request, path, data)

    def do(self, request, path, data):
        response = dict(message=None, exception=None, error=None, data=None, metadata=[], url=None)
        try:
            if path.endswith('/'):
                path = path[0:-1]
            tokens = path.split('/')
            if len(tokens) == 1:
                if path == 'user':
                    if request.user.is_authenticated:
                        response.update(data=request.user.values())
                    else:
                        response.update(data={}, message='Nenhum usuário autenticado')
                elif path == 'login':
                    user = authenticate(request, username=data['username'], password=data['password'])
                    if user:
                        login(request, user)
                        data = dict(token=request.user.auth_token.key)
                        response.update(message='Login realizado com sucesso', data=data)
                    else:
                        data = dict(token=None)
                        response.update(message='Usuário não autenticado', data=data)
                elif path == 'logout':
                    logout(request)
                    response.update(message='Logout realizado com sucesso')
            else:
                if len(tokens) > 1:
                    model = apps.get_model(tokens[0], tokens[1])
                    if len(tokens) > 2:
                        if tokens[2] == 'add':  # add
                            func = model.objects.add
                            data, metadata = utils.apply(model, func, {'instance': data}, request.user)
                            response.update(message='Cadastro realizado com sucesso', data=data, metadata=metadata)
                            if data.get('id'):
                                response.update(url='/api/{}/{}/{}/'.format(
                                    model.get_metadata('app_label'),
                                    model.get_metadata('model_name'),
                                    data.get('id')
                                ))
                        elif tokens[2] == 'delete':  # delete
                            func = model.objects.all().delete
                            data, metadata = utils.apply(model, func, data, request.user)
                            response.update(message='Exclusão realizada com sucesso', data=data, metadata=metadata)
                        elif tokens[2].isdigit():  # get or execute intance method
                            obj = model.objects.get(pk=tokens[2])
                            if len(tokens) > 3:  # execute instance method
                                if tokens[3] == 'dir':
                                    response.update(data=['xxx', 'yyy'])
                                else:
                                    func = getattr(obj, tokens[3])
                                    if len(tokens) > 4:  # add or remove
                                        qs = func()
                                        if tokens[4] == 'add':
                                            data, metadata = utils.apply(model, qs.add, data, request.user, relation_name=tokens[3])
                                            response.update(message='Adição realizada com sucesso', data=data, metadata=metadata)
                                        elif tokens[4] == 'remove':
                                            data, metadata = utils.apply(model, qs.remove, data, request.user, relation_name=tokens[3])
                                            response.update(message='Removação realizada com sucesso', data=data, metadata=metadata)
                                        if data and data.get('id'):
                                            response.update(url='/api/{}/{}/{}/'.format(
                                                qs.model.get_metadata('app_label'),
                                                qs.model.get_metadata('model_name'),
                                                data.get('id')
                                            ))
                                    else:
                                        data, metadata = utils.apply(model, func, data, request.user)
                                        response.update(data=data, metadata=metadata, message='Ação realizada com sucesso')
                            else:  # get instance
                                response.update(data=obj.values())
                        else:  # execute manager method
                            func = getattr(model.objects, tokens[2])
                            data, metadata = utils.apply(model, func, data, request.user)
                            response.update(data=data, metadata=metadata)
                    else:  # list
                        func = getattr(model.objects, 'list')
                        print(model, func, data, request.user)
                        data, metadata = utils.apply(model, func, data, request.user)
                        response.update(data=data, metadata=metadata)
        except ValidationError as e:
            error = {}
            for key, messages in e.message_dict.items():
                error[key] = ', '.join(messages)
            response.update(error=error)
        except BaseException as e:
            traceback.print_exc(file=sys.stdout)
            response.update(exception=str(e))
        print(response)
        response = Response(response)
        response["Access-Control-Allow-Origin"] = "*"
        return response

