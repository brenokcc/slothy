from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile
from django.forms import ModelForm, modelform_factory
from slothy.api.utils import format_value, make_choices


class InputValidationError(BaseException):
    def __init__(self, errors, metadata, initial_data):
        self.errors = errors
        self.metadata = metadata
        self.initial_data = initial_data


class ApiModelForm(ModelForm):

    def __init__(self, title, func, params, exclude=None, fields=None, fieldsets=None, **kwargs):
        self.title = title
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
            del (self.fields[exclude])

        # fieldsets
        if fieldsets is None:
            fieldsets = dict()
            fieldsets['Dados Gerais'] = []
            for field_name in self.fields:
                fieldsets['Dados Gerais'].append((field_name,))

        field_width = dict()
        for verbose_name, field_lists in fieldsets.items():
            for field_list in field_lists:
                for field_name in field_list:
                    field_width[field_name] = 100//len(field_list)

        # custom choices
        method_name = '{}_choices'.format(func.__name__)
        custom_choices = getattr(self.instance, method_name)() if hasattr(self.instance, method_name) else {}

        # metadata
        self.metadata = {}
        for name, field in self.fields.items():
            choices = make_choices(name, field, custom_choices)
            field_type = type(field).__name__.replace('Field', '').lower()
            item = OrderedDict(
                label=field.label, type=field_type, required=field.required,
                mask=None, value=None, choices=choices, help_text=field.help_text,
                width=field_width.get(name, 100)
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
            one_to_one_form_cls = modelform_factory(one_to_one_field.queryset.model, exclude=())
            if hasattr(one_to_one_field.queryset.model, 'add'):
                one_to_one_field_width = getattr(
                    one_to_one_field.queryset.model.add, '_metadata', {}
                ).get('field_width', {})
            else:
                one_to_one_field_width = {}
            for name, field in one_to_one_form_cls.base_fields.items():
                choices = make_choices(name, field, custom_choices)
                field_type = type(field).__name__.replace('Field', '').lower()
                item = OrderedDict(
                    label=field.label, type=field_type, required=field.required,
                    mask=None, value=None, choices=choices, help_text=field.help_text,
                    width=one_to_one_field_width.get(name, 100)
                )
                one_to_one_items[name] = item
            self.metadata[one_to_one_field_name] = one_to_one_items
            one_to_one_form_instance = getattr(self.instance, one_to_one_field_name)
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
            one_to_many_form_cls = modelform_factory(one_to_many_field.queryset.model, exclude=())
            for name, field in one_to_many_form_cls.base_fields.items():
                choices = make_choices(name, field, custom_choices)
                field_type = type(field).__name__.replace('Field', '').lower()
                item = OrderedDict(
                    label=field.label, type=field_type, required=field.required,
                    mask=None, value=None, choices=choices, help_text=field.help_text,
                    width=100 // len(one_to_many_form_cls.base_fields)
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
                    one_to_many_form_data = one_to_many_data[i]
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
            value = self.initial.get(name)
            if isinstance(value, FieldFile):
                value = value.name or None
            self.initial_data[name] = value
            self.metadata[name]['value'] = format_value(field.to_python(value))
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

    def save(self, *args, **kwargs):
        inner_errors = []
        # print(data, form.cleaned_data)
        # print(form.fields.keys(), custom_fields.keys(), metadata['params'])

        if self.errors:
            for inner_field_name, inner_messages in self.errors.items():
                inner_errors.append({'message': ','.join(inner_messages), 'field': inner_field_name})
        else:
            # one-to-one
            for one_to_one_field_name, one_to_one_form in self.one_to_one_forms.items():
                if one_to_one_form.is_valid():
                    one_to_one_form.save()
                    setattr(self.instance, one_to_one_field_name, one_to_one_form.instance)
                elif one_to_one_form.errors:
                    for i, (inner_field_name, inner_messages) in enumerate(one_to_one_form.errors.items()):
                        inner_errors.append(
                            {'message': ','.join(inner_messages), 'field': one_to_one_field_name,
                             'index': i, 'inner': inner_field_name}
                        )
            # func
            params = {}
            for param in self.params:
                params[param] = self.cleaned_data.get(param)
            try:
                self.result = self.func(**params)
            except ValidationError as ve:
                inner_errors.append({'message': ve.message, 'field': None})

            # one-to-many
            for one_to_many_field_name, one_to_many_forms in self.one_to_many_forms.items():
                for one_to_many_form in one_to_many_forms:
                    if one_to_many_form.is_valid():
                        one_to_many_form.save()
                        getattr(self.instance, one_to_many_field_name).add(one_to_many_form.instance)
                    elif one_to_many_form.errors:
                        inner_errors = []
                        for i, (inner_field_name, inner_messages) in enumerate(one_to_many_form.errors.items()):
                            inner_errors.append(
                                {'message': ','.join(inner_messages), 'field': one_to_many_field_name,
                                 'index': i, 'inner': inner_field_name}
                            )

        if inner_errors:
            raise InputValidationError(inner_errors, self.fieldsets, self.initial_data)

    def serialize(self, as_view=True):
        serialized = dict(
            type='form',
            input=dict(data=self.initial_data, metadata=self.fieldsets),
            result=self.result.serialize() if self.result is not None else None
        )
        if as_view:
            return dict(
                type='form_view',
                title=self.title,
                form=serialized
            )
        else:
            return serialized