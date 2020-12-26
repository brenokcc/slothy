# -*- coding: utf-8 -*-
from slothy.api import models
from slothy.api.models.decorators import param, meta, role, user


@user('email')
class Pessoa(models.AbstractUser):

    nome = models.CharField(verbose_name='Nome', max_length=255)
    email = models.EmailField(verbose_name='E-mail', unique=True, max_length=255)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    class Meta:
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'
        list_display = 'nome', 'email'

    def __str__(self):
        return self.nome

    def delete(self):
        super().delete()

    @param(data_atualizacao=models.DateField())
    def atualizar_nome(self, nome):
        self.nome = nome
        self.save()

    @param(raw_password=models.CharField('Senha'))
    def change_password(self, raw_password):
        super().change_password(raw_password)


class PontoTuristicoManager(models.DefaultManager):

    @meta('Todos')
    def list(self):
        return self.all()

    @meta('Referenciados')
    def referenciados(self):
        return self.filter(cidade__isnull=False)

    @meta('Referenciados')
    @param(sigla=models.CharField())
    def referenciados_no_estado(self, sigla):
        return self.filter(cidade__estado__sigla=sigla)

    @classmethod
    @meta('Remover Tudo')
    def remover_tudo(cls):
        PontoTuristico.objects.all().delete()


class PontoTuristico(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)

    class Meta:
        verbose_name = 'Ponto Turístico'
        verbose_name_plural = 'Pontos Turísticos'

    def __str__(self):
        return '{}'.format(self.nome)

    @meta('Cadastrar')
    def add(self):
        self.save()

    @meta('Editar')
    def edit(self):
        if self.pk:
            raise models.ValidationError('Período de edição ainda não está aberto')
        self.save()

    @meta('Visualizar')
    def view(self):
        return self.values('nome')

    @meta('Remover')
    def remove(self):
        self.delete()


class EstadoManager(models.DefaultManager):

    @meta('Todos')
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
        )

    @meta('Ativos')
    def ativos(self):
        return self.filter(ativo=True)

    @meta('Inativos')
    def inativos(self):
        return self.filter(ativo=False)

    @meta('Ativar')
    def ativar(self):
        self.update(ativo=True)

    @meta('Agendar Inativacao')
    @param(data=models.DateField('Data'))
    def agendar_inativacao(self, data):
        self.update(ativo=False)

    @meta('Atualizar Status')
    def atualizar_status(self, ativo):
        self.update(ativo=ativo)

    @meta('Agendar Atualização de Status')
    @param(data=models.DateField('Data'))
    def agendar_atualizacao_status(self, ativo, data):
        self.update(ativo=ativo)

    @classmethod
    @meta('Inativar Todos')
    def inativar_todos(cls):
        Estado.objects.update(ativo=False)

    @classmethod
    @meta('Agendar Inativação Total')
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

    @meta('Visualizar')
    def view(self):
        return self.values('dados_gerais', 'dados_populacionais')

    @meta('Dados Gerais')
    def dados_gerais(self):
        return self.values('nome', ('sigla', 'ativo'))

    @meta('Dados Populacionais')
    def dados_populacionais(self):
        return self.values('get_populacao')

    @meta('Cadastrar')
    def add(self):
        self.save()

    @meta('Editar')
    def edit(self):
        self.save()

    @meta('Excluir')
    def remove(self):
        self.delete()

    @meta('Ativar')
    def ativar(self):
        self.ativo = True
        self.save()

    @meta('Ativar')
    def inativar(self):
        self.ativo = False
        self.save()

    @meta('População')
    def get_populacao(self):
        return 279876

    @meta('Cidades')
    def get_cidades(self):
        return self.cidade_set.all().list_filter('estado')

    @meta('Alterar Sigla')
    def alterar_sigla(self, sigla):
        self.sigla = sigla
        self.save()

    @meta('Programar Ativação')
    @param(data=models.DateField('Data da Ativação'))
    def programar_ativacao(self, data):
        pass


class PresidenteManager(models.DefaultManager):
    @meta('Presidentes')
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
    @meta('Listar')
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


class CidadeManager(models.DefaultManager):

    @meta('Listar')
    def list(self):
        return self.all()


class Cidade(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE)
    prefeito = models.RoleForeignKey(Pessoa, verbose_name='Prefeito', null=True, blank=True)
    vereadores = models.RoleManyToManyField(Pessoa, verbose_name='Vereadores', blank=True, related_name='cidades_legisladas')
    pontos_turisticos = models.ManyToManyField(PontoTuristico, verbose_name='Pontos Turísticos', blank=True)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return '{}/{}'.format(self.nome, self.estado)

    @meta('Adicionar')
    def add(self):
        self.save()

    @meta('Pontos Turísticos')
    def get_pontos_turisticos(self):
        return self.pontos_turisticos
