# -*- coding: utf-8 -*-

from django.db import models
from slothy.forms import fields as form_fields
from django.db.models.fields import files as file_fields


ImageField = file_fields.ImageField
FileField = file_fields.FileField


class CharField(models.CharField):
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs.update(max_length=255)
        if 'is_username' in kwargs:
            self.is_username = kwargs.pop('is_username')
        super().__init__(*args, **kwargs)


class EmailField(models.EmailField):
    def __init__(self, *args, **kwargs):
        if 'max_length' not in kwargs:
            kwargs.update(max_length=255)
        if 'is_username' in kwargs:
            self.is_username = kwargs.pop('is_username')
        super().__init__(*args, **kwargs)


class ForeignKey(models.ForeignKey):
    def __init__(self, to, **kwargs):
        on_delete = kwargs.pop('on_delete', models.CASCADE)
        self.filter_display = kwargs.pop('filter_display', ('__str__',))
        super().__init__(to, on_delete, **kwargs)


class OneToOneField(models.OneToOneField):
    def __init__(self, to, **kwargs):
        on_delete = kwargs.pop('on_delete', models.SET_NULL)
        super().__init__(to, on_delete, **kwargs)

    def formfield(self, *args, **kwargs):
        field = super().formfield(**kwargs)
        setattr(field, '_is_one_to_one', True)
        return field


class RoleForeignKey(ForeignKey):
    pass


class RoleField(ForeignKey):
    inherits_role = True


class OneToManyField(models.ManyToManyField):
    def formfield(self, *args, **kwargs):
        field = super().formfield(*args, **kwargs)
        setattr(field, '_is_one_to_many', True)
        return field


class RoleManyToManyField(models.ManyToManyField):
    pass


class ColorField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.update(max_length=10, default='#FFFFFF')
        super().__init__(*args, **kwargs)

    def formfield(self, **defaults):
        defaults.update(form_class=form_fields.ColorField)
        if 'initial' not in defaults:
            defaults.update(initial='#FFFFFF')
        return super().formfield(**defaults)


class MaskedField(CharField):
    mask = None

    def __init__(self, *args, **kwargs):
        if 'mask' in kwargs:
            self.mask = kwargs.pop('mask')
        super().__init__(*args, **kwargs)

    def formfield(self, **defaults):
        defaults.update(form_class=form_fields.MaskedField)
        defaults.update(mask=self.mask)
        return super().formfield(**defaults)


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


class GeoLocationField(CharField):
    def formfield(self, **defaults):
        defaults.update(form_class=form_fields.GeolocationField)
        return super().formfield(**defaults)
