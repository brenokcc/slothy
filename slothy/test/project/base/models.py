# -*- coding: utf-8 -*-
from slothy.api import models
from slothy.api.models.decorators import param, meta


class Usuario(models.AbstractUser):
    USERNAME_FIELD = 'email'
    email = models.EmailField(verbose_name='E-mail', unique=True, max_length=255)
    nome = models.CharField(verbose_name='Nome', max_length=255)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
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


class PontoTuristico(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)

    class Meta:
        verbose_name = 'Ponto Turístico'
        verbose_name_plural = 'Pontos Turísticos'

    def __str__(self):
        return '{}'.format(self.nome)


class EstadoManager(models.DefaultManager):

    @meta('Todos')
    def list(self):
        return self.filter(
            pk__lte=10
        ).list_display(
            'nome', 'ativo'
        ).list_filter(
            'ativo'
        ).list_actions(
            'inativar'
        ).list_search(
            'inativar'
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

    def inativar(self):
        self.update(ativo=True)


class Estado(models.Model):
    nome = models.CharField(verbose_name='Nome', max_length=255)
    sigla = models.CharField(verbose_name='Sigla', max_length=255)
    ativo = models.BooleanField(verbose_name='Ativo', default=True)

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return '{}'.format(self.sigla)

    def view(self):
        self.values('nome', ('sigla', 'estado'))

    def add(self):
        self.save()

    def edit(self):
        self.save()

    def remove(self):
        self.delete()

    def ativar(self):
        self.ativo = True
        self.save()

    def inativar(self):
        self.ativo = False
        self.save()

    def get_cidades(self):
        return self.cidade_set

    def alterar_sigla(self, sigla):
        self.sigla = sigla
        self.save()


class Cidade(models.Model):
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE)
    nome = models.CharField(verbose_name='Nome', max_length=255)
    pontos_turisticos = models.ManyToManyField(PontoTuristico, verbose_name='Pontos Turísticos')

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return '{}/{}'.format(self.nome, self.estado)

    def get_pontos_turisticos(self):
        return self.pontos_turisticos

