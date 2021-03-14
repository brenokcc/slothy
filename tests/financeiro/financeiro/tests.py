# -*- coding: utf-8 -*-

from slothy.admin.models import User
from slothy.api.tests import ApiTestCase
from .models import Pessoa, TipoReceita, TipoReceitaPessoal


class MainTestCase(ApiTestCase):

    def test(self):
        TipoReceita.objects.create(descricao='Salário')
        breno = Pessoa(nome='Breno', email='brenokcc@yahoo.com.br')
        breno.add()
        bruno = Pessoa(nome='Bruno', email='bruno_ufrn_natal@yahoo.com.br')
        bruno.add()
        user = User.objects.get(username=breno.email)
        TipoReceitaPessoal.objects.create(pessoa=breno, descricao='Traduções')
        TipoReceitaPessoal.objects.create(pessoa=bruno, descricao='Declarações de IR')
        qs = TipoReceita.objects.all().apply_lookups(
            user, ('self__tiporeceitapessoal__isnull', 'self__tiporeceitapessoal__pessoa')
        )
        self.assertEqual(qs.count(), 2)
