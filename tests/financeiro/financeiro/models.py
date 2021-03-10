# -*- coding: utf-8 -*-
from slothy.db import models
from datetime import date
from slothy.api.models import User
from slothy.decorators import attr, action, fieldset, dashboard, fieldsets


class PessoaSet(models.Set):

    @attr('Pessoas')
    def all(self):
        return self.display('foto', 'nome', 'email').search('nome')

    @staticmethod
    def create_superuser():
        pessoa = Pessoa.objects.create(
            nome='Breno', email='brenokcc@yahoo.com.br'
        )
        pessoa.alterar_senha('senha')


class Pessoa(User):

    nome = models.CharField(verbose_name='Nome')
    email = models.EmailField(verbose_name='E-mail', unique=True)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

    @dashboard.public()
    @fieldsets({'Dados Gerais': ('nome', ('email', 'foto'))})
    @action('Cadastrar')
    def add(self):
        self.username = self.email
        super().add()
        super().change_password('123')

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view()
 
    @action('Alterar Senha')
    def alterar_senha(self, senha):
        super().change_password(senha)

    @fieldset('Dados Gerais')
    def get_dados_gerais(self):
        return self.values('nome', ('email', 'foto'))

    @fieldset('Dados de Acesso')
    def get_dados_acesso(self):
        return self.values('nome', ('last_login', 'password'))


class TipoReceitaSet(models.Set):
    @dashboard.card()
    @attr('Tipos de Receita', icon='attach_money')
    def all(self):
        return self.actions('add', 'edit', 'delete')


class TipoReceita(models.Model):

    descricao = models.CharField(verbose_name='Descrição')

    class Meta:
        icon = 'attach_money'
        verbose_name = 'Tipo de Receita'
        verbose_name_plural = 'Tipos de Receita'

    def __str__(self):
        return self.descricao

    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view()


class TipoDespesaSet(models.Set):
    @dashboard.card()
    @attr('Tipos de Despesa', icon='attach_money')
    def all(self):
        return self.actions('add', 'edit', 'delete')


class TipoDespesa(models.Model):

    descricao = models.CharField(verbose_name='Descrição')

    class Meta:
        icon = 'attach_money'
        verbose_name = 'Tipo de Despesa'
        verbose_name_plural = 'Tipos de Despesa'

    def __str__(self):
        return self.descricao

    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view()


class ReceitaSet(models.Set):
    @dashboard.card()
    @dashboard.calendar()
    @attr('Receitas')
    def all(self):
        return self.display('descricao', 'data_prevista', 'valor_previsto', 'data_recebimento', 'valor_recebido').actions('add', 'edit', 'delete').subsets('recebidas', 'nao_recebidas').lookups('self__pessoa')

    @attr('Recebidas')
    def recebidas(self):
        return self.filter(data_recebimento__isnull=False).lookups('self__pessoa').actions('cancelar_recebimento')

    @attr('Não-Recebidas')
    def nao_recebidas(self):
        return self.filter(data_recebimento__isnull=True).lookups('self__pessoa').actions('registrar_recebimento')


class Receita(models.Model):
    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa', exclude='self')
    tipo = models.ForeignKey(TipoReceita, verbose_name='Tipo')
    descricao = models.CharField(verbose_name='Descrição')
    data_prevista = models.DateField(verbose_name='Data Prevista')
    valor_previsto = models.DecimalField(verbose_name='Valor Previsto')
    data_recebimento = models.DateField(verbose_name='Data do Recebimento', null=True, blank=True)
    valor_recebido = models.DecimalField(verbose_name='Valor Recebido', null=True, blank=True)

    class Meta:
        icon = 'call_received'
        verbose_name = 'Receita'
        verbose_name_plural = 'Receitas'

    def __str__(self):
        return self.descricao

    @fieldsets({
        'Dados Gerais': ('pessoa', 'tipo', 'descricao'),
        'Previsão do Recebimento': (('data_prevista', 'valor_previsto'),)
    })
    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view()

    def can_edit(self):
        return self.data_recebimento is None

    def can_delete(self):
        return self.data_recebimento is None

    def registrar_recebimento_initial(self):
        return dict(data_recebimento=date.today(), valor_recebido=self.valor_previsto)

    @fieldsets({'Dados do Pagamento': (('data_recebimento', 'valor_recebido'),)})
    @action('Registrar Recebimento')
    def registrar_recebimento(self, data_recebimento, valor_recebido):
        self.data_recebimento = data_recebimento
        self.valor_recebido = valor_recebido
        self.save()

    @action('Cancelar Recebimento')
    def cancelar_recebimento(self):
        self.data_recebimento = None
        self.valor_recebido = None
        self.save()


class DespesaSet(models.Set):
    @dashboard.card()
    @dashboard.calendar()
    @dashboard.public()
    @attr('Despesas')
    def all(self):
        return self.display('descricao', 'data_prevista', 'valor_previsto', 'data_pagamento', 'valor_pago').actions('add', 'edit', 'delete', 'view', 'registrar_pagamento').subsets('pagas', 'nao_pagas').lookups('self__pessoa')

    @attr('Pagas')
    def pagas(self):
        return self.filter(data_pagamento__isnull=False).lookups('self__pessoa').actions('cancelar_pagamento')

    @attr('Não-Pagas')
    def nao_pagas(self):
        return self.filter(data_pagamento__isnull=True).lookups('self__pessoa').actions('registrar_pagamento')

    @dashboard.shortcut()
    @attr('Total por Tipo', icon='insert_chart_outlined', formatter='bar_chart')
    def total_por_tipo(self):
        return self.all().sum('tipo', z='valor_previsto')


class Despesa(models.Model):
    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa', readonly='self')
    tipo = models.ForeignKey(TipoDespesa, verbose_name='Tipo')
    descricao = models.CharField(verbose_name='Descrição')
    data_prevista = models.DateField(verbose_name='Data Prevista')
    valor_previsto = models.DecimalField(verbose_name='Valor Previsto')
    data_pagamento = models.DateField(verbose_name='Data do Pagamento', null=True, blank=True)
    valor_pago = models.DecimalField(verbose_name='Valor Pago', null=True, blank=True)

    class Meta:
        icon = 'call_made'
        verbose_name = 'Despesa'
        verbose_name_plural = 'Despesas'

    def __str__(self):
        return self.descricao

    @fieldsets({
        'Dados Gerais': ('pessoa', 'tipo', 'descricao'),
        'Previsão do Pagamento': (('data_prevista', 'valor_previsto'),)
    })
    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view()

    @fieldset('Dados Gerais')
    def get_dados_gerais(self):
        return self.values(('pessoa', 'tipo'), 'descricao')

    @fieldset('Previsão do Pagamento')
    def get_previsao_pagamento(self):
        return self.values(('data_prevista', 'valor_previsto'),)

    @fieldset('Dados do Pagamento')
    def get_dados_pagamento(self):
        return self.values(('data_pagamento', 'valor_pago'),).actions('registrar')

    def registrar_pagamento_initial(self):
        return dict(data_pagamento=date.today(), valor_pago=self.valor_previsto)

    @fieldsets({'Dados do Pagamento': (('data_pagamento', 'valor_pago'),)})
    @action('Registrar Pagamento', condition='not data_pagamento')
    def registrar_pagamento(self, data_pagamento, valor_pago):
        self.data_pagamento = data_pagamento
        self.valor_pago = valor_pago
        self.save()

    @action('Cancelar Pagamento')
    def cancelar_pagamento(self):
        self.data_pagamento = None
        self.valor_pago = None
        self.save()
