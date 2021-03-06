# -*- coding: utf-8 -*-

import six
from django.apps import apps
from slothy.db import models
from django.contrib.auth import base_user


class Group(models.Model):
    name = models.CharField(verbose_name='Name', max_length=255)
    lookup = models.CharField(verbose_name='Chave', max_length=255)

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'

    def get_users(self):
        from django.conf import settings
        user_model_name = settings.AUTH_USER_MODEL.split('.')[1].lower()
        return getattr(self, '{}_set'.format(user_model_name)).all()

    def __str__(self):
        return self.name


class AbstractUser(six.with_metaclass(models.ModelBase, base_user.AbstractBaseUser, models.Model)):

    password = models.CharField(verbose_name='Senha', null=True, blank=True, default='!', max_length=255)
    last_login = models.DateTimeField(verbose_name='Último Login', null=True, blank=True)
    #is_superuser = models.BooleanField(verbose_name='Superusuário', default=False)
    groups = models.ManyToManyField(Group, verbose_name='Grupos', blank=True)

    class Meta:
        abstract = True

    def change_password(self, raw_password):
        super().set_password(raw_password)
        super().save()
