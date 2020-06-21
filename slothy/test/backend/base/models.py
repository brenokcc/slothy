# -*- coding: utf-8 -*-
from slothy.api import models


class UsuarioManager(models.DefaultManager):
    def ativos(self):
        return self.all()[0:1]


class Usuario(models.AbstractUser):
    USERNAME_FIELD = 'email'
    email = models.EmailField(verbose_name='E-mail', unique=True, max_length=255)
    nome = models.CharField(verbose_name='Nome', max_length=255)

    class Meta:
        icon = 'fa-users'
        menu = 'Usuários'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        list_display = 'nome', 'email'
        list_actions = 'alterar_senha',

    def __str__(self):
        return self.nome