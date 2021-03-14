# -*- coding: utf-8 -*-

from django.test import TestCase
from .models import Pessoa, Estado, Cidade, PontoTuristico, Presidente, Governador, Telefone, Endereco
import json

# /queryset
# /queryset/<filter>

# /user
# /login
# /logout

# /projeto/estado
# /projeto/estado/ativos
# /projeto/estado/inativar
# /projeto/estado/inativar_todos
# /projeto/estado/<id>/view
# /projeto/estado/<id>/edit
# /projeto/estado/<id>/delete
# /projeto/estado/<id>/altualizar_sigla
# /projeto/estado/<id>/get_cidades
# /projeto/estado/<id>/get_cidades/add
# /projeto/estado/<id>/get_cidades/remove
# /projeto/estado/<id>/get_pontos_turisticos/add
# /projeto/estado/<id>/get_pontos_turisticos/remove

# curl -H "Content-Type: application/json" -X POST http://localhost:8000/api/login/ -d '{"username": "brenokcc@yahoo.com.br", "password": "senha"}'
# curl -H "Content-Type: application/json" -H "Authorization: Token 3853ded71e2cb8299a1e1c7e45c4722a787a45e9" -X GET http://localhost:8000/api/projeto/estado/



def log(response):
    print(json.dumps(response, indent=2, sort_keys=False, ensure_ascii=False))


class MainTestCase(TestCase):

    def get(self, url, data=None):
        data = json.dumps(data) if data is not None else None
        response = self.client.get(url, data=data, content_type='application/json')
        return json.loads(response.content)

    def post(self, url, data=None):
        data = json.dumps(data) if data is not None else None
        response = self.client.post(url, data=data, content_type='application/json')
        return json.loads(response.content)

    def test_models(self):

        estado = Estado(nome='São Paulo', sigla='SP', ativo=False)
        estado.add()
        estado = Estado(nome='Rio Grande do Norte', sigla='RN')
        estado.add()
        self.assertEqual(Estado.objects.all().count(), 2)

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

        self.assertTrue(1)

    def test_login(self):
        pessoa = Pessoa(nome='Carlos Breno', email='brenokcc@yahoo.com.br')
        pessoa.add()
        pessoa.alterar_senha('senha')
        # getting the metadata
        r = self.get('/api/login')
        data = r['input']
        # setting the data
        data['username'] = 'brenokcc@yahoo.com.br'
        data['password'] = 'senha'
        r = self.post('/api/forms/loginform', data=data)
        self.assertEqual(r['message'], 'Login realizado com sucesso')
        self.assertIsNotNone(r['token'])
        # getting authenticated user
        r = self.get('/api/user')
        self.assertIsNotNone(r['data'])
        # logging out
        r = self.get('/api/logout')
        self.assertEqual(r['text'], 'Logout realizado com sucesso')
        r = self.get('/api/user')
        self.assertEqual(r['text'], 'Usuário não autenticado')
        # wrong password
        data['password'] = '123'
        r = self.post('/api/forms/loginform', data=data)
        self.assertEqual(r['text'], 'Usuário e senha não conferem')

    def test_api(self):
        data = dict(nome='Parque do Povo')
        # add
        r = self.post('/api/projeto/pontoturistico/add/', data=data)
        self.assertEqual(r, dict(type='message', text='Cadastro realizado com sucesso'))
        self.assertEqual(PontoTuristico.objects.count(), 1)
        # list
        r = self.get('/api/projeto/pontoturistico/')
        self.assertEqual(len(r['data']), 1)
        # view
        r = self.get('/api/projeto/pontoturistico/1/')
        self.assertIn([{'name': 'nome', 'label': 'Nome', 'value': 'Parque do Povo', 'formatter': None}], r['data'][0]['data']['fields'])
        # edit
        data = dict(nome='Parque da Cidade')
        r = self.post('/api/projeto/pontoturistico/1/edit/', data=data)
        self.assertEqual(r, dict(type='message', text='Edição realizada com sucesso'))
        r = self.get('/api/projeto/pontoturistico/1/')
        self.assertIn([{'name': 'nome', 'label': 'Nome', 'value': 'Parque da Cidade', 'formatter': None}], r['data'][0]['data']['fields'])
        self.assertEqual(PontoTuristico.objects.count(), 1)
        # validation error
        data = dict(nome='Parque da Cidade')
        r = self.post('/api/projeto/pontoturistico/1/atualizar_nome/', data=data)
        self.assertEqual(r, dict(type='error', text='Período de edição ainda não está aberto', errors=[]))
        # delete
        r = self.post('/api/projeto/pontoturistico/1/delete/')
        self.assertEqual(r, dict(type='message', text='Exclusão realizada com sucesso'))
        self.assertEqual(PontoTuristico.objects.count(), 0)

        # one-to-many (add)
        data = dict(nome='Rio Grande do Norte', sigla='RN')
        r = self.post('/api/projeto/estado/add/', data=data)
        self.assertEqual(r, dict(type='message', text='Cadastro realizado com sucesso'))
        r = self.get('/api/projeto/estado/1/get_cidades/')
        self.assertEqual(r['data'][0]['data']['total'], 0)
        data = dict(nome='Natal')
        r = self.post('/api/projeto/estado/1/get_cidades/add/', data=data)
        self.assertEqual(r, dict(type='message', text='Cadastro realizado com sucesso'))
        r = self.get('/api/projeto/estado/1/get_cidades/')
        self.assertEqual(r['data'][0]['data']['total'], 1)

        # many-to-many (add)
        data = dict(nome='Morro do Careca')
        r = self.post('/api/projeto/pontoturistico/add/', data=data)
        self.assertEqual(r, dict(type='message', text='Cadastro realizado com sucesso'))
        r = self.get('/api/projeto/pontoturistico/')
        pk = r['data'][0][0]
        r = self.get('/api/projeto/cidade/1/get_pontos_turisticos/')
        self.assertEqual(r['data'][0]['data']['total'], 0)
        data = dict(ids=[pk])
        r = self.post('/api/projeto/cidade/1/get_pontos_turisticos/add/', data=data)
        self.assertEqual(r, dict(type='message', text='Ação realizada com sucesso'))
        r = self.get('/api/projeto/cidade/1/get_pontos_turisticos/')
        self.assertEqual(r['data'][0]['data']['total'], 1)

        # many-to-many (remove)
        r = self.post('/api/projeto/cidade/1/get_pontos_turisticos/remove/{}'.format(pk))
        self.assertEqual(r, dict(type='message', text='Ação realizada com sucesso'))
        r = self.get('/api/projeto/cidade/1/get_pontos_turisticos/')
        self.assertEqual(r['data'][0]['data']['total'], 0)

        # one-to-many (remove)
        r = self.get('/api/projeto/estado/1/get_cidades/')
        pk = r['data'][0]['data']['data'][0][0]
        r = self.post('/api/projeto/estado/1/get_cidades/remove/{}'.format(pk))
        self.assertEqual(r, dict(type='message', text='Ação realizada com sucesso'))
        r = self.get('/api/projeto/estado/1/get_cidades/')
        self.assertEqual(r['data'][0]['data']['total'], 0)

        # many-to-many (reverse)
        sp = Estado.objects.create(nome='São Paulo', sigla='SP')
        guarulhos = Cidade.objects.create(nome='Guarulhos', estado=sp)
        data = dict(ids=[guarulhos.pk])
        r = self.post('/api/projeto/pontoturistico/2/get_cidades/add/', data=data)
        self.assertEqual(r, dict(type='message', text='Ação realizada com sucesso'))
        r = self.get('/api/projeto/pontoturistico/2/get_cidades/')
        self.assertEqual(r['data'][0]['data']['total'], 1)

    def test_queryset(self):
        estado = Estado(nome='Rio Grande do Norte', sigla='RN')
        estado.add()
        estado.get_cidades().add(Cidade(nome='Macaíba'))
        estado.get_cidades().add(Cidade(nome='Natal'))
        response = self.get('/api/projeto/cidade/')
        response['input']['q'] = 'Maca'
        search_response = self.post(
            response['path'],
            data=response['input']
        )
        self.assertEqual(type(search_response), dict)
        self.assertEqual(type(search_response['data']), list)
        self.assertEqual(type(search_response['total']), int)

    def test_lookups(self):
        bolsonaro = Presidente.objects.create(nome='Jair Bolsonaro')
        fatima = Pessoa(nome='Fátima', email='fatima@mail.com')
        fatima.add()
        alvaro_dias = Pessoa(nome='Álvaro Dias', email='alvaro@mail.com')
        alvaro_dias.add()
        kelps = Pessoa(nome='Kelps', email='kelps@mail.com')
        kelps.add()

        rn = Estado.objects.create(nome='Rio Grande do Norte', sigla='RN')
        sp = Estado.objects.create(nome='São Paulo', sigla='SP')

        Governador.objects.create(pessoa=fatima, estado=rn)

        natal = Cidade.objects.create(nome='Natal', estado=rn, prefeito=alvaro_dias)

        parnamirim = Cidade.objects.create(nome='Parnamirim', estado=rn)
        sao_paulo = Cidade.objects.create(nome='São Paulo', estado=sp)
        Cidade.objects.create(nome='Guarulhos', estado=sp)

        endereco = Endereco.objects.create(logradouro='Centro', numero=1, cidade=parnamirim)
        Pessoa(nome='Fulano', email='fulano@mail.com', endereco=endereco).add()

        endereco = Endereco.objects.create(logradouro='Centro', numero=1, cidade=natal)
        Pessoa(nome='Beltrano', email='beltrano@mail.com', endereco=endereco).add()

        endereco = Endereco.objects.create(logradouro='Centro', numero=1, cidade=sao_paulo)
        Pessoa(nome='Cicrano', email='cicrano@mail.com', endereco=endereco).add()

        # states
        self.assertEqual(Estado.objects.all().apply_lookups(bolsonaro).count(), 2)
        self.assertEqual(Estado.objects.all().apply_lookups(fatima).count(), 1)

        # cities
        self.assertEqual(Cidade.objects.all().apply_lookups(bolsonaro).count(), 4)
        self.assertEqual(Cidade.objects.all().apply_lookups(fatima).count(), 2)
        self.assertEqual(Cidade.objects.all().apply_lookups(kelps).count(), 0)

        # action lookups
        self.assertTrue(natal.check_lookups('teste2', bolsonaro))
        self.assertTrue(natal.check_lookups('teste2', fatima))
        natal.prefeito = None
        natal.save()
        self.assertFalse(natal.check_lookups('teste2', alvaro_dias))
        natal.prefeito = alvaro_dias
        natal.save()
        self.assertTrue(natal.check_lookups('teste2', alvaro_dias))
        self.assertFalse(natal.check_lookups('teste2', kelps))
        natal.vereadores.add(kelps)
        self.assertTrue(natal.check_lookups('teste2', kelps))

        self.assertEqual(Pessoa.objects.all3().apply_lookups(bolsonaro).count(), Pessoa.objects.count())
        self.assertEqual(Pessoa.objects.all3().apply_lookups(fatima).count(), 2)
        self.assertEqual(Pessoa.objects.all3().apply_lookups(alvaro_dias).count(), 1)
        self.assertEqual(Pessoa.objects.all3().apply_lookups(kelps).count(), 1)

    def test_one_to_many(self):
        telefones = [
            dict(ddd=84, numero='99106-2760'),
            dict(ddd=84, numero='')
        ]
        data = dict(nome='Carlos Breno', email='brenokcc@yahoo.com.br', telefones=telefones)
        r = self.post('/api/projeto/pessoa/add/', data=data)
        self.assertIsNone(Pessoa.objects.first())
        error = dict(field='numero', message='Este campo é obrigatório.', one_to_many='telefones', index=1)
        self.assertEqual(r['text'], 'Por favor, corriga os erros abaixo')
        self.assertIn(error, r['errors'])
        telefones[1]['numero'] = '3272-3898'
        r = self.post('/api/projeto/pessoa/add/', data=data)
        self.assertIsNotNone(Pessoa.objects.first())
        self.assertEqual(Telefone.objects.count(), 2)
        self.assertEqual(r, dict(type='message', text='Cadastro realizado com sucesso'))

    def test_many_to_many(self):
        rn = Estado.objects.create(nome='Rio Grande do Norte', sigla='RN')
        va = Pessoa(nome='Vereador A', email='va@mail.com')
        va.add()
        vb = Pessoa(nome='Vereador B', email='vb@mail.com')
        vb.add()
        data = dict(nome='Natal', estado=rn.pk, prefeito=None, vereadores=[va.pk, vb.pk])
        r = self.post('/api/projeto/cidade/add/', data=data)
        self.assertEqual(r, dict(type='message', text='Cadastro realizado com sucesso'))
        self.assertEqual(Cidade.objects.first().vereadores.count(), 2)
