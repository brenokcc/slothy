# -*- coding: utf-8 -*-

import json
from urllib.error import HTTPError
from slothy.regional.brasil.enderecos.models import Municipio, Estado
import urllib.request, urllib.error, urllib.parse


def consultar(cep):
    try:
        # {'bairro': 'Santos Reis', 'cidade': 'Parnamirim', 'logradouro': 'Avenida Jo\xe3o XXIII', 'estado_info':
        # {'area_km2': '52.811,110', 'codigo_ibge': '24', 'nome': 'Rio Grande do Norte'}, 'cep': '59141030',
        # 'cidade_info': {'area_km2': '123,471', 'codigo_ibge': '2403251'}, 'estado': 'RN'}

        dados = json.loads(urllib.request.urlopen(
            'http://api.postmon.com.br/v1/cep/{}'.format(cep)
        ).read().decode('utf-8'))
        codigo_estado = dados['estado_info']['codigo_ibge']
        codigo_cidade = dados['cidade_info']['codigo_ibge']
        nome_cidade = dados['cidade']
        
        qs = Municipio.objects.filter(codigo=dados['cidade_info']['codigo_ibge'])
        if qs.exists():
            cidade = qs[0]
            dados['cidade_id'] = cidade.pk
            dados['cidade'] = str(cidade)
        else:
            estado = Estado.objects.get(codigo=codigo_estado)
            cidade = Municipio.objects.create(nome=nome_cidade, estado=estado, codigo=codigo_cidade)
            dados['cidade_id'] = cidade.pk
            dados['cidade'] = str(cidade)
        return json.dumps(dados)
    except HTTPError:
        return json.dumps(dict(message='CPF inválido!'))