# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth import login, authenticate
from django.core import signing
from django.core.exceptions import ValidationError
from slothy.forms import Form


class LoginForm(Form):
    username = forms.CharField(label='Usuário')
    password = forms.CharField(label='Senha')

    class Meta:
        image = '/static/round-blue.png'
        center = True
        lookups = ()
        fieldsets = {
            None: ('username', 'password')
        }

    def show(self):
        return super().show()

    def submit(self):
        user = authenticate(
            self.request, username=self.data['username'],
            password=self.data['password']
        )
        if user:
            login(self.request, user)
            return dict(
                type='login',
                message='Login realizado com sucesso',
                token=signing.dumps(self.request.user.id)
            )
        raise ValidationError('Usuário e senha não conferem')
