from django.test import TestCase
from base.models import Pessoa, Estado, Cidade, PontoTuristico, Presidente, Governador
from django.apps import apps
from slothy.api.models import Group
import json
from slothy.api.utils import setup_signals

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
# /base/estado/<id>/get_cidades/remove/
# /base/estado/<id>/get_pontos_turisticos/add/
# /base/estado/<id>/get_pontos_turisticos/remove/

# curl -H "Content-Type: application/json" -X POST http://localhost:8000/api/login/ -d '{"username": "brenokcc@yahoo.com.br", "password": "senha"}'
# curl -H "Content-Type: application/json" -H "Authorization: Token 3853ded71e2cb8299a1e1c7e45c4722a787a45e9" -X GET http://localhost:8000/api/base/estado/


setup_signals()


def log(response):
    print(json.dumps(response, indent=2, sort_keys=False, ensure_ascii=False))


class MainTestCase(TestCase):

    def setUp(self):
        Group.objects.all().delete()

    def test_direct_inherited_role(self):
        self.assertFalse(Group.objects.filter(name='Presidente').exists())
        presidente = Presidente.objects.create(nome='Jair Bolsonaro')
        self.assertTrue(Group.objects.filter(name='Presidente').exists())
        self.assertTrue(presidente.groups.filter(name='Presidente').exists())

    def test_indirect_inherited_role(self):
        self.assertFalse(Group.objects.filter(name='Governador').exists())
        rn = Estado.objects.create(nome='Rio Grande do Norte', sigla='RN')
        pessoa = Pessoa.objects.create(nome='Fátima', email='fatima@mail.com')
        governador_rn = Governador.objects.create(pessoa=pessoa, estado=rn)
        self.assertTrue(Group.objects.filter(name='Governador').exists())
        self.assertTrue(pessoa.groups.filter(name='Governador').exists())

        rj = Estado.objects.create(nome='Rio de Janeiro', sigla='RJ')
        governador_rj = Governador.objects.create(pessoa=pessoa, estado=rj)
        governador_rn.delete()
        self.assertTrue(pessoa.groups.filter(name='Governador').exists())
        governador_rj.delete()
        self.assertFalse(pessoa.groups.filter(name='Governador').exists())

    def test_fk_inherited_role(self):
        self.assertFalse(Group.objects.filter(name='Prefeito').exists())
        rn = Estado.objects.create(nome='Rio Grande do Norte', sigla='RN')
        natal = Cidade.objects.create(nome='Natal', estado=rn)
        alvaro_dias = Pessoa.objects.create(nome='Álvaro Dias', email='alvaro@mail.com')
        self.assertFalse(alvaro_dias.groups.filter(name='Prefeito').exists())
        natal.prefeito = alvaro_dias
        natal.save()
        self.assertTrue(Group.objects.filter(name='Prefeito').exists())
        self.assertTrue(alvaro_dias.groups.filter(name='Prefeito').exists())
        natal.prefeito = None
        natal.save()
        self.assertFalse(alvaro_dias.groups.filter(name='Prefeito').exists())

    def test_m2m_inherited_role(self):
        self.assertFalse(Group.objects.filter(name='Vereadores').exists())
        rn = Estado.objects.create(nome='Rio Grande do Norte', sigla='RN')
        natal = Cidade.objects.create(nome='Natal', estado=rn)
        kelps = Pessoa.objects.create(nome='Kelps', email='kelps@mail.com')
        self.assertFalse(kelps.groups.filter(name='Vereadores').exists())
        natal.vereadores.add(kelps)
        self.assertTrue(Group.objects.filter(name='Vereadores').exists())
        self.assertTrue(kelps.groups.filter(name='Vereadores').exists())
        natal.vereadores.remove(kelps)
        self.assertFalse(kelps.groups.filter(name='Vereadores').exists())

    def test_models(self):

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
        payload['metadata']['q'] = 'SP'
        payload['metadata']['filters'][0]['value'] = False
        payload['metadata']['page']['number'] = 1
        payload['metadata']['subset'] = 'inativos'
        # print(json.dumps(payload))
        qs = Estado.objects.loads(json.dumps(payload['metadata']))
        # print(qs.dumps())

        self.assertTrue(1)

    def get(self, url, data=None):
        response = self.client.get(url, data=data)
        return json.loads(response.content)

    def post(self, url, data=None):
        response = self.client.post(url, data=data)
        return json.loads(response.content)

    def test_api(self):
        data = dict(nome='Parque do Povo')
        # add
        r = self.post('/api/base/pontoturistico/add/', data=data)
        self.assertEqual(r['message'], 'Cadastro realizado com sucesso')
        self.assertEqual(PontoTuristico.objects.count(), 1)
        # list
        r = self.get('/api/base/pontoturistico/')
        self.assertEqual(len(r['output']['data']), 1)
        # view
        r = self.get('/api/base/pontoturistico/1/')
        self.assertIn([{'Nome': 'Parque do Povo'}], r['output']['data']['fieldsets']['Dados Gerais']['fields'])
        # edit
        data = dict(nome='Parque da Cidade')
        r = self.post('/api/base/pontoturistico/1/edit/', data=data)
        self.assertEqual(r['message'], 'Edição realizada com sucesso')
        r = self.get('/api/base/pontoturistico/1/')
        self.assertIn([{'Nome': 'Parque da Cidade'}], r['output']['data']['fieldsets']['Dados Gerais']['fields'])
        self.assertEqual(PontoTuristico.objects.count(), 1)
        # validation error
        data = dict(nome='Parque da Cidade')
        r = self.post('/api/base/pontoturistico/1/atualizar_nome/', data=data)
        self.assertIn({'message': 'Período de edição ainda não está aberto', 'field': None}, r['errors'])
        # remove
        r = self.post('/api/base/pontoturistico/1/remove/')
        self.assertEqual(r['message'], 'Exclusão realizada com sucesso')
        self.assertEqual(PontoTuristico.objects.count(), 0)

        # one-to-many (add)
        data = dict(nome='Rio Grande do Norte', sigla='RN')
        self.post('/api/base/estado/add/', data=data)
        r = self.get('/api/base/estado/1/get_cidades/')
        self.assertEqual(r['output']['total'], 0)
        data = dict(nome='Natal')
        r = self.get('/api/base/estado/1/get_cidades/add/', data=data)
        r = self.get('/api/base/estado/1/get_cidades/')
        self.assertEqual(r['output']['total'], 1)

        # many-to-many (add)
        data = dict(nome='Morro do Careca')
        r = self.post('/api/base/pontoturistico/add/', data=data)
        self.assertEqual(r['message'], 'Cadastro realizado com sucesso')
        r = self.get('/api/base/pontoturistico/')
        pk = r['output']['data'][0][0]
        r = self.get('/api/base/cidade/1/get_pontos_turisticos/')
        self.assertEqual(r['output']['total'], 0)
        data = dict(pontos_turisticos=pk)
        self.post('/api/base/cidade/1/get_pontos_turisticos/add/', data=data)
        r = self.get('/api/base/cidade/1/get_pontos_turisticos/')
        self.assertEqual(r['output']['total'], 1)

        # many-to-many (remove)
        data = dict(pontos_turisticos=pk)
        r = self.post('/api/base/cidade/1/get_pontos_turisticos/remove/', data=data)
        r = self.get('/api/base/cidade/1/get_pontos_turisticos/')
        self.assertEqual(r['output']['total'], 0)

        # one-to-many (remove)
        r = self.get('/api/base/estado/1/get_cidades/')
        pk = r['output']['data'][0][0]
        data = dict(cidade=pk)
        r = self.get('/api/base/estado/1/get_cidades/remove/', data=data)
        r = self.get('/api/base/estado/1/get_cidades/')
        self.assertEqual(r['output']['total'], 0)

    def test_queryset(self):
        estado = Estado(nome='Rio Grande do Norte', sigla='RN')
        estado.add()
        estado.get_cidades().add(Cidade(nome='Macaíba'))
        estado.get_cidades().add(Cidade(nome='Natal'))
        response = self.client.get('/api/base/cidade/')
        metadata = response.data['output']['metadata']
        metadata['q'] = 'Maca'
        response = self.client.post(
            response.data['output']['path'],
            data=dict(metadata=json.dumps(metadata))
        )
        print(json.loads(response.content))

