# -*- coding: utf-8 -*-

import six
from slothy.db import models
from django.contrib.auth import base_user


class User(six.with_metaclass(models.ModelBase, base_user.AbstractBaseUser, models.Model)):
    USERNAME_FIELD = 'username'
    username = models.CharField(verbose_name='Login', unique=True)
    password = models.CharField(verbose_name='Senha', null=True, blank=True, default='!', max_length=255)
    last_login = models.DateTimeField(verbose_name='Último Login', null=True, blank=True)
    is_superuser = models.BooleanField(verbose_name='Superusuário', default=False)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def change_password(self, raw_password):
        super().set_password(raw_password)
        super().save()
