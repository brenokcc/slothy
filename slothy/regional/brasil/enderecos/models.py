# -*- coding: utf-8 -*-

from slothy.db import models, fieldsets, action, attr


class RegiaoSet(models.Set):

    @attr('Regiões', icon='map')
    def all(self):
        return self.display('nome', 'codigo')


class Regiao(models.Model):
    nome = models.CharField(verbose_name='Nome')
    codigo = models.CharField(verbose_name='Código')

    class Meta:
        verbose_name = 'Região'
        verbose_name_plural = 'Regiões'

    def __str__(self):
        return '{}'.format(self.nome)

    @action('Cadastrar')
    @fieldsets({'Dados Gerais': (('nome', 'codigo'),)})
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


class EstadoSet(models.Set):

    @attr('Estados', icon='map')
    def all(self):
        return self.display('nome', 'sigla', 'codigo', 'regiao').search('nome', 'sigla')


class Estado(models.Model):
    nome = models.CharField(verbose_name='Nome')
    sigla = models.CharField(verbose_name='Sigla')
    codigo = models.CharField(verbose_name='Código')
    regiao = models.ForeignKey(Regiao, verbose_name='Região', null=True, blank=False)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return '{}'.format(self.sigla)

    @action('Cadastrar')
    @fieldsets({'Dados Gerais': ('nome', ('sigla', 'codigo'), 'regiao')})
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


class MunicipioSet(models.Set):

    @attr('Municípios')
    def all(self):
        return self.display('nome', 'estado', 'codigo').search('nome')


class Municipio(models.Model):
    nome = models.CharField(verbose_name='Nome')
    estado = models.ForeignKey(Estado, verbose_name='Estado')
    codigo = models.CharField(verbose_name='Código')

    class Meta:
        icon = 'map'
        verbose_name = 'Município'
        verbose_name_plural = 'Municípios'

    def __str__(self):
        return '{}/{}'.format(self.nome, self.estado)

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
    cep = models.MaskedField(verbose_name='CEP', mask='00.000-000')
    logradouro = models.CharField(verbose_name='Logradouro')
    numero = models.CharField(verbose_name='Número')
    complemento = models.CharField(verbose_name='Complemento', null=True, blank=True)
    municipio = models.ForeignKey(Municipio, verbose_name='Município')
    bairro = models.CharField(verbose_name='Bairro')

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'

    def __str__(self):
        return self.pk and '{}, {}, {}'.format(self.logradouro, self.numero, self.municipio) or None

    @action('Cadastrar')
    @fieldsets({'Dados Gerais': (('cep', 'numero'), ('complemento', 'logradouro'), ('bairro', 'municipio'))})
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
