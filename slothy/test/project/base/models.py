# -*- coding: utf-8 -*-
from slothy.api import models
from slothy.api.models.decorators import user, role, attr, action, fieldset, param


class Telefone(models.Model):
    ddd = models.IntegerField(verbose_name='DDD')
    numero = models.CharField(verbose_name='Telefone', max_length=255)

    class Meta:
        verbose_name = 'Telefone'
        verbose_name_plural = 'Telefones'

    def __str__(self):
        return '({}) {}'.format(self.ddd, self.numero)


class EstadoManager(models.DefaultManager):

    @action('Todos')
    def list(self):
        return self.all(
        ).list_display(
            'nome', 'ativo'
        ).list_filter(
            'ativo'
        ).list_actions(
            'inativar'
        ).list_search(
            'nome', 'sigla'
        ).list_subsets(
            'ativos', 'inativos'
        ).list_per_page(
            10
        ).lookups(
            'presidente',
            'self__governador__pessoa'
        )

    @attr('Ativos')
    def ativos(self):
        return self.filter(ativo=True)

    @attr('Inativos')
    def inativos(self):
        return self.filter(ativo=False)

    @action('Ativar')
    def ativar(self):
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

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.sigla

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

    @attr('Dados Gerais', display=True)
    def dados_gerais(self):
        return self.values('nome', ('sigla', 'ativo'))

    @attr('Dados Populacionais', display=True)
    def dados_populacionais(self):
        return self.values('get_populacao')

    @attr('Cidades', display=True)
    def get_cidades(self):
        return self.cidade_set.all().list_filter('estado')

    @action('Ativar')
    def ativar(self):
        self.ativo = True
        self.save()

    @action('Ativar')
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


class CidadeManager(models.DefaultManager):

    @action('Listar', lookups=('governador', 'prefeito', 'presidente'))
    def list(self):
        return self.all().list_filter(
            'estado'
        ).list_display(
            'id', 'get_dados_gerais'
        ).lookups(
            'self__estado__governador__pessoa', 'self__prefeito', 'presidente'
        )


class Cidade(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE, filter_display=('nome', 'sigla'))
    prefeito = models.RoleForeignKey('base.Pessoa', verbose_name='Prefeito', null=True, blank=True)
    vereadores = models.RoleManyToManyField('base.Pessoa', verbose_name='Vereadores', blank=True, related_name='cidades_legisladas')
    pontos_turisticos = models.ManyToManyField('base.PontoTuristico', verbose_name='Pontos Turísticos', blank=True)

    class Meta:
        verbose_name = 'Cidade'
        verbose_name_plural = 'Cidades'

    def __str__(self):
        return '{}/{}'.format(self.nome, self.estado)

    @action('Adicionar')
    @fieldset({
        'Dados Gerais': ('nome', 'estado'),
        'Administração': ('prefeito', 'vereadores')
    })
    def add(self):
        super().add()

    @staticmethod
    def add_choices():
        return dict(
            prefeito=Pessoa.objects.filter(id__lt=3)
        )

    @staticmethod
    def add_initial():
        return dict(nome='Rio Grande do Norte')

    @action('Editar', lookups=('self__prefeito', 'self__estado__governador__pessoa', 'presidente'))
    def edit(self):
        super().edit()

    @action('Visualizar')
    def view(self):
        return super().view()

    @attr('Dados Gerais', display=True)
    def get_dados_gerais(self):
        return self.values('nome', ('estado', 'get_qtd_pontos_turisticos')).allow('edit')

    @attr('Prefeito', display='Administração')
    def get_prefeito(self):
        return self.values('prefeito__nome', 'prefeito__email').allow('set_prefeito')

    @attr('Vereadores', display='Administração')
    def get_vereadores(self):
        return self.vereadores

    @attr('Quantidade de Pontos Turísticos', display='Turismo')
    def get_qtd_pontos_turisticos(self):
        return self.pontos_turisticos.count()

    @attr('Pontos Turísticos', display='Turismo')
    def get_pontos_turisticos(self):
        return self.pontos_turisticos

    @attr('Estatística Populacional', display='Estatística')
    def get_estatisticas(self):
        return {
            'Polulação Infantil': 288989,
            'População Adulta': 9389332
        }

    @action('Definir Prefeito')
    def set_prefeito(self, prefeito):
        self.prefeito = prefeito
        self.save()


class Endereco(models.Model):
    logradouro = models.CharField(verbose_name='Logradouro', max_length=100)
    numero = models.IntegerField(verbose_name='Número')
    cidade = models.ForeignKey(Cidade, verbose_name='Cidade', null=True)

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'

    def __str__(self):
        return '{}, {}, {}'.format(self.logradouro, self.numero, self.cidade)

    @fieldset({'Dados Gerais': ('logradouro', ('numero', 'cidade'))})
    def add(self):
        super().add()

    @action('Visualizar')
    def view(self):
        return super().view()


class PessoaManager(models.DefaultManager):

    @action('Todas')
    def list(self):
        return self.list_display('id', 'nome')


@user('email')
class Pessoa(models.AbstractUser):

    nome = models.CharField(verbose_name='Nome', max_length=255)
    email = models.EmailField(verbose_name='E-mail', unique=True, max_length=255)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    endereco = models.OneToOneField(Endereco, verbose_name='Endereço', null=True, blank=True)

    telefones = models.OneToManyField(Telefone, verbose_name='Telefones')

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

    @action('Cadastrar', atomic=True)
    @fieldset({
        'Dados Gerais': ('nome', ('email', 'foto')),
        'Endereço': 'endereco',
        'Telefones': 'telefones'
    })
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

    @attr('Dados Gerais', display=True)
    def dados_gerais(self):
        return self.values('nome', ('email', 'foto'))

    @attr('Dados de Acesso', display=True)
    def dados_acesso(self):
        return self.values(('last_login', 'password'), 'groups')

    @attr('Grupos', display=True)
    def get_grupos(self):
        return self.groups

    @action('Atualizar Nome')
    @param(data_atualizacao=models.DateField())
    def atualizar_nome(self, nome):
        self.nome = nome
        self.save()

    @action('Alterar Senha')
    @param(senha=models.CharField('Senha'))
    def alterar_senha(self, senha):
        super().change_password(senha)


class PontoTuristicoManager(models.DefaultManager):

    @action('Todos')
    def list(self):
        return self.all()

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


class PontoTuristico(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)

    class Meta:
        verbose_name = 'Ponto Turístico'
        verbose_name_plural = 'Pontos Turísticos'

    def __str__(self):
        return '{}'.format(self.nome)

    @action('Visualizar')
    def view(self):
        return super().view()

    @action('Cadastrar')
    def add(self):
        super().add()

    @action('Editar')
    def edit(self):
        super().edit()

    @action('Atualizar Nome')
    def atualizar_nome(self, nome):
        raise models.ValidationError('Período de edição ainda não está aberto')

    @action('Excluir')
    def delete(self):
        super().delete()

    @attr('Cidades')
    def get_cidades(self):
        return self.cidade_set.all()


class PresidenteManager(models.DefaultManager):
    @action('Presidentes')
    def list(self):
        return self.all()


@role()
class Presidente(Pessoa):

    class Meta:
        verbose_name = 'Presidente'
        verbose_name_plural = 'Presidentes'

    def __str__(self):
        return '{}'.format(self.nome)


class GovernadorManager(models.DefaultManager):
    @action('Listar')
    def list(self):
        return self.all()


@role('pessoa')
class Governador(models.Model):
    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa')
    estado = models.ForeignKey(Estado, verbose_name='Estado')

    class Meta:
        verbose_name = 'Governador'
        verbose_name_plural = 'Governadores'

    def __str__(self):
        return '{} - {}'.format(self.pessoa, self.estado)
