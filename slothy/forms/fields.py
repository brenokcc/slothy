# -*- coding: utf-8 -*-

from django import forms
from django.conf import settings


class ColorField(forms.ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.update(initial='#FFFFFF')
        kwargs.pop('max_length')
        if 'choices' not in kwargs:
            colors = settings.THEME['COLORS']
            kwargs.update(choices=[[color, color] for color in colors])
        super().__init__(*args, **kwargs)


class MaskedField(forms.CharField):
    mask = None

    def __init__(self, *args, **kwargs):
        if 'mask' in kwargs:
            self.mask = kwargs.pop('mask')
        super().__init__(*args, **kwargs)


class GeolocationField(forms.CharField):
    pass


class CpfField(MaskedField):
    mask = '000.000.000-00'


class CnpjField(MaskedField):
    mask = '00.000.000/0000-00'


class CepField(MaskedField):
    mask = '00.000-000'


class PlacaField(MaskedField):
    mask = 'AAA-0A00'


class TelefoneField(MaskedField):
    mask = '(00) 00000-0000'

