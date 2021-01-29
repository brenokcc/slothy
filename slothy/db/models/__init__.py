# -*- coding: utf-8 -*-

import six
import json
from django.db.models import query, base, manager, Sum, Count, Avg
from django.db.models.fields import *
from django.db.models.fields.related import *
from django.core.exceptions import FieldDoesNotExist
from slothy import decorators
from slothy.db.utils import getattrr
from slothy.db import utils
import zlib
import base64
import _pickle as cpickle
from django.core import signing
from django.db.models import Q
import operator
from collections import UserDict
from functools import reduce
from django.core import exceptions
from django.conf import settings
from slothy.db.models.fields import *

ValidationError = exceptions.ValidationError


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
            self._xdict = {i + 1: month for i, month in enumerate(QuerySetStatistic.MONTHS)}
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


class ValueSet(UserDict):

    def __init__(self, obj, *lookups, verbose=True, detail=False):
        self.obj = obj
        self.thumbnail = None
        self.actions = []
        self.nested_keys = []
        self.nested = False
        super().__init__()
        _values = []
        for lookup in lookups:
            keys = []
            if not isinstance(lookup, tuple):
                lookup = lookup,
            for attr_name in lookup:
                if verbose:
                    verbose_name = obj.get_verbose_name(attr_name)
                else:
                    verbose_name = attr_name

                value = getattrr(obj, attr_name)
                if callable(value):
                    value = value()
                if isinstance(value, ValueSet):
                    self.nested = True
                if isinstance(value, QuerySet):
                    if hasattr(value, '_related_manager'):
                        caller = dict(
                            id=obj.id,
                            attr_name=attr_name,
                            app_label=type(obj).get_metadata('app_label'),
                            model_name=type(obj).get_metadata('model_name')
                        )
                        setattr(value, '_caller', caller)
                self[verbose_name] = value
                keys.append(verbose_name)
            self.nested_keys.append(keys)

    def thumbnail(self, lookup):
        self.thumbnail = getattr(self.obj, lookup)
        return self

    def allow(self, *lookups):
        for lookup in lookups:
            self.actions.append(
                {'name': lookup, 'label': self.obj.get_verbose_name(lookup)}
            )
        return self

    def get_nested_values(self):
        _values = []
        for key_list in self.nested_keys:
            values = []
            for key in key_list:
                value = self[key]
                value = utils.serialize(value, False)
                values.append({key: value})
            _values.append(values)
        return _values

    def serialize(self):
        serialized = []
        for name, value in self.items():
            value = utils.serialize(value, True)
            serialized.append(dict(type='fieldset', name=name, data=value))
        return serialized


class QuerySet(query.QuerySet):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = None
        self._slice = None
        self._list_display = ()
        self._list_filter = ()
        self._list_subsets = ()
        self._list_actions = ()
        self._list_search = ()
        self._list_sort = ()
        self._page = 0
        self._page_size = 10
        self._subset = None
        self._q = None
        self._sorter = None
        self._filters = []
        self._actions = []
        self._subsets = []
        self._display = []
        self._search = []
        self._sort = []
        self._count_subsets = False
        self._related_manager = None
        self._related_attribute = None
        self._iterable_class = ModelIterable
        self._lookups = ()
        self._caller = None

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

    def display(self, *list_display):
        self._list_display = ['id']
        for lookup in list_display:
            self._list_display.append(lookup)
        return self

    def filter_by(self, *list_filter):
        self._list_filter = list_filter
        return self

    def get_list_filter(self, add_default=False):
        if self._list_filter is None and add_default:
            self._list_filter = self.model.get_metadata('list_filter')
        return self._list_filter

    def subsets(self, *list_subsets):
        self._list_subsets = list_subsets
        return self

    def get_list_subsets(self, add_default=False):
        if self._list_subsets is None and add_default:
            self._list_subsets = self.model.get_metadata('list_subsets')
        return self._list_subsets

    def allow(self, *list_actions):
        self._list_actions = list_actions
        return self

    def get_list_actions(self, add_default=False):
        list_actions = []
        if self._list_actions:
            list_actions.extend(self._list_actions)
        if add_default:
            list_actions.extend(self.model.get_metadata('list_actions', ()))
        return list_actions

    def paginate(self, page_size):
        self._page_size = page_size
        return self

    def get_page_size(self):
        return self._page_size

    def search_by(self, *search_fields):
        self._list_search = search_fields
        return self

    def get_list_search(self):
        return self._list_search

    def sort_by(self, *sort_fields):
        self._list_sort = sort_fields
        return self

    def get_sort_by(self):
        return self._list_sort

    def __str__(self):
        output = list()
        for obj in self[0:self._page_size]:
            output.append("'{}'".format(obj))
        if self.count() > self._page_size:
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
        clone._lookups = self._lookups
        clone._page_size = self._page_size
        clone._list_search = self._list_search
        clone._list_sort = self._list_sort
        clone._page = self._page
        clone._subset = self._subset
        clone._q = self._q
        clone._sorter = self._sorter
        clone._filters = self._filters
        clone._actions = self._actions
        clone._subsets = self._subsets
        clone._display = self._display
        clone._sort = self._sort
        clone._search = self._search
        clone._related_manager = self._related_manager
        clone._related_attribute = self._related_attribute
        clone._caller = self._caller
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

    def set(self, instances):
        related_manager = getattr(self, '_related_manager', None)
        if related_manager:
            for instance in instances:
                related_manager.add(instance)

    def count(self, x=None, y=None):
        return QuerySetStatistic(self, x, y=y) if x else super().count()

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def lookups(self, *lookups):
        self._lookups = lookups
        return self

    def apply_lookups(self, user):
        self._user = user
        if user.pk is None:
            queryset = self.all()
        elif self._lookups is ():
            queryset = self.all()
        else:
            filters = []
            group_lookups = []
            for lookup_key in self._lookups:
                if lookup_key.startswith('self'):  # self or self__<attr>
                    if lookup_key == 'self':  # self
                        lookup_key = 'pk'
                    else:  # self__<attr>
                        lookup_key = lookup_key[6:]
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

    def dump_query(self):
        return signing.dumps(base64.b64encode(zlib.compress(cpickle.dumps(self.query))).decode())

    def load_query(self, s):
        self.query = cpickle.loads(zlib.decompress(base64.b64decode(signing.loads(s))))
        return self

    def load(self, metadata):
        self._q = metadata['q']
        self._sorter = metadata['sorter']
        self._subset = metadata['subset']
        self._caller = metadata['caller']
        self._page = metadata['page']['number'] - 1
        self._page_size = metadata['page']['size']
        for name, value in metadata['filters'].items():
            self._filters.append(dict(name=name, value=value))
        self._list_display = metadata['display']
        self._list_actions = metadata['actions']
        if 'subsets' in metadata:
            self._count_subsets = metadata['subsets']
        return self

    def serialize(self, name=''):
        data = []
        s = self.dump_query()

        for lookup in self._list_subsets:
            attr = getattr(self, lookup)
            metadata = getattr(attr, '_metadata', {})
            qss = attr()
            self._subsets.append(
                {'name': lookup, 'label': metadata.get('verbose_name'),
                 'count': qss.count(), 'query': qss.dump_query(), 'active': False}
            )
        for lookup in self._list_filter:
            choices = []
            field = self.model.get_field(lookup)
            if hasattr(field, 'related_model') and field.related_model:
                qs = field.related_model.objects.filter(
                    pk__in=self.values_list(lookup).distinct()
                ).display(*('__str__',))
                choices = qs.serialize(self.model.get_verbose_name(lookup))
            elif hasattr(field, 'choices') and field.choices:
                choices = field.choices
            elif isinstance(field, BooleanField):
                choices = [[True, 'Sim'], [False, 'Não']]
            self._filters.append(
                {'name': lookup, 'label': self.model.get_verbose_name(lookup),
                 'value': None, 'display': None, 'choices': choices}
            )
        for lookup in self._list_sort:
            self._sort.append(
                {'name': lookup, 'label': self.model.get_verbose_name(lookup),
                 'value': None, 'display': None}
            )
        for lookup in self._list_search:
            self._search.append(
                {'name': lookup, 'label': self.model.get_verbose_name(lookup)}
            )
        for lookup in self._list_actions:
            action_params = True
            if self._caller:
                action_url = '/api/{}/{}/{}/{}/{}'.format(
                    self._caller['app_label'], self._caller['model_name'],
                    self._caller['id'], self._caller['attr_name'], lookup
                )
                if lookup == 'add':
                    action_icon = None
                    action_type = 'subset'
                    action_params = True
                    action_label = 'Adicionar'
                else:
                    action_icon = None
                    action_type = 'instance'
                    action_params = False
                    action_label = 'Remover'
                    action_url = '{}/{{id}}'.format(action_url)
            else:
                action_url = '/api/{}/{}'.format(
                    self.model.get_metadata('app_label'),
                    self.model.get_metadata('model_name')
                )
                if hasattr(self.model, lookup):
                    action_type = 'instance'
                    action_func = getattr(self.model, lookup)
                else:
                    action_type = 'subset'
                    action_func = getattr(getattr(self.model.objects, '_queryset_class'), lookup)

                action_metadata = getattr(action_func, '_metadata')
                action_icon = action_metadata['icon']
                if action_metadata['name'] == 'add':
                    action_type = 'subset'
                if action_type == 'instance':
                    action_url = '{}/{{id}}'.format(action_url)
                action_url = '{}/{}'.format(action_url, action_metadata['name'])
                action_label = self.model.get_verbose_name(lookup)
                if action_metadata['name'] not in ('add', 'edit') and not action_metadata['params']:
                    action_params = False
            self._actions.append(
                {'name': lookup, 'label': action_label, 'type': action_type,
                 'icon': action_icon, 'url': action_url, 'params': action_params}
            )
        for lookup in self._list_display or ('id', '__str__'):
            self._display.append(
                {'name': lookup, 'label': self.model.get_verbose_name(lookup), 'sorted': False, 'formatter': None},
            )

        if self._subset:
            qs = getattr(self, self._subset)()
        else:
            qs = self

        if self._q:
            qs = qs.search(self._q)

        if self._sorter:
            qs = qs.order_by(self._sorter)

        for _filter in self._filters:
            if _filter['value'] is not None:
                qs = qs.filter(**{_filter['name']: _filter['value']})

        for obj in qs[self._page * self._page_size:self._page * self._page_size + self._page_size]:
            item = []
            for display in self._display:
                value = getattrr(obj, display['name'])
                if callable(value):
                    value = value()
                item.append(utils.serialize(value, detail=False))
            actions = []
            for action in self._actions:
                if action['type'] == 'instance':
                    actions.append(action['name'])
            item.append(actions)
            data.append(item)

        if self._count_subsets:
            serialized = dict(data=data, total=self.count())
            totals = dict()
            clone = self._clone()
            for subset_name, subset_query in self._count_subsets.items():
                clone.load_query(subset_query)
                totals[subset_name] = clone.count()
            serialized.update(totals=totals)
        else:
            serialized = dict()
            serialized['type'] = 'queryset'
            serialized['name'] = name
            serialized['path'] = '/queryset/{}/{}/'.format(
                getattr(self.model, '_meta').app_label.lower(),
                self.model.__name__.lower()
            )
            serialized['input'] = dict()
            serialized['input']['query'] = s
            serialized['input']['q'] = ''
            serialized['input']['sorter'] = None
            serialized['input']['subset'] = self._subset
            serialized['input']['caller'] = self._caller
            serialized['input']['page'] = {
                'number': self._page + 1,
                'size': self._page_size
            }
            serialized['input']['display'] = [display['name'] for display in self._display]
            serialized['input']['actions'] = [action['name'] for action in self._actions]
            serialized['input']['filters'] = dict()
            for _filter in self._filters:
                serialized['input']['filters'][_filter['name']] = _filter['value']

            serialized['metadata'] = {
                'search': self._search,
                'filters': self._filters,
                'actions': self._actions,
                'subsets': self._subsets,
                'display': self._display,
                'sort': self._sort,
            }
            serialized['data'] = data
            serialized['total'] = self.count()

        return serialized

    def dumps(self):
        return json.dumps(self.serialize())


class DefaultManager(QuerySet):
    pass


class Manager(manager.BaseManager.from_queryset(QuerySet)):

    def __init__(self, *args, **kwargs):
        self.queryset_class = kwargs.pop('queryset_class', QuerySet)
        super().__init__(*args, **kwargs)

    def all(self):
        return self.get_queryset().all()

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
                class LocalManager(manager.BaseManager.from_queryset(queryset_class)):
                    def __init__(self, *args, **kwargs):
                        self.queryset_class = queryset_class
                        super().__init__(*args, **kwargs)

                    def all(self):
                        return self.get_queryset().all()

                    def get_queryset(self):
                        return self.queryset_class(self.model, using=self._db)

                    def get_by_natural_key(self, username):
                        return self.get(**{self.model.USERNAME_FIELD: username})

                attrs.update(
                    objects=LocalManager()
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

    def serialize(self, *lookups):
        fieldsets = []
        displays = []
        default_display = None
        data = dict(fieldset=[], tab=[], shortcut=[], card=[], top=[], left=[], center=[], right=[], bottom=[])
        for attr_name in dir(self):
            if attr_name.startswith('get'):
                attr = getattr(self, attr_name)
                if hasattr(attr, '__page'):
                    item = getattr(attr, '__page')
                    if item['key'] == 'tab':
                        if not displays:
                            default_display = item['verbose_name']
                        displays.append(item)
                    else:
                        fieldsets.append(item)
                    data[item['key']].append(item)

        fieldsets = sorted(fieldsets, key=lambda item: item['order'])

        current_display_name = getattr(self, '_current_display_name', None)
        if current_display_name is None:
            current_display_name = default_display

        dimensions = {}
        for item in displays:
            if item['verbose_name'] == current_display_name:
                dimensions[item['verbose_name']] = getattr(self, item['name'])().serialize()
            else:
                dimensions[item['verbose_name']] = []

        if not fieldsets:
            fieldsets.append(dict(name='default_viewset'))
        fieldset_names = []
        for item in fieldsets:
            fieldset_names.append(item['name'])
        serialized = dict(
            type='object',
            name=str(self),
            input=dict(dimension=current_display_name),
            data=self.values(*fieldset_names, verbose=True, detail=True).serialize(),
            dimensions=dimensions
        )
        return serialized

    def values(self, *lookups, verbose=True, detail=False):
        return ValueSet(self, *lookups, verbose=verbose, detail=detail)

    def view(self, *lookups):
        return self.serialize(*lookups)

    def add(self):
        self.save()

    def edit(self):
        self.save()

    @decorators.attr('Dados Gerais')
    def default_viewset(self):
        lookups = self.get_metadata('list_display')
        return self.values(*lookups)

    @classmethod
    def get_metadata(cls, name, default=None):
        metadata = getattr(cls, '_meta')
        if name == 'list_display' and not hasattr(metadata, name):
            default = [field.name for field in metadata.local_fields]
        return getattr(metadata, name, default)

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

    @classmethod
    def get_verbose_name(cls, lookup):
        model = cls
        if lookup == '__str__':
            return getattr(model, '_meta').verbose_name
        attrs = lookup.split('__')
        while attrs:
            attr_name = attrs.pop(0)
            if attrs:  # go deeper
                field = getattr(model, '_meta').get_field(attr_name)
                model = field.related_model
            else:  # last
                if hasattr(model, attr_name):
                    attr = getattr(model, attr_name)
                    if hasattr(attr, '_meta'):  # method
                        return getattr(attr, '_meta').verbose_name
                    else:
                        try:
                            field = getattr(model, '_meta').get_field(attr_name)
                            if hasattr(field, 'verbose_name'):
                                return field.verbose_name
                            else:
                                return getattr(field.related_model, '_meta').verbose_name
                        except FieldDoesNotExist:  # mehod
                            attr = getattr(model, attr_name)
                            return getattr(attr, '_metadata', {}).get('verbose_name')
                else:
                    attr = getattr(getattr(model.objects, '_queryset_class'), attr_name)
                    return getattr(attr, '_metadata', {}).get('verbose_name')

    def check_lookups(self, attr_name, user):
        self._user = user
        attr = getattr(self, attr_name)
        metadata = getattr(attr, '_metadata')
        lookups = metadata['lookups']

        if user.pk is None:
            return True
        elif not lookups:
            return True
        else:
            filters = []
            group_lookups = []
            for lookup_key in lookups:
                if lookup_key.startswith('self'):  # self or self__<attr>
                    if lookup_key == 'self':  # self
                        lookup_key = 'pk'
                    else:  # self__<attr>
                        lookup_key = lookup_key[6:]
                    lookup = {lookup_key: user.pk}
                    filters.append(Q(**lookup))
                else:  # group
                    group_lookups.append(lookup_key)
            if group_lookups and user.groups.filter(lookup__in=group_lookups).exists():
                return True
            if filters and type(self).objects.filter(reduce(operator.__or__, filters)).exists():
                return True
        return False