# -*- coding: utf-8 -*-
from slothy.db import models
from datetime import date
from slothy.api.models import User
from slothy.decorators import attr, attrs, action, dashboard, fieldsets


class PessoaSet(models.Set):

    @dashboard.floating()
    @attr('Pessoas')
    def all(self):
        return self.display('nome', 'email').search('nome').actions('view', 'add', 'edit', 'delete')


class Pessoa(User):

    nome = models.CharField(verbose_name='Nome')
    email = models.EmailField(verbose_name='E-mail', unique=True)

    class Meta:
        icon = 'people_alt'
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

    @dashboard.public()
    @fieldsets({'Dados Gerais': ('nome', 'email')})
    @action('Cadastrar')
    def add(self):
        self.username = self.email
        super().change_password('senha')

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view('get_dados_gerais', 'get_registros', 'get_estatisticas')
 
    @action('Alterar Senha')
    def alterar_senha(self, senha):
        super().change_password(senha)

    @attr('Dados Gerais')
    def get_dados_gerais(self):
        return self.values('nome', 'email')

    @attr('Despesas')
    def get_despesas(self):
        return self.despesa_set.all()

    @attr('Receitas')
    def get_receitas(self):
        return self.receita_set.all()

    @attr('Despesas por Tipo', formatter='donut_chart')
    def get_total_despesas_por_tipo(self):
        return self.get_despesas().count('tipo')

    @attr('Receitas por Tipo', formatter='bar_chart')
    def get_total_receitas_por_tipo(self):
        return self.get_receitas().count('tipo')

    @attrs('Registros')
    def get_registros(self):
        return self.values('get_despesas', 'get_receitas')

    @attrs('Estatística')
    def get_estatisticas(self):
        return self.values('get_total_despesas_por_tipo', 'get_total_receitas_por_tipo')


class TipoReceitaSet(models.Set):
    @dashboard.card()
    @attr('Tipos de Receita Padrão', icon='attach_money')
    def padrao(self):
        return self.filter(tiporeceitapessoal__isnull=True).actions('add', 'edit', 'delete')


class TipoReceita(models.Model):

    descricao = models.CharField(verbose_name='Descrição')

    class Meta:
        icon = 'attach_money'
        verbose_name = 'Tipo de Receita Padrão'
        verbose_name_plural = 'Tipos de Receita Padrão'

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


class TipoReceitaPessoalSet(models.Set):
    @dashboard.card()
    @attr('Tipos de Receita', lookups='pessoa')
    def all(self):
        return self.search('descricao').actions('add', 'edit', 'delete')


class TipoReceitaPessoal(TipoReceita):

    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa', exclude='self')

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
    @attr('Tipos de Despesa Padrão', icon='attach_money')
    def padrao(self):
        return self.filter(tipodespesapessoal__isnull=True).actions('add', 'edit', 'delete')


class TipoDespesa(models.Model):

    descricao = models.CharField(verbose_name='Descrição')

    class Meta:
        icon = 'attach_money'
        verbose_name = 'Tipo de Despesa Padrão'
        verbose_name_plural = 'Tipos de Despesa Padrão'

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


class TipoDespesaPessoalSet(models.Set):
    @dashboard.card()
    @attr('Tipos de Despesa', lookups='pessoa')
    def all(self):
        return self.search('descricao').actions('add', 'edit', 'delete')


class TipoDespesaPessoal(TipoDespesa):

    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa', exclude='self')

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
    @dashboard.bottom_bar()
    @dashboard.calendar()
    @attr('Receitas', lookups='pessoa')
    def all(self):
        return self.display('tipo', 'descricao', 'data_prevista', 'valor_previsto', 'data_recebimento', 'valor_recebido').actions('add', 'edit', 'delete').subsets('recebidas', 'nao_recebidas').lookups('self__pessoa')

    @attr('Recebidas', lookups='pessoa')
    def recebidas(self):
        return self.filter(data_recebimento__isnull=False).lookups('self__pessoa').actions('cancelar_recebimento')

    @dashboard.shortcut()
    @attr('Não-Recebidas', lookups='pessoa')
    def nao_recebidas(self):
        return self.filter(data_recebimento__isnull=True).lookups('self__pessoa').actions('registrar_recebimento')


class Receita(models.Model):
    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa', exclude='self')
    tipo = models.ForeignKey(TipoReceita, verbose_name='Tipo', lookup=('self__tiporeceitapessoal__isnull', 'self__tiporeceitapessoal__pessoa'))
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
        return '{} - {}'.format(self.tipo, self.descricao)

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
    @dashboard.bottom_bar()
    @dashboard.calendar()
    @dashboard.public()
    @attr('Despesas', lookups='pessoa')
    def all(self):
        return self.display('tipo', 'descricao', 'data_prevista', 'valor_previsto', 'data_pagamento', 'valor_pago').actions('add', 'edit', 'delete', 'view', 'registrar_pagamento').subsets('pagas', 'nao_pagas').lookups('self__pessoa')

    @attr('Pagas', lookups='pessoa')
    def pagas(self):
        return self.filter(data_pagamento__isnull=False).lookups('self__pessoa').actions('cancelar_pagamento')

    @dashboard.center()
    @attr('Não-Pagas', lookups='pessoa')
    def nao_pagas(self):
        return self.filter(data_pagamento__isnull=True).lookups('self__pessoa').actions('registrar_pagamento')

    @dashboard.shortcut()
    @attr('Total por Tipo', icon='insert_chart_outlined', lookups='pessoa', formatter='bar_chart')
    def total_por_tipo(self):
        return self.all().sum('tipo', z='valor_previsto')


class Despesa(models.Model):
    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa', exclude='self')
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
        return '{} - {}'.format(self.tipo, self.descricao)

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
        return super().view('get_dados_gerais', 'get_previsao_pagamento', 'get_dados_pagamento')

    @attr('Dados Gerais')
    def get_dados_gerais(self):
        return self.values(('pessoa', 'tipo'), 'descricao')

    @attr('Previsão do Pagamento')
    def get_previsao_pagamento(self):
        return self.values(('data_prevista', 'valor_previsto'),)

    @attr('Dados do Pagamento')
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
