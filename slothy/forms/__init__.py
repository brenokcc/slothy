# -*- coding: utf-8 -*-

import json
from collections import OrderedDict
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile
from django import forms
from slothy.api.utils import format_value, make_choices
from django.core.files.uploadedfile import InMemoryUploadedFile


class InputValidationError(BaseException):
    def __init__(self, error, errors=()):
        self.error = error or 'Por favor, corriga os erros abaixo'
        self.errors = errors


class Form(forms.Form):

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.title = None
        self.icon = None
        self.image = None
        self.center = False
        self.cancel = False

        metaclass = getattr(self, 'Meta', None)
        if metaclass:
            self.title = getattr(metaclass, 'title', self.title)
            self.icon = getattr(metaclass, 'icon', self.icon)
            self.image = getattr(metaclass, 'image', self.image)
            self.center = getattr(metaclass, 'center', self.center)
            self.cancel = getattr(metaclass, 'cancel', self.cancel)

        super().__init__(*args, **kwargs)

        # fieldsets
        if metaclass and hasattr(metaclass, 'fieldsets'):
            fieldsets = metaclass.fieldsets
        else:
            fieldsets = dict()
            fieldsets['Dados Gerais'] = []
            for field_name in self.fields:
                fieldsets['Dados Gerais'].append((field_name,))

        # metadata
        self.metadata = {}
        for name, field in self.fields.items():
            choices = make_choices(name, field, {})
            field_type = type(field).__name__.replace('Field', '').lower()
            mask = field.mask if hasattr(field, 'mask') else None
            item = OrderedDict(
                label=field.label, type=field_type, required=field.required,
                mask=mask, value=None, display=None, choices=choices, help_text=field.help_text,
                error=None, width=100
            )
            self.metadata[name] = item

        # initial data
        self.initial_data = {}
        for name, field in self.fields.items():
            value = self.initial.get(name)
            if isinstance(value, FieldFile):
                display = value.name
                value = None
            else:
                display = format_value(field.to_python(value))
            self.initial_data[name] = value
            self.metadata[name]['value'] = value
            self.metadata[name]['display'] = display

        # fieldsets
        self.fieldsets = {}
        for verbose_name, field_lists in fieldsets.items():
            if verbose_name is None:
                verbose_name = ''
            self.fieldsets[verbose_name] = {}
            for field_list in field_lists:
                if isinstance(field_list, str):
                    field_list = field_list,
                for field_name in field_list:
                    if field_name in self.metadata:
                        self.fieldsets[verbose_name][field_name] = self.metadata[field_name]

        # result
        self.result = None

    def show(self):
        return True

    def submit(self):
        pass

    def save(self, *args, **kwargs):
        error = None
        errors = []

        if self.errors:
            for inner_field_name, inner_messages in self.errors.items():
                errors.append(dict(field=inner_field_name, message=','.join(inner_messages)))

        try:
            self.submit()
        except ValidationError as ve:
            error = ''.join(ve.message)

        if error or errors:
            raise InputValidationError(error, errors)

    def serialize(self):
        return dict(
            type='form',
            path='/api/forms/{}'.format(self.__class__.__name__.lower()),
            name=self.title,
            icon=self.icon,
            image=self.image,
            center=self.center,
            cancel=self.cancel,
            input=self.initial_data,
            fieldsets=self.fieldsets,
            result=self.result.serialize() if self.result is not None else None
        )

    def log(self):
        print(json.dumps(self.serialize(), indent=2, sort_keys=False, ensure_ascii=False))


class ModelForm(forms.ModelForm):

    def __init__(self, title, func, params, exclude=None, fields=None, fieldsets=None, icon=None, request=None, **kwargs):
        self.request = request
        self.title = title
        self.icon = icon
        self.func = func
        self.params = params

        # custom initial
        method_name = '{}_initial'.format(func.__name__)
        custom_initial = getattr(kwargs['instance'], method_name)() if hasattr(kwargs['instance'], method_name) else {}
        initial = kwargs.pop('initial', {})
        for key in custom_initial:
            initial[key] = custom_initial[key]
        kwargs['initial'] = initial

        super().__init__(**kwargs)

        # custom fields
        if fields:
            for name, field in fields.items():
                self.fields[name] = field.formfield()

        # exclude fields
        if exclude and exclude in self.fields:
            del self.fields[exclude]

        for name in list(self.fields.keys()):
            field = self.fields[name]
            if hasattr(field, 'exclude') and field.exclude:
                queryset = field.queryset.apply_lookups(self.request.user, field.exclude)
                if queryset.count() == 1:
                    setattr(self.instance, name, queryset.first())
                    del self.fields[name]

        # fieldsets
        if fieldsets is None:
            fieldsets = dict()
            if self.fields:
                fieldsets['Dados Gerais'] = []
                for field_name in self.fields:
                    fieldsets['Dados Gerais'].append((field_name,))

        field_width = dict()
        forgotten_fields = list(self.fields.keys())
        for verbose_name, field_lists in fieldsets.items():
            for field_list in field_lists:
                for field_name in field_list:
                    field_width[field_name] = 100 // len(field_list)
                    if field_name in forgotten_fields:
                        forgotten_fields.remove(field_name)
        if forgotten_fields:
            fieldsets['Extra'] = forgotten_fields

        # custom choices
        method_name = '{}_choices'.format(func.__name__)
        custom_choices = getattr(self.instance, method_name)() if hasattr(self.instance, method_name) else {}

        # metadata
        self.metadata = {}
        exclude = []
        for name, field in self.fields.items():
            readonly = False
            if hasattr(field, 'readonly'):
                queryset = field.queryset.apply_lookups(self.request.user, field.lookup)
                if queryset.count() == 1:
                    setattr(self.instance, name, queryset.first())
                    readonly = True
            choices = make_choices(name, field, custom_choices)
            field_type = type(field).__name__.replace('Field', '').lower()
            mask = field.mask if hasattr(field, 'mask') else None
            item = OrderedDict(
                label=field.label, type=field_type, required=field.required, readonly=readonly,
                mask=mask, value=None, display=None, choices=choices, help_text=field.help_text,
                error=None, width=field_width.get(name, 100)
            )
            self.metadata[name] = item

        # one-to-one
        self.one_to_one_forms = {}
        one_to_one_field_names = [
            name for name in self.fields if hasattr(self.fields[name], '_is_one_to_one')
        ]
        for one_to_one_field_name in one_to_one_field_names:
            one_to_one_items = {}
            one_to_one_field = self.fields[one_to_one_field_name]
            del (self.fields[one_to_one_field_name])
            one_to_one_form_cls = forms.modelform_factory(one_to_one_field.queryset.model, exclude=())
            if hasattr(one_to_one_field.queryset.model, 'add'):
                one_to_one_fieldsets = getattr(
                    one_to_one_field.queryset.model.add, '_metadata', {}
                ).get('fieldsets', {})
                one_to_one_field_width = dict()
                for verbose_name, field_lists in one_to_one_fieldsets.items():
                    for field_list in field_lists:
                        for field_name in field_list:
                            one_to_one_field_width[field_name] = 100 // len(field_list)
            else:
                one_to_one_field_width = {}
            for name, field in one_to_one_form_cls.base_fields.items():
                choices = make_choices(name, field, custom_choices)
                field_type = type(field).__name__.replace('Field', '').lower()
                mask = field.mask if hasattr(field, 'mask') else None
                item = OrderedDict(
                    label=field.label, type=field_type, required=field.required,
                    mask=mask, value=None, display=None, choices=choices, help_text=field.help_text,
                    error=None, one_to_one=one_to_one_field_name, width=one_to_one_field_width.get(name, 100)
                )
                one_to_one_items[name] = item
            self.metadata[one_to_one_field_name] = one_to_one_items
            one_to_one_form_instance = getattr(self.instance, one_to_one_field_name)
            if one_to_one_field.required:
                one_to_one_form_data = self.data.get(one_to_one_field_name) or {}
            else:
                one_to_one_form_data = self.data.get(one_to_one_field_name)

            one_to_one_form = one_to_one_form_cls(
                data=one_to_one_form_data,
                instance=one_to_one_form_instance
            )
            self.one_to_one_forms[one_to_one_field_name] = one_to_one_form

        # one-to-many
        self.one_to_many_forms = {}
        one_to_many_field_names = [
            name for name in self.fields if hasattr(self.fields[name], '_is_one_to_many')
        ]
        for one_to_many_field_name in one_to_many_field_names:
            one_to_many_items = {}
            one_to_many_field = self.fields[one_to_many_field_name]
            del (self.fields[one_to_many_field_name])
            one_to_many_form_cls = forms.modelform_factory(one_to_many_field.queryset.model, exclude=())
            if hasattr(one_to_many_field.queryset.model, 'add'):
                one_to_many_fieldsets = getattr(
                    one_to_many_field.queryset.model.add, '_metadata', {}
                ).get('fieldsets', {})
                one_to_many_field_width = dict()
                for verbose_name, field_lists in one_to_many_fieldsets.items():
                    for field_list in field_lists:
                        for field_name in field_list:
                            one_to_many_field_width[field_name] = 100 // len(field_list)
            else:
                one_to_many_field_width = {}
            for name, field in one_to_many_form_cls.base_fields.items():
                choices = make_choices(name, field, custom_choices)
                field_type = type(field).__name__.replace('Field', '').lower()
                mask = field.mask if hasattr(field, 'mask') else None
                item = OrderedDict(
                    label=field.label, type=field_type, required=field.required,
                    mask=mask, value=None, display=None, choices=choices, help_text=field.help_text,
                    error=None, one_to_many=one_to_many_field_name, width=one_to_many_field_width.get(name, 100)
                )
                one_to_many_items[name] = item
            self.metadata[one_to_many_field_name] = [one_to_many_items]
            self.one_to_many_forms[one_to_many_field_name] = []
            one_to_many_data = self.data.get(one_to_many_field_name, [])
            one_to_many_instances = self.instance.pk and getattr(
                self.instance, one_to_many_field_name).order_by('id') or [None]

            for i in range(0, max(len(one_to_many_data), len(one_to_many_instances))):
                one_to_many_form_data = None
                one_to_many_form_instance = None
                if len(one_to_many_data) > i:
                    one_to_many_form_data = one_to_many_data[i] or None
                if len(one_to_many_instances) > i:
                    one_to_many_form_instance = one_to_many_instances[i]

                one_to_many_form = one_to_many_form_cls(
                    instance=one_to_many_form_instance,
                    data=one_to_many_form_data
                )
                self.one_to_many_forms[one_to_many_field_name].append(one_to_many_form)

        # initial data
        self.initial_data = {}
        for name, field in self.fields.items():
            if name in self.metadata:
                value = self.initial.get(name)
                is_cf = isinstance(field, forms.MultipleChoiceField) or isinstance(field, forms.ModelMultipleChoiceField)
                if value is None and is_cf:
                    value = []
                if isinstance(value, FieldFile):
                    display = value.name
                    value = None
                else:
                    display = format_value(field.to_python(value))
                self.initial_data[name] = value
                self.metadata[name]['value'] = value
                self.metadata[name]['display'] = display
        for one_to_one_field_name, one_to_one_form in self.one_to_one_forms.items():
            self.initial_data[one_to_one_field_name] = {}
            for name, field in one_to_one_form.fields.items():
                value = one_to_one_form.initial.get(name)
                self.initial_data[one_to_one_field_name][name] = value
                self.metadata[one_to_one_field_name][name]['value'] = format_value(field.to_python(value))
        for one_to_many_field_name, one_to_many_forms in self.one_to_many_forms.items():
            self.initial_data[one_to_many_field_name] = []
            for one_to_many_form in one_to_many_forms:
                one_to_many_initial_data = {}
                for name in one_to_many_form.fields:
                    one_to_many_initial_data[name] = one_to_many_form.initial.get(name)
                self.initial_data[one_to_many_field_name].append(one_to_many_initial_data)

        # fieldsets
        self.fieldsets = {}
        for verbose_name, field_lists in fieldsets.items():
            if verbose_name is None:
                verbose_name = ''
            self.fieldsets[verbose_name] = {}
            for field_list in field_lists:
                for field_name in field_list:
                    if field_name in self.one_to_one_forms:
                        for inner_field_name, inner_field in self.metadata[field_name].items():
                            self.fieldsets[verbose_name][inner_field_name] = inner_field
                    elif field_name in self.one_to_many_forms:
                        self.fieldsets[verbose_name] = self.metadata[field_name]
                    elif field_name in self.metadata:
                        self.fieldsets[verbose_name][field_name] = self.metadata[field_name]

        # result
        self.result = None

    def _clean_fields(self):
        for name, field in self.fields.items():
            if isinstance(field, forms.FileField):
                if name in self.data:
                    if self.data[name]:
                        data = json.loads(self.data[name])
                        file_path = '{}{}'.format(settings.BASE_DIR, data['path'])
                        self.files[name] = InMemoryUploadedFile(
                            open(file_path, 'rb'),
                            field_name=name,
                            name=data['name'],
                            content_type=data['content_type'],
                            size=data['size'],
                            charset=data['charset']
                        )

        return super()._clean_fields()

    def save(self, *args, **kwargs):
        error = None
        errors = []
        # print(data, form.cleaned_data)
        # print(form.fields.keys(), custom_fields.keys(), metadata['params'])
        if self.errors:
            for inner_field_name, inner_messages in self.errors.items():
                errors.append(dict(field=inner_field_name, message=','.join(inner_messages)))
        else:
            # one-to-one
            for one_to_one_field_name, one_to_one_form in self.one_to_one_forms.items():
                if one_to_one_form.is_valid():
                    one_to_one_form.save()
                    setattr(self.instance, one_to_one_field_name, one_to_one_form.instance)
                elif one_to_one_form.errors:
                    for inner_field_name, inner_messages in one_to_one_form.errors.items():
                        errors.append(dict(
                            field=inner_field_name,
                            message=','.join(inner_messages),
                            one_to_one=one_to_one_field_name
                        ))
            # func
            params = {}
            for param in self.params:
                params[param] = self.cleaned_data.get(param)
            try:
                self.result = self.func(**params)
                if self.base_fields and hasattr(self, 'cleaned_data'):
                    self._save_m2m()
            except ValidationError as ve:
                error = ''.join(ve.message)

            # one-to-many
            for one_to_many_field_name, one_to_many_forms in self.one_to_many_forms.items():
                for i, one_to_many_form in enumerate(one_to_many_forms):
                    if one_to_many_form.data:
                        if one_to_many_form.is_valid():
                            one_to_many_form.save()
                            getattr(self.instance, one_to_many_field_name).add(one_to_many_form.instance)
                        else:
                            for inner_field_name, inner_messages in one_to_many_form.errors.items():
                                errors.append(dict(
                                    field=inner_field_name,
                                    message=','.join(inner_messages),
                                    one_to_many=one_to_many_field_name,
                                    index=i
                                ))

        if error or errors:
            raise InputValidationError(error, errors)

    def serialize(self, path):
        return dict(
            type='form',
            path=path,
            name=self.title,
            icon=self.icon,
            input=self.initial_data,
            fieldsets=self.fieldsets,
            result=self.result.serialize() if self.result is not None else None
        )
