# -*- coding: utf-8 -*-
import six
import json
from django.contrib.auth import base_user
from django.db.models import query, base, manager, Sum, Count, Avg
from django.db import models
from django.db.models.fields import related
from django.db.models.fields import *
from django.db.models.fields.files import *
from django.db.models.fields.related import *
from slothy.api.utils import getattrr
from slothy.api import utils
import zlib
import base64
import _pickle as cpickle
from django.apps import apps
from django.core import signing
from django.db.models import Q
import operator
import codecs
from collections import UserDict
from functools import reduce
from django.core import exceptions
from django.conf import settings


ValidationError = exceptions.ValidationError


class ForeignKey(models.ForeignKey):
    def __init__(self, to, **kwargs):
        on_delete = kwargs.pop('on_delete', models.CASCADE)
        super().__init__(to, on_delete, **kwargs)


class RoleForeignKey(ForeignKey):
    pass


class RoleManyToManyField(models.ManyToManyField):
    pass


class ModelGeneratorWrapper:
    def __init__(self, generator, user):
        self.generator = generator
        self._user = user

    def __iter__(self):
        return self

    def __next__(self):
        obj = next(self.generator)
        obj._user = self._user
        return obj


class ModelIterable(query.ModelIterable):

    def __iter__(self):
        generator = super(ModelIterable, self).__iter__()
        return ModelGeneratorWrapper(generator, getattr(self.queryset, '_user'))


class QuerySetStatistic(object):

    MONTHS = ('JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ')

    def __init__(self, qs, x, y=None, func=Count, z='id'):
        self.qs = qs
        self.x = x
        self.y = y
        self.func = func
        self.z = z
        self._xfield = None
        self._yfield = None
        self._xdict = {}
        self._ydict = {}
        self._values_dict = None

        if '__month' in x:
            self._xdict = {i+1: month for i, month in enumerate(QuerySetStatistic.MONTHS)}
        if y and '__month' in y:
            self._ydict = {i + 1: month for i, month in enumerate(QuerySetStatistic.MONTHS)}

    @property
    def xfield(self):
        self._calc()
        return self._xfield

    @property
    def yfield(self):
        self._calc()
        return self._yfield

    @property
    def xdict(self):
        self._calc()
        return self._xdict

    @property
    def ydict(self):
        self._calc()
        return self._ydict

    @property
    def values_dict(self):
        self._calc()
        return self._values_dict

    def _calc(self):
        if self._values_dict is None:
            self.calc()

    def _xfield_display_value(self, value):
        if hasattr(self._xfield, 'choices') and self._xfield.choices:
            for choice in self._xfield.choices:
                if choice[0] == value:
                    return choice[1]
        return value

    def _yfield_display_value(self, value):
        if hasattr(self._yfield, 'choices') and self.yfield.choices:
            for choice in self.yfield.choices:
                if choice[0] == value:
                    return choice[1]
        return value

    def _clear(self):
        self._xfield = None
        self._yfield = None
        self._xdict = {}
        self._ydict = {}
        self._values_dict = None

    def calc(self):
        self._values_dict = {}
        values_list = self.qs.values_list(self.x, self.y).annotate(
            self.func(self.z)) if self.y else self.qs.values_list(self.x).annotate(self.func(self.z))
        self._xfield = self.qs.model.get_field(self.x.replace('__year', '').replace('__month', ''))
        if self._xdict == {}:
            if self._xfield.related_model:
                self._xdict = {
                    obj.pk: str(obj) for obj in self._xfield.related_model.objects.filter(
                        pk__in=self.qs.values_list(self.x, flat=True).order_by(self.x).distinct())
                }
            else:
                self._xdict = {
                    value: value for value in self.qs.values_list(self.x, flat=True).order_by(self.x).distinct()
                }
        if self.y:
            self._yfield = self.qs.model.get_field(self.y.replace('__year', '').replace('__month', ''))
            if self._ydict == {}:
                if self._yfield.related_model:
                    self._ydict = {
                        obj.pk: str(obj) for obj in self._yfield.related_model.objects.filter(
                            pk__in=self.qs.values_list(self.y, flat=True).order_by(self.y).distinct())
                    }
                else:
                    self._ydict = {
                        value: value for value in self.qs.values_list(self.y, flat=True).order_by(self.y).distinct()
                    }
            self._values_dict = {(vx, vy): calc for vx, vy, calc in values_list}
        else:
            self._ydict = {}
            self._values_dict = {(vx, None): calc for vx, calc in values_list}
        self._xdict[None] = self._ydict[None] = None

    def filter(self, **kwargs):
        self._clear()
        self.qs = self.qs.filter(**kwargs)
        return self

    def apply_lookups(self, user, lookups=None):
        self._clear()
        if lookups is None:
            lookups = self.qs.model.get_metadata('list_lookups')
        self.qs = self.qs.apply_lookups(user, lookups)
        return self

    def list(self):
        self._calc()
        rows = []
        if self._yfield:
            row = [('', None)]
            for key, value in self._ydict.items():
                if key is not None:
                    row.append((self._yfield_display_value(value), None))
            rows.append(row)
        for xkey, xvalue in self._xdict.items():
            if xkey is not None:
                row = [(str(self._xfield_display_value(xvalue)), None)]
                if self._yfield:
                    for ykey, yvalue in self._ydict.items():
                        if ykey is not None:
                            row.append((self._values_dict.get((xkey, ykey), 0), {self.x: xkey, self.y: ykey}))
                else:
                    row.append((self._values_dict.get((xkey, None), 0), {self.x: xkey}))
                rows.append(row)
        return rows


class ValuesDict(UserDict):

    def __init__(self, obj, *lookups, verbose_key=True):
        self.obj = obj
        self.lookups = lookups
        self.image_lookup = None
        self.actions_lookups = []
        self.nested_keys = []
        super().__init__()
        _values = []
        for lookup in lookups:
            keys = []
            if not isinstance(lookup, tuple):
                lookup = lookup,
            for attr in lookup:
                verbose_name = obj.get_verbose_name(attr)
                value = obj.value(attr, serialized=True)
                value = utils.custom_serialize(value)
                self[verbose_name] = value
                keys.append(verbose_name)
            self.nested_keys.append(keys)

    def image(self, lookup):
        self.image_lookup = lookup
        self[lookup] = self.get_image()
        return self

    def actions(self, *lookups):
        self.actions_lookups = lookups
        return self

    def get_nested_values(self):
        _values = []
        for key_list in self.nested_keys:
            values = []
            for key in key_list:
                values.append((key, self[key]))
            _values.append(values)
        return _values

    def get_actions(self):
        actions = []
        for lookup in self.actions_lookups:
            actions.append(self.obj.get_attr_metadata(lookup))
        return actions

    def get_image(self):
        return self.image_lookup and getattr(self.obj, self.image_lookup) or None

    def serialize(self):
        return str(self)


class QuerySet(query.QuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None
        self._slice = None
        self._list_display = ()
        self._list_filter = ()
        self._list_subsets = ()
        self._list_actions = ()
        self._list_per_page = 5
        self._list_search = None
        self._page = 0
        self._subset = None
        self._q = None
        self._filters = []
        self._actions = []
        self._subsets = []
        self._display = []
        self._deserialized = False
        self._related_manager = None
        self._related_attribute = None
        self._iterable_class = ModelIterable

    def filter(self, *args, **kwargs):
        low_mark = self.query.low_mark
        high_mark = self.query.high_mark
        self.query.low_mark = 0
        self.query.high_mark = None
        qs = super().filter(*args, **kwargs)
        qs.query.low_mark = low_mark
        qs.query.high_mark = high_mark
        return qs

    def values_list(self, *field_names, flat=False, named=False):
        if not field_names and self._list_display:
            field_names = self._list_display
        return super().values_list(*field_names, flat=flat, named=named)

    def list_display(self, *list_display):
        self._list_display = list_display
        return self

    def get_list_display(self, exclude=()):
        list_display = self._list_display
        if not list_display:
            list_display = self.model.get_metadata('list_display')
            if not list_display:
                local_fields = self.model.get_metadata('local_fields')
                list_display = [field.name for field in local_fields
                                if field.name not in exclude]
            self._list_display = list_display
        return self._list_display

    def list_filter(self, *list_filter):
        self._list_filter = list_filter
        return self

    def get_list_filter(self, add_default=False):
        if self._list_filter is None and add_default:
            self._list_filter = self.model.get_metadata('list_filter')
        return self._list_filter

    def list_subsets(self, *list_subsets):
        self._list_subsets = list_subsets
        return self

    def get_list_subsets(self, add_default=False):
        if self._list_subsets is None and add_default:
            self._list_subsets = self.model.get_metadata('list_subsets')
        return self._list_subsets

    def list_actions(self, *list_actions):
        self._list_actions = list_actions
        return self

    def get_list_actions(self, add_default=False):
        list_actions = []
        if self._list_actions:
            list_actions.extend(self._list_actions)
        if add_default:
            list_actions.extend(self.model.get_metadata('list_actions', ()))
        return list_actions

    def list_per_page(self, list_per_page):
        self._list_per_page = list_per_page
        return self

    def get_list_per_page(self, add_default=False):
        if self._list_per_page is None and add_default:
            self._list_per_page = self.model.get_metadata('list_per_page')
        return self._list_per_page or 5

    def list_search(self, *search_fields):
        self._list_search = search_fields
        return self

    def get_list_search(self, add_default=False):
        if self._list_search is None and add_default:
            self._list_search = self.model.get_metadata('search_fields')
        return self._list_search

    def __str__(self):
        output = list()
        for obj in self[0:10]:
            output.append("'{}'".format(obj))
        if self.count() > 10:
            output.append(' ...')
        return '[{}]'.format(','.join(output))

    def _clone(self):
        clone = super()._clone()
        clone._user = self._user
        clone._slice = self._slice
        clone._list_display = self._list_display
        clone._list_filter = self._list_filter
        clone._list_subsets = self._list_subsets
        clone._list_actions = self._list_actions
        clone._list_per_page = self._list_per_page
        clone._list_search = self._list_search
        clone._page = self._page
        clone._subset = self._subset
        clone._q = self._q
        clone._filters = self._filters
        clone._actions = self._actions
        clone._subsets = self._subsets
        clone._display = self._display
        clone._related_manager = self._related_manager
        clone._related_attribute = self._related_attribute
        return clone

    def add(self, instance):
        related_manager = getattr(self, '_related_manager', None)
        if related_manager:  # one-to-many or many-to-many
            field = getattr(related_manager, 'field', None)
            if field:  # one-to-many
                if isinstance(instance, dict):  # dictionary instance
                    instance.update(**{field.name: self._hints['instance']})
                    return self.model.objects.get_or_create(**instance)[0]
                else:  # model instance
                    setattr(instance, field.name, self._hints['instance'])
                    instance.save()
                    return instance
            else:  # many-to-many
                if isinstance(instance, dict):  # dictionary instance
                    if instance.get('id'):
                        instance = self.model.objects.get(pk=instance.get('id'))
                    else:
                        instance = self.model.objects.get_or_create(**instance)[0]
                else:
                    if instance.pk is None:
                        instance.save()
                related_manager.add(instance)
                return instance
        else:
            return self.model.objects.get_or_create(**instance)[0]

    def remove(self, instance):
        if isinstance(instance, int):
            instance = {'id': instance}
        if isinstance(instance, dict):
            instance = self.model.objects.get(pk=instance.get('id'))
        related_manager = getattr(self, '_related_manager')
        field = getattr(related_manager, 'field', None)
        if field:  # one-to-many
            instance.delete()
        else:  # many-to-many
            related_manager.remove(instance)

    def list(self):
        return super().all()

    def count(self, x=None, y=None):
        return QuerySetStatistic(self, x, y=y) if x else super().count()

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def apply_list_lookups(self, user):
        lookup_keys = self.model.get_metadata('list_lookups', None)
        return self.apply_lookups(user, lookup_keys)

    def apply_add_lookups(self, user):
        lookup_keys = self.model.get_metadata('add_lookups', None)
        return self.apply_lookups(user, lookup_keys)

    def apply_edit_lookups(self, user):
        lookup_keys = self.model.get_metadata('edit_lookups', None)
        return self.apply_lookups(user, lookup_keys)

    def apply_delete_lookups(self, user):
        lookup_keys = self.model.get_metadata('delete_lookups', None)
        return self.apply_lookups(user, lookup_keys)

    def apply_lookups(self, user, lookups):
        self._user = user
        if user.pk is None:
            queryset = self.all()
        elif lookups is None:
            queryset = self.filter(pk__isnull=True)
        else:
            filters = []
            group_lookups = []
            for lookup_key in lookups:
                if lookup_key.startswith('self'):  # self or self__<attr>
                    if lookup_key == 'self':  # self
                        lookup_key = 'pk'
                    else:  # self__<attr>
                        lookup_key = lookup_key[6:]
                        field = self.model.get_field(lookup_key)
                    lookup = {lookup_key: user.pk}
                    filters.append(Q(**lookup))
                else:  # group
                    group_lookups.append(lookup_key)
            if group_lookups and user.groups.filter(lookup__in=group_lookups).exists():
                queryset = self.all()
            elif filters:
                queryset = self.filter(reduce(operator.__or__, filters)).distinct()
            else:
                queryset = self.all()
        return queryset

    def search(self, q):
        queryset = self.none()
        search_fields = self.model.get_metadata('search_fields')
        if not search_fields:
            local_fields = self.model.get_metadata('local_fields')
            search_fields = [field.name for field in local_fields if field.__class__.__name__ == 'CharField']
        for search_field in search_fields:
            queryset = queryset | self.filter(**{'{}__icontains'.format(search_field): q})
        return queryset

    @staticmethod
    def loads(payload):
        payload = json.loads(payload)
        model = apps.get_model(payload['model'])
        qs = model.objects.none()
        qs.query = cpickle.loads(zlib.decompress(base64.b64decode(signing.loads(payload['query']))))
        qs.list_display(*payload['list_display'])
        qs.list_filter(*payload['list_filter'])
        qs.list_subsets(*payload['list_subsets'])
        qs.list_actions(*payload['list_actions'])
        qs.list_per_page(payload['list_per_page'])
        qs.list_search(payload['list_search'])
        qs._q = payload['q']
        qs._filters = payload['filters']
        qs._actions = payload['actions']
        qs._subsets = payload['subsets']
        qs._subset = payload['subset']
        qs._display = payload['display']
        qs._page = payload['page'] - 1
        qs._deserialized = True

        return qs

    def serialize(self):
        data = []
        serialized_str = base64.b64encode(zlib.compress(cpickle.dumps(self.query))).decode()

        if not self._deserialized:
            for lookup in self._list_subsets:
                metadata = getattr(getattr(self, lookup), '_metadata', {})
                self._subsets.append(
                    {'name': lookup, 'label': metadata.get('verbose_name'), 'active': False}
                )
            for lookup in self._list_filter:
                self._filters.append(
                    {'name': lookup, 'label': self.model.get_verbose_name(lookup), 'value': None}
                )
            for lookup in self._list_actions:
                self._actions.append(
                    {'name': lookup, 'label': self.model.get_verbose_name(lookup), 'value': None}
                )
            for lookup in self.get_list_display():
                self._display.append(
                    {'name': lookup, 'label': self.model.get_verbose_name(lookup), 'sorted': False, 'formatter': None},
                )

        if self._subset:
            qs = getattr(self, self._subset)()
        else:
            qs = self.all()

        if qs._q:
            qs = qs.search(qs._q)

        for _filter in qs._filters:
            if _filter['value']:
                qs = qs.filter(**{_filter['name']: _filter['value']})

        for obj in qs[self._page * self._list_per_page:self._page * self._list_per_page + self._list_per_page]:
            item = []
            for lookup in self._list_display:
                value = getattrr(obj, lookup)
                if isinstance(value, Model):
                    value = str(value)
                item.append(value)
            data.append(item)

        payload = {
            'type': 'queryset',
            'metadata': not self._deserialized and {
                'model': getattr(self.model, '_meta').label.lower(),
                'query': signing.dumps(serialized_str),

                'list_display': self._list_display,
                'list_filter': self._list_filter,
                'list_subsets': self._list_subsets,
                'list_actions': self._list_actions,
                'list_per_page': self._list_per_page,
                'list_search': self._list_search,

                'q': None,
                'filters': self._filters,
                'actions': self._actions,
                'subsets': self._subsets,
                'subset': self._subset,
                'display': self._display,
                'page': self._page + 1,
            } or {},
            'data': data,
            'total': self.count()
        }
        return payload

    def dumps(self):
        return json.dumps(self.serialize())


class DefaultManager(QuerySet):
    pass


class Manager(manager.BaseManager.from_queryset(QuerySet)):

    def __init__(self, *args, **kwargs):
        self.queryset_class = kwargs.pop('queryset_class', QuerySet)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return self.queryset_class(self.model, using=self._db)

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})


class ModelBase(base.ModelBase):

    def __new__(mcs, name, bases, attrs):
        fromlist = list(map(str, attrs['__module__'].split('.')))
        module = __import__(attrs['__module__'], fromlist=fromlist)
        if hasattr(module, '{}Manager'.format(name)):
            queryset_class = getattr(module, '{}Manager'.format(name))
            if issubclass(queryset_class, DefaultManager):
                attrs.update(
                    objects=manager.BaseManager.from_queryset(queryset_class)()
                )

        if 'AbstractUser' in (cls.__name__ for cls in bases):
            username_field = None
            for attr_name in attrs:
                attr = attrs[attr_name]
                if getattr(attr, '_username', False):
                    username_field = attr_name
            if username_field:
                attrs.update(USERNAME_FIELD=username_field)
            setattr(settings, 'AUTH_USER_MODEL', '{}.{}'.format(fromlist[-2], name))

        cls = super().__new__(mcs, name, bases, attrs)

        return cls


class Model(six.with_metaclass(ModelBase, models.Model)):
    class Meta:
        abstract = True

    objects = Manager()

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        self._user = None

    def __getattribute__(self, item):
        value = super().__getattribute__(item)
        if hasattr(value, 'get_queryset'):
            queryset = value.get_queryset()
            queryset._related_manager = value
            queryset._related_attribute = item
            return queryset
        return value

    def save(self, *args, **kwargs):
        utils.pre_save(self)
        super().save(*args, **kwargs)
        utils.post_save(self)

    def delete(self, *args, **kwargs):
        utils.pre_delete(self)
        super().delete(*args, **kwargs)

    def satisfies(self, condition):
        satisfied = True
        if condition in ('can_add', 'can_edit', 'can_delete'):
            attr = getattr(self, condition, None)
            if attr:
                satisfied = attr()
        elif self.pk and condition:
            attr_name = condition.replace('not ', '')
            if hasattr(self, attr_name):  # model attribute or method
                attr = getattr(self, attr_name)
                if callable(attr):
                    satisfied = attr()
                else:
                    satisfied = bool(attr)
            else:  # manager subset method
                qs = type(self).objects.all()
                if hasattr(qs, attr_name):
                    attr = getattr(qs, attr_name)
                    satisfied = attr().filter(pk=self.pk).exists()
                else:
                    raise Exception(
                        'The condition "{}" is invalid for "{}" because'
                        'it is not an attribute or a method of {},'
                        ' neither a method of its manager'.format(condition, self, type(self)))
            if 'not ' in condition:
                satisfied = not satisfied
        return satisfied

    @classmethod
    def set_metadata(cls, name, value):
        setattr(getattr(cls, '_meta'), name, value)

    @classmethod
    def get_metadata(cls, name, default=None):
        metadata = getattr(cls, '_meta')
        if name in ('fieldsets', 'list_display') and not hasattr(metadata, name):
            field_names = [field.name for field in metadata.local_fields]
            if name == 'list_display':
                default = field_names
            else:
                default = dict(title='Dados Gerais', fields=field_names, relations=[], lookups=[], actions=[], tab_name=None, tab_title=None, image=None),
        elif name == 'exclude':
            default = [field.name for field in metadata.get_fields() if hasattr(field, 'exclude') and field.exclude]
        elif name == 'tabs':
            if hasattr(metadata, 'fieldsets'):
                default = [fieldset['tab_name'] for fieldset in metadata.fieldsets if fieldset['tab_name']]
        elif name in ('list_lookups', 'add_lookups', 'edit_lookups', 'delete_lookups'):
            default = getattr(metadata, 'lookups', None)
        return getattr(metadata, name, default)

    @classmethod
    def get_list_url(cls):
        return '/api/{}/{}/'.format(
            cls.get_metadata('app_label'),
            cls.get_metadata('model_name')
        )

    @classmethod
    def get_add_url(cls):
        return '/api/{}/{}/add/'.format(
            cls.get_metadata('app_label'),
            cls.get_metadata('model_name')
        )

    def get_view_url(self):
        return '{}{}/'.format(
            type(self).get_list_url(),
            self.pk
        )

    def get_edit_url(self):
        return '{}edit/'.format(self.get_view_url())

    def get_delete_url(self):
        return '{}delete/'.format(self.get_view_url())

    def value(self, lookup, serialized=False):
        value = getattrr(self, lookup)
        if serialized:
            value = utils.custom_serialize(value)
        if callable(value):
            value = value()
        return value

    def enable_nested_values(self):
        setattr(self, '_nestvalue', True)

    def disable_nested_values(self):
        delattr(self, '_nestvalue')

    def values(self, *lookups, verbose_key=False):
        if not lookups:
            lookups = list(self.get_metadata('list_display')) + ['id']
        return ValuesDict(self, *lookups, verbose_key=verbose_key)

    def serialize(self):
        return str(self)

    @classmethod
    def get_field(cls, lookup):
        field = None
        model = cls
        attrs = lookup.split('__')
        while attrs:
            attr_name = attrs.pop(0)
            if attrs:  # go deeper
                field = getattr(model, '_meta').get_field(attr_name)
                model = field.related_model
            else:
                field = getattr(model, '_meta').get_field(attr_name)
        return field

    def get_one_to_one_field_names(self):
        return (field.name for field in type(self).get_metadata('fields') if field.one_to_one)

    def get_many_to_many_field_names(self):
        return (field.name for field in type(self).get_metadata('many_to_many'))

    def get_one_to_many_field_names(self):
        return (field.name for field in type(self).get_metadata('get_fields')() if type(field).__name__ == 'OneToManyField')

    def get_one_to_many_relation_names(self):
        return (rel.get_accessor_name() for rel in type(self).get_metadata('related_objects'))

    @classmethod
    def get_verbose_name(cls, lookup):
        model = cls
        attrs = lookup.split('__')
        while attrs:
            attr_name = attrs.pop(0)
            if attrs:  # go deeper
                field = getattr(model, '_meta').get_field(attr_name)
                model = field.related_model
            else:  # last
                try:  # field
                    field = getattr(model, '_meta').get_field(attr_name)
                    if hasattr(field, 'verbose_name'):
                        return field.verbose_name
                    else:
                        return getattr(field.related_model, '_meta').verbose_name
                except FieldDoesNotExist:  # mehod
                    attr = getattr(model, attr_name)
                    return getattr(attr, '_metadata', {}).get('verbose_name')

    @classmethod
    def get_attr_metadata(cls, attr_name):
        if not hasattr(cls, '_attr_metadata'):
            chache = {}
            for _cls in (cls, getattr(cls.objects, '_queryset_class')):
                for name in dir(_cls):
                    if name and not name.startswith('_'):
                        attr = getattr(_cls, name)
                        if hasattr(attr, '_metadata'):
                            metadata = getattr(attr, '_metadata')
                            if metadata['type'] == 'action':
                                if metadata['scope'] != 'class':
                                    if cls is _cls:
                                        metadata['scope'] = 'instance'
                                    else:
                                        metadata['scope'] = 'manager'
                            chache[name] = metadata
            setattr(cls, '_attr_metadata', chache)
        return getattr(cls, '_attr_metadata').get(attr_name)

    @classmethod
    def check_lookups(cls, user, lookups, groups_only=True):
        group_lookups = {}
        if lookups:
            if user.pk:
                for lookup_key in lookups or ():
                    if lookup_key.startswith('self'):  # self or self__<attr>
                        if lookup_key == 'self':
                            group_lookup = user.get_metadata('model_name')
                        else:  # group
                            field = cls.get_field(lookup_key[6:])
                            group_lookup = field.related_model.get_metadata('model_name')
                    else:
                        group_lookup = lookup_key
                    group_lookups[group_lookup] = lookup_key

                    qs = user.groups.filter(lookup__in=group_lookups.keys())
                    checked_lookups = qs.values_list('lookup', flat=True)
                    return checked_lookups if groups_only else {
                        group_lookup: group_lookups[group_lookup] for group_lookup in checked_lookups
                    }
            else:
                return False if groups_only else group_lookups

        return True if groups_only else group_lookups


class Group(Model):
    name = models.CharField(verbose_name='Name', max_length=255)
    lookup = models.CharField(verbose_name='Chave', max_length=255)

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'
        list_display = 'name',

    def get_users(self):
        from django.conf import settings
        user_model_name = settings.AUTH_USER_MODEL.split('.')[1].lower()
        return getattr(self, '{}_set'.format(user_model_name)).all()

    def __str__(self):
        return self.name


class AbstractUser(six.with_metaclass(ModelBase, base_user.AbstractBaseUser, Model)):

    password = models.CharField(verbose_name='Senha', null=True, blank=True, default='!', max_length=255)
    last_login = models.DateTimeField(verbose_name='Último Login', null=True, blank=True)
    groups = models.ManyToManyField(Group, verbose_name='Grupos', blank=True)

    class Meta:
        abstract = True

    def change_password(self, raw_password):
        super().set_password(raw_password)
        super().save()

    def send_access_email(self, email):
        from dp.admin.utils.mail import send_mail
        subject = 'Acesso ao Sistema'
        message = 'Clique no botão abaixo para (re)definir sua senha de acesso'
        token = signing.dumps(dict(username=self.get_username(), pk=self.pk))
        token = codecs.encode(token.encode(), 'hex').decode()
        actions = [('(Re)definir Senha', '/admin/login/?reset={}'.format(token))]
        send_mail(subject, message, email, actions=actions)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        token_model = apps.get_model('authtoken', 'Token')
        token_model.objects.get_or_create(user=self)

