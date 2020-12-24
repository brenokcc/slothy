from django.test import TestCase
from base.models import Estado, Cidade, PontoTuristico
from django.apps import apps
import json

# /queryset
# /queryset/<filter>

# /user
# /login
# /logout

# /base/estado/list
# /base/estado/ativos
# /base/estado/inativar
# /base/estado/inativar_todos
# /base/estado/<id>/view
# /base/estado/<id>/edit/
# /base/estado/<id>/remove/
# /base/estado/<id>/altualizar_sigla/
# /base/estado/<id>/get_cidades/
# /base/estado/<id>/get_cidades/add/
# /base/estado/<id>/get_cidades/remove/1/
# /base/estado/<id>/get_pontos_turisticos/add/
# /base/estado/<id>/get_pontos_turisticos/remove/1/

# curl -H "Content-Type: application/json" -H "Authorization: Token 3853ded71e2cb8299a1e1c7e45c4722a787a45e9" -X GET http://localhost:8000/api/base/estado/


def parse_url(url):
    tokens = url.split('/')
    model = apps.get_model(tokens[1], tokens[2])
    print(model)


class SuapTestCase(TestCase):
    def test_models(self):

        parse_url('/base/estado/')
        estado = Estado(nome='São Paulo', sigla='SP', ativo=False)
        estado.add()
        estado = Estado(nome='Rio Grande do Norte', sigla='RN')
        estado.add()
        print(Estado.objects.list())

        # one-to-many
        print(estado.get_cidades())
        macaiba = estado.get_cidades().add(Cidade(nome='Macaíba'))
        natal = estado.get_cidades().add(Cidade(nome='Natal'))

        # many-to-many
        parque_da_cidade = natal.get_pontos_turisticos().add(PontoTuristico(nome='Parque da Cidade'))
        print(natal, natal.get_pontos_turisticos())
        natal.get_pontos_turisticos().remove(parque_da_cidade)
        print(natal, natal.get_pontos_turisticos())
        parnamirim = estado.get_cidades().add(Cidade(nome='Parnamirim'))

        # reverse many-to-many
        print(macaiba, macaiba.get_pontos_turisticos())
        parque_da_cidade.cidade_set.add(macaiba)
        print(macaiba, macaiba.get_pontos_turisticos())
        print(parque_da_cidade, parque_da_cidade.cidade_set)
        parque_da_cidade.cidade_set.remove(macaiba)
        print(parque_da_cidade, parque_da_cidade.cidade_set)
        print(macaiba, macaiba.get_pontos_turisticos())

        print(estado.get_cidades())
        estado.get_cidades().remove(parnamirim)
        print(estado.get_cidades())

        payload = json.loads(Estado.objects.list().dumps())
        payload['metadata']['q'] = 'RN'
        payload['metadata']['filters'][0]['value'] = True
        payload['metadata']['page'] = 0
        payload['metadata']['subset'] = 'ativos'
        # print(json.dumps(payload))
        qs = Estado.objects.loads(json.dumps(payload['metadata']))
        # print(qs.dumps())
