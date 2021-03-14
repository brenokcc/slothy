# -*- coding: utf-8 -*-

import datetime
from slothy.db import models, attr, attrs, action, param, fieldsets
from slothy.regional.brasil.enderecos import models as enderecos
from slothy.admin.models import User
from slothy.admin.ui import dashboard


class Telefone(models.Model):
    ddd = models.IntegerField(verbose_name='DDD')
    numero = models.CharField(verbose_name='Telefone', max_length=255)

    class Meta:
        verbose_name = 'Telefone'
        verbose_name_plural = 'Telefones'

    def __str__(self):
        return '({}) {}'.format(self.ddd, self.numero)

    @fieldsets({'Dados Gerais': (('ddd', 'numero'),)})
    def add(self):
        super().add()


class EstadoSet(models.Set):

    @dashboard.shortcut()
    @dashboard.card()
    @attr('Estados', icon='map')
    def all(self):
        return self.display(
            'nome', 'cor'
        ).filters(
            'ativo'
        ).search(
            'nome', 'sigla'
        ).subsets(
            'ativos', 'inativos'
        ).paginate(
            10
        ).lookups(
            'presidente',
            'self__governador__pessoa'
        ).actions(
            'add', 'edit', 'delete', 'view', 'ativar', 'inativar'
        )

    @dashboard.center()
    @attr('Ativos')
    def ativos(self):
        return self.filter(ativo=True).display('nome', 'sigla').lookups(
            'presidente', 'self__governador__pessoa').actions('inativar', 'edit').search('sigla')

    @attr('Inativos')
    def inativos(self):
        return self.filter(ativo=False).actions('ativar').search('sigla')

    @action('Ativar')
    def ativar_todos(self):
        self.update(ativo=True)

    @action('Agendar Inativacao')
    @param(data=models.DateField('Data'))
    def agendar_inativacao(self, data):
        self.update(ativo=False)

    @action('Atualizar Status')
    def atualizar_status(self, ativo):
        self.update(ativo=ativo)

    @action('Agendar Atualização de Status')
    @param(data=models.DateField('Data'))
    def agendar_atualizacao_status(self, ativo, data):
        self.update(ativo=ativo)

    @classmethod
    @action('Inativar Todos')
    def inativar_todos(cls):
        Estado.objects.update(ativo=False)

    @classmethod
    @attr('Agendar Inativação Total')
    @param(data=models.DateField('Data'))
    def agendar_inativacao_total(cls, data):
        Estado.objects.update(ativo=False)


class Estado(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)
    sigla = models.CharField(verbose_name='Sigla', max_length=255)
    ativo = models.BooleanField(verbose_name='Ativo', default=True)
    cor = models.ColorField(verbose_name='Cor', max_length=10, blank=True)

    class Meta:
        icon = 'map'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.sigla

    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar', icon='edit')
    def edit(self):
        super().edit()

    @action('Testar')
    def testar(self):
        print()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view('get_dados_gerais', 'get_cidades')

    @attr('Dados Gerais')
    def get_dados_gerais(self):
        return self.values(('nome', 'sigla', 'ativo'),)

    @attr('Dados Populacionais')
    def get_dados_populacionais(self):
        return self.values('get_populacao')

    @attr('Cidades')
    def get_cidades(self):
        return self.cidade_set.actions('add', 'remove')

    @action('Ativar')
    def ativar(self):
        self.ativo = True
        self.save()

    @action('Inativar')
    def inativar(self):
        self.ativo = False
        self.save()

    @attr('População')
    def get_populacao(self):
        return 279876

    @action('Alterar Sigla')
    def alterar_sigla(self, sigla):
        self.sigla = sigla
        self.save()

    @action('Programar Ativação')
    @param(data=models.DateField('Data da Ativação'))
    def programar_ativacao(self, data):
        pass


class CidadeSet(models.Set):

    @dashboard.shortcut()
    @attr('Cidades', lookups=('governador', 'prefeito', 'presidente'), icon='house')
    def all(self):
        return self.filters(
            'estado', 'prefeito', 'estado__ativo', 'vereadores'
        ).display(
            'get_dados_gerais', 'nome'
        ).lookups(
            'self__estado__governador__pessoa', 'self__prefeito', 'presidente'
        ).sort_by('nome', 'estado').actions('add', 'view', 'edit')


class Cidade(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE, filter_display=('nome', 'sigla'))
    prefeito = models.ForeignKey('projeto.Pessoa', verbose_name='Prefeito', null=True, blank=True)
    vereadores = models.ManyToManyField('projeto.Pessoa', verbose_name='Vereadores', blank=True, related_name='cidades_legisladas')
    pontos_turisticos = models.ManyToManyField('projeto.PontoTuristico', verbose_name='Pontos Turísticos', blank=True)
    localizacao = models.GeoLocationField(verbose_name='Localização', null=True, blank=True)

    class Meta:
        icon = 'house'
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'

    def __str__(self):
        return '{}/{}'.format(self.nome, self.estado)

    @action('Adicionar')
    @fieldsets({
        'Dados Gerais': (('nome', 'estado'),),
        'Administração': ('prefeito', 'vereadores'),
        'Localização': ('localizacao',)
    })
    def add(self):
        super().add()

    @staticmethod
    def add_choices():
        return dict(
            prefeito=Pessoa.objects.filter(id__lt=3)
        )

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Visualizar')
    def view(self):
        return super().view('get_dados_gerais', 'get_pontos_turisticos', 'get_localizacao', 'get_dados_administrativos', 'get_dados_turisticos', 'get_dados_estatisticos')

    @attr('Dados Gerais')
    def get_dados_gerais(self):
        return self.values('nome', ('estado', 'get_qtd_pontos_turisticos')).actions('edit')

    # Dados Administrativos
    @attrs('Dados Administrativos')
    def get_dados_administrativos(self):
        return self.values('get_prefeito', 'get_vereadores')

    @attr('Prefeito')
    def get_prefeito(self):
        return self.values('prefeito__nome', 'prefeito__email').actions('set_prefeito')

    @attr('Vereadores')
    def get_vereadores(self):
        return self.vereadores

    @attr('Teste')
    def teste(self):
        return self.values('get_dados_gerais', 'get_qtd_pontos_turisticos', 'get_localizacao')

    @attr('Teste 2', lookups=('presidente', 'governador__pessoa', 'self__prefeito', 'self__vereadores'))
    def teste2(self):
        return self.values('get_dados_gerais', 'get_qtd_pontos_turisticos')

    # Dados Turísticos
    @attrs('Dados Turísticos')
    def get_dados_turisticos(self):
        return self.values('get_qtd_pontos_turisticos', 'get_pontos_turisticos')

    @attr('Quantidade de Pontos Turísticos')
    def get_qtd_pontos_turisticos(self):
        return self.pontos_turisticos.count()

    @attr('Pontos Turísticos')
    def get_pontos_turisticos(self):
        return self.pontos_turisticos.display('nome').actions('add', 'remove')

    # Dados Estatísticos
    @attrs('Dados Estatísticos')
    def get_dados_estatisticos(self):
        return self.values('get_estatisticas')

    @attr('Estatística Populacional')
    def get_estatisticas(self):
        return {
            'Polulação Infantil': 288989,
            'População Adulta': 9389332
        }

    @attr('Localização')
    def get_localizacao(self):
        print(self.localizacao)
        return self.localizacao

    @action('Definir Prefeito')
    def set_prefeito(self, prefeito):
        self.prefeito = prefeito
        self.save()


class MunicipioSet(models.Set):

    @dashboard.card()
    @attr('Municípios')
    def all(self):
        return self.display('nome', 'estado', 'codigo').search('nome')

    # @dashboard.center(formatter='rnmap')
    @attr('Geolocalizados', icon='map')
    def geolocalizados(self):
        return self.filter(estado__sigla='RN', nome__icontains='mo').display('nome', 'estado', 'codigo', 'get_cor').paginate(200)


class Municipio(enderecos.Municipio):

    class Meta:
        icon = 'map'
        verbose_name = 'Município'
        verbose_name_plural = 'Municípios'
        proxy = True

    def __str__(self):
        return '{}/{}'.format(self.nome, self.estado)

    @attr('Cor')
    def get_cor(self):
        if self.nome.startswith('Moss'):
            return '#FF0000'
        else:
            return '#00FF00'

    @action('Cadastrar')
    @fieldsets({'Dados Gerais': ('nome', 'estado', 'codigo')})
    def add(self):
        super().add()

    @action('Editar', icon='edit')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view()


class Endereco(models.Model):
    logradouro = models.CharField(verbose_name='Logradouro', max_length=100)
    numero = models.IntegerField(verbose_name='Número')
    cidade = models.ForeignKey(Cidade, verbose_name='Cidade', null=True)

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'

    def __str__(self):
        return '{}, {}, {}'.format(self.logradouro, self.numero, self.cidade)

    @fieldsets({'Dados Gerais': (('logradouro', 'numero', 'cidade'),)})
    def add(self):
        super().add()

    @action('Visualizar')
    def view(self):
        return super().view()


class PessoaSet(models.Set):

    @dashboard.shortcut()
    @dashboard.bottom_bar()
    @dashboard.floating()
    @dashboard.calendar()
    @attr('Pessoas', icon='people_alt')
    def all(self):
        return self.display('nome').actions('add', 'view')

    @dashboard.calendar()
    @attr('Pessoas Inativas', icon='people_alt')
    def all2(self):
        return self.display('nome', 'last_login')

    @dashboard.calendar()
    @attr('Pessoas Ativas', icon='people_alt')
    def all3(self):
        return self.display('nome', 'email', 'foto').lookups(
            'self__endereco__cidade__estado__governador__pessoa',
            'self__endereco__cidade__prefeito', 'presidente',
            'self__endereco__cidade__vereadores'
        )


class Pessoa(User):

    nome = models.CharField(verbose_name='Nome', max_length=255)
    email = models.EmailField(verbose_name='E-mail', unique=True, max_length=255)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    endereco = models.OneToOneField(Endereco, verbose_name='Endereço', null=True, blank=True)

    telefones = models.OneToManyField(Telefone, verbose_name='Telefones')

    class Meta:
        icon = 'people_alt'
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

    @action('Cadastrar', atomic=True, icon='people_alt')
    @fieldsets({
        'Dados Gerais': ('nome', ('email', 'foto', 'password', 'last_login'),),
        'Endereço': 'endereco',
        'Telefones': 'telefones'
    })
    def add(self):
        self.username = self.email
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Excluir')
    def delete(self):
        super().delete()

    @action('Visualizar')
    def view(self):
        return super().view('get_dados_gerais', 'get_dados_acesso')

    @attr('Dados Gerais')
    def get_dados_gerais(self):
        return self.values('nome', ('email', 'foto'))

    @attr('Dados de Acesso')
    def get_dados_acesso(self):
        return self.values(('last_login', 'get_senha'),)

    @attr('Grupos')
    def get_grupos(self):
        return self.groups

    @attr('Senha')
    def get_senha(self):
        return '*****'

    @action('Atualizar Nome')
    @param(data_atualizacao=models.DateField())
    def atualizar_nome(self, nome):
        self.nome = nome
        self.save()

    @action('Alterar Senha')
    @param(senha=models.CharField('Senha'))
    def alterar_senha(self, senha):
        super().change_password(senha)

    @attr('Telefones')
    def get_telefones(self):
        return self.telefones.all()


class PontoTuristicoSet(models.Set):

    @dashboard.center(formatter='round_image', priority=10)
    @dashboard.shortcut()
    @dashboard.bottom_bar()
    @dashboard.floating()
    @attr('Pontos Turísticos', icon='wb_sunny')
    def all(self):
        return super().display('foto', 'nome').search('nome').order_by('nome').actions(
            'add', 'edit', 'delete', 'teste2', 'view'
        )

    @attr('Referenciados')
    def referenciados(self):
        return self.filter(cidade__isnull=False)

    @attr('Referenciados')
    @param(sigla=models.CharField())
    def referenciados_no_estado(self, sigla):
        return self.filter(cidade__estado__sigla=sigla)

    @classmethod
    @action('Remover Tudo')
    def remover_tudo(cls):
        PontoTuristico.objects.all().delete()

    @staticmethod
    def teste_initial():
        return dict(data=datetime.date.today())

    @action('Teste')
    @param(data=models.DateField('Data'))
    def teste(self, data):
        print(self.count(), data)

    @dashboard.shortcut()
    @attr('Total por Cidade', icon='pie_chart')
    def total_por_cidade(self):
        return self.count('cidade')

    @dashboard.floating()
    @attr('Total por Cidade e Status', icon='insert_chart_outlined', formatter='bar_chart')
    def total_por_cidade_ativo(self):
        return self.count('cidade', 'ativo')


class PontoTuristico(models.Model):
    foto = models.ImageField(verbose_name='Foto', upload_to='fotos', null=True, blank=True)
    nome = models.CharField(verbose_name='Nome', max_length=255)
    ativo = models.BooleanField(verbose_name='Ativo', default=True)

    class Meta:
        icon = 'wb_sunny'
        verbose_name = 'Ponto Turístico'
        verbose_name_plural = 'Pontos Turísticos'

    def __str__(self):
        return '{}'.format(self.nome)

    @action('Visualizar')
    def view(self):
        return super().view('get_dados_gerais', 'get_x', 'get_y')

    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @attr('Dados Gerais')
    def get_dados_gerais(self):
        return self.values('nome', 'ativo')

    @action('Atualizar Nome')
    def atualizar_nome(self, nome):
        raise models.ValidationError('Período de edição ainda não está aberto')

    @action('Excluir')
    def delete(self):
        super().delete()

    @attr('Cidades')
    def get_cidades(self):
        return self.cidade_set.all()

    @staticmethod
    def teste2_initial():
        return dict(data=datetime.date.today())

    @action('Teste')
    @param(data=models.DateField('Data'))
    def teste2(self, data):
        print(self.id, data)

    @attr('Status')
    def get_status(self):
        return self.values('ativo')

    @attrs('Tab X')
    def get_x(self):
        return self.values('get_dados_gerais', 'get_status')

    @attrs('Tab Y')
    def get_y(self):
        return self.values('get_status')


class PresidenteSet(models.Set):
    @attr('Presidentes')
    def all(self):
        return self


class Presidente(Pessoa):

    class Meta:
        verbose_name = 'Presidente'
        verbose_name_plural = 'Presidentes'

    def __str__(self):
        return '{}'.format(self.nome)


class GovernadorSet(models.Set):
    @attr('Governadores')
    def all(self):
        return self


class Governador(models.Model):
    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa')
    estado = models.ForeignKey(Estado, verbose_name='Estado')

    class Meta:
        verbose_name = 'Governador'
        verbose_name_plural = 'Governadores'

    def __str__(self):
        return '{} - {}'.format(self.pessoa, self.estado)