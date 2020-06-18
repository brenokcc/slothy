import json
from django.apps import apps
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import login, logout, authenticate
from slothy.api.backend import utils

from rest_framework.authentication import SessionAuthentication, TokenAuthentication


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

    def post(self, request, path):
        body = request.body
        if request.POST:  # browser
            data = {}
            for key in request.POST:
                data[key] = request.POST[key]
        else:  # nodejs
            data = json.loads(body or '{}')
        return self.do(request, path, data)

    def do(self, request, path, data):
        print(request.user, path)
        response = dict(message=None, exception=None, error=None, data=None, metadata=[], url='/api/{}'.format(path))
        if path.startswith('user/'):
            if request.user.is_authenticated:
                response.update(data=request.user.values())
            else:
                response.update(data={})
        elif path.startswith('login/'):
            user = authenticate(request, username=data['username'], password=data['password'])
            if user:
                login(request, user)
                data = dict(token=request.user.auth_token.key)
                response.update(message='Login realizado com sucesso', data=data)
            else:
                data = dict(token=None)
                response.update(message='Usuário não autenticado', data=data)
        elif path.startswith('logout/'):
            logout(request)
            response.update(message='Logout realizado com sucesso')
        else:
            tokens = path.split('/')
            if len(tokens) > 1:
                model = apps.get_model(tokens[0], tokens[1])
                if tokens[2]:
                    if tokens[2] == 'add':  # add
                        obj = model.objects.get_or_create(**data)[0]
                        response.update(message='Cadastro realizado com sucesso', data=obj.values())
                    if tokens[2].isdigit():
                        obj = model.objects.get(pk=tokens[2])
                        if tokens[3]:  # execute method
                            attr = getattr(obj, tokens[3])
                            data = attr(**data) if callable(attr) else attr
                            response.update(data=data, message='Ação realizada com sucesso')
                        else:  # view
                            response.update(data=obj.values())
                else:  # list
                    response.update(data=list(model.objects.all().values()))
        response = Response(json.dumps(response, default=utils.custom_serialize))
        response["Access-Control-Allow-Origin"] = "*"
        return response

