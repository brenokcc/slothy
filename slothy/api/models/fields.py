from django.db import models
from slothy.forms import fields as form_fields


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
        field = super().formfield(*args, **kwargs)
        setattr(field, '_is_one_to_one', True)
        return field


class RoleForeignKey(ForeignKey):
    pass


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

    def formfield(self, **kwargs):
        return form_fields.ColorField(**kwargs)
