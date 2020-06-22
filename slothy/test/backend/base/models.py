# -*- coding: utf-8 -*-
from slothy.api import models
from slothy.api.models.decorators import expose, param


class UsuarioManager(models.DefaultManager):
    @expose()
    def add(self, **kwargs):
        return super().create(**kwargs)

    @expose()
    def list(self):
        return super().all()

    @expose()
    def delete(self):
        return super().delete()

    @expose('usuario')
    def ativos(self):
        return self.all()[0:1]


class Usuario(models.AbstractUser):
    USERNAME_FIELD = 'email'
    email = models.EmailField(verbose_name='E-mail', unique=True, max_length=255)
    nome = models.CharField(verbose_name='Nome', max_length=255)
    foto = models.ImageField(verbose_name='Foto', null=True, blank=True, upload_to='fotos')

    class Meta:
        icon = 'fa-users'
        menu = 'Usuários'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        list_display = 'nome', 'email'

    def __str__(self):
        return self.nome

    @expose()
    def delete(self):
        super().delete()

    @expose()
    @param(data_atualizacao=models.DateField())
    def atualizar_nome(self, nome, data_atualizacao):
        print(data_atualizacao)
        self.nome = nome
        self.save()

    @expose()
    @param(raw_password=models.CharField())
    def change_password(self, raw_password):
        super().change_password(raw_password)
