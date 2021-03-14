# -*- coding: utf-8 -*-
import datetime
import six
import json
from django.db.models import query, base, manager, Sum, Count, Avg
from django.db.models.fields import *
from django.db.models.fields.related import *
from django.core.exceptions import FieldDoesNotExist
from slothy.db.utils import getattrr
from slothy.db import utils
import zlib
import base64
import _pickle as cpickle
from django.core import signing
from django.db.models import Q
import operator
from functools import reduce
from django.core import exceptions
from django.conf import settings
from slothy.db import attr
from slothy.db.models.fields import *
from django.db.models.functions import TruncDay
ValidationError = exceptions.ValidationError


AUTH_USER_MODEL = None


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

    def __init__(self, qs, x, y=None, func=None, z='id'):
        self.qs = qs
        self.x = x
        self.y = y
        self.func = func or Count
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
        if hasattr(self._yfield, 'choices') and self._yfield.choices:
            for choice in self._yfield.choices:
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
            xvalues = self.qs.values_list(self.x, flat=True).order_by(self.x).distinct()
            if self._xfield.related_model:
                self._xdict = {
                    obj.pk: str(obj) for obj in self._xfield.related_model.objects.filter(pk__in=xvalues)
                }
            else:
                self._xdict = {
                    value: value for value in self.qs.values_list(self.x, flat=True)
                }
            if None in xvalues:
                self._xdict[None] = 'Não-Informado'
        if self.y:
            self._yfield = self.qs.model.get_field(self.y.replace('__year', '').replace('__month', ''))
            yvalues = self.qs.values_list(self.y, flat=True).order_by(self.y).distinct()
            if self._ydict == {}:
                if self._yfield.related_model:
                    self._ydict = {
                        obj.pk: str(obj) for obj in self._yfield.related_model.objects.filter(pk__in=yvalues)
                    }
                else:
                    self._ydict = {
                        value: value for value in yvalues
                    }
            self._values_dict = {(vx, vy): calc for vx, vy, calc in values_list}
            if None in yvalues:
                self._ydict[None] = 'Não-Informado'
        else:
            self._ydict = {}
            self._values_dict = {(vx, None): calc for vx, calc in values_list}

    def filter(self, **kwargs):
        self._clear()
        self.qs = self.qs.filter(**kwargs)
        return self

    def apply_lookups(self, user, lookups):
        self._clear()
        self.qs = self.qs.apply_lookups(user, lookups)
        return self

    def serialize(self, name=None):
        self._calc()
        series = dict()
        formatter = {True: 'Sim', False: 'Não', None: 'Não-Informado'}
        if not self._ydict:
            self._ydict[None] = 'Não-Informado'
        for i, (yk, yv) in enumerate(self._ydict.items()):
            data = []
            for j, (xk, xv) in enumerate(self._xdict.items()):
                color = i if len(self._ydict.items()) > 1 else j
                data.append([formatter.get(xv, str(xv)), self._values_dict.get((xk, yk), 0), settings.THEME['COLORS'][color]])
            series.update(**{formatter.get(yv, str(yv)): data})

        return dict(
            type='statistic',
            name=name,
            series=series
        )


class ValueSet(dict):

    def __init__(self, obj, *lookups, verbose=True, detail=False):
        self.obj = obj
        self.thumbnail = None
        self.action_list = []
        self.nested_keys = []
        self.nested = False
        self.verbose_names = {}

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
                self[attr_name] = value
                self.verbose_names[attr_name] = verbose_name
                keys.append((attr_name, verbose_name, None))
            self.nested_keys.append(keys)

    def thumbnail(self, lookup):
        self.thumbnail = getattr(self.obj, lookup)
        return self

    def actions(self, *lookups):
        model = type(self.obj)
        for lookup in lookups:
            action_func = getattr(model, lookup)
            action_metadata = getattr(action_func, '_metadata')
            action_verbose_name = action_metadata['verbose_name']
            action_icon = action_metadata['icon']
            action_params = bool(action_metadata['params'])
            action_url = '/api/{}/{}/{}/{}'.format(
                model.get_metadata('app_label'),
                model.get_metadata('model_name'),
                self.obj.pk, lookup
            )
            self.action_list.append(
                {'name': lookup, 'label': action_verbose_name, 'icon': action_icon, 'params': action_params, 'url': action_url}
            )
        return self

    def get_nested_values(self):
        _values = []
        for key_list in self.nested_keys:
            values = []
            for attr_name, verbose_name, formatter in key_list:
                value = self[attr_name]
                value = utils.serialize(value, False)
                values.append(dict(name=attr_name, label=verbose_name, value=value, formatter=formatter))
            _values.append(values)
        return _values

    def serialize(self):
        serialized = []
        for name, value in self.items():
            value = utils.serialize(value, True)
            serialized.append(dict(type='fieldset', name=name, label=self.verbose_names[name], data=value))
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
        self._hidden_filters = []
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
        self._applied = False

    # def _fetch_all(self):
    #     print(999)
    #     if not self._applied and self._user:
    #         qs = self.apply_lookups()
    #     return super()._fetch_all()

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

    def filters(self, *list_filter):
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

    def actions(self, *list_actions):
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

    def search(self, *search_fields, q=None):
        if search_fields:
            self._list_search = search_fields
        if q is None:
            return self
        else:
            search_fields = self._list_search
            queryset = self.none()
            if not search_fields:
                local_fields = self.model.get_metadata('local_fields')
                search_fields = [field.name for field in local_fields if field.__class__.__name__ == 'CharField']
            for search_field in search_fields:
                queryset = queryset | self.filter(**{'{}__icontains'.format(search_field): q})
            return queryset


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
        clone._hidden_filters = self._hidden_filters
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

    def sum(self, x, y=None, z=None):
        if y:
            return QuerySetStatistic(self, x, y=y, func=Sum, z=z)
        else:
            return QuerySetStatistic(self, x, func=Sum, z=z)

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD: username})

    def get_calendar_field(self):
        return [field for field in self.model.get_metadata('fields') if type(field).__name__ in ('DateField', 'DateTimeField')][0]

    def count_by_date(self, year, month):
        filters = dict()
        data = dict()
        field = self.get_calendar_field()
        first_day_of_month = datetime.date(year, month, 1)
        filters['{}__gte'.format(field.name)] = first_day_of_month
        while first_day_of_month.month == month:
            first_day_of_month += datetime.timedelta(1)
        filters['{}__lt'.format(field.name)] = first_day_of_month
        for item in self.filter(**filters).annotate(day=TruncDay(field.name)).values('day').annotate(value=Count('id')):
            data[item['day'].strftime('%d/%m/%Y')] = item['value']
        return dict(verbose_name=field.verbose_name, data=data)

    def filter_by_date(self, year, month, day):
        filters = dict()
        start = datetime.date(year, month, day)
        end = start + datetime.timedelta(1)
        field = self.get_calendar_field()
        filters['{}__gte'.format(field.name)] = start
        filters['{}__lt'.format(field.name)] = end
        for name, value in filters.items():
            self._hidden_filters.append(dict(name=name, value=value))
        return self.filter(**filters)

    def lookups(self, *lookups):
        self._lookups = lookups
        return self

    def apply_lookups(self, user, lookups=None):
        self._user = user
        if lookups is None:
            lookups = self._lookups

        if user is None:
            return self
        if user.pk is None:
            return self
        elif user.is_superuser:
            return self
        elif lookups == ():
            return self
        else:
            filters = []
            model_filters = {}
            for lookup_key in lookups:
                if lookup_key.startswith('self'):  # self or self__<attr>
                    if lookup_key == 'self':  # self
                        lookup_key = 'pk'
                    else:  # self__<attr>
                        lookup_key = lookup_key[6:]
                    if lookup_key.endswith('__isnull'):
                        filters.append(Q(**{lookup_key: True}))
                    else:
                        filters.append(Q(**{lookup_key: user.pk}))
                else:
                    app_label = self.model.get_metadata('app_label')
                    tokens = lookup_key.split('__')
                    model = apps.get_model(app_label, tokens[0])
                    lookup_key = len(tokens) > 1 and '__'.join(tokens[1:]) or 'pk'
                    if model not in model_filters:
                        model_filters[model] = []
                    model_filters[model].append(Q(**{lookup_key: user.pk}))
            for model in model_filters:
                if model.objects.filter(reduce(operator.__or__, model_filters[model])).exists():
                    return self
            if filters:
                return self.filter(reduce(operator.__or__, filters))
        return self.none()

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
        for name, value in metadata['hidden_filters'].items():
            self._hidden_filters.append(dict(name=name, value=value))
        self._list_display = metadata['display']
        self._list_actions = metadata['actions']
        self._list_search = metadata['search']
        if 'subsets' in metadata:
            self._count_subsets = metadata['subsets']
        return self

    def serialize(self, name='', icon=None):
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
            action_condition = None
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
                action_condition = action_metadata['condition']
                if action_metadata['name'] == 'add':
                    action_type = 'subset'
                if action_type == 'instance':
                    action_url = '{}/{{id}}'.format(action_url)
                action_url = '{}/{}'.format(action_url, action_metadata['name'])
                action_label = self.model.get_verbose_name(lookup)
                if action_metadata['name'] not in ('add', 'edit') and not action_metadata['params']:
                    action_params = False

            self._actions.append(
                {
                    'name': lookup, 'label': action_label, 'type': action_type,
                    'icon': action_icon, 'url': action_url, 'params': action_params,
                    'condition': action_condition
                }
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
            qs = qs.search(q=self._q)

        if self._sorter:
            qs = qs.order_by(self._sorter)

        for filter_type in (self._filters, self._hidden_filters):
            for _filter in filter_type:
                if _filter['value'] is not None:
                    qs = qs.filter(**{_filter['name']: _filter['value']})

        for obj in qs[self._page * self._page_size:self._page * self._page_size + self._page_size]:
            item = []
            for display in self._display:
                value = getattrr(obj, display['name'])
                if callable(value):
                    value = value()
                if isinstance(value, ValueSet):
                    item.append(utils.serialize(value, detail=True))
                else:
                    item.append(utils.serialize(value, detail=False))
            actions = []
            for action in self._actions:
                if action['type'] == 'instance':
                    if obj.check_method_condition(action['name']):
                        if obj.check_condition(action['condition']):
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
            serialized['icon'] = icon or self.model.get_metadata('icon')
            serialized['path'] = '/queryset/{}/{}'.format(
                getattr(self.model, '_meta').app_label.lower(),
                self.model.__name__.lower()
            )
            serialized['input'] = dict()
            serialized['input']['query'] = s
            serialized['input']['q'] = ''
            serialized['input']['sorter'] = None
            serialized['input']['subset'] = self._subset
            serialized['input']['caller'] = self._caller
            serialized['input']['search'] = self._list_search
            serialized['input']['page'] = {
                'number': self._page + 1,
                'size': self._page_size
            }
            serialized['input']['display'] = [display['name'] for display in self._display]
            serialized['input']['actions'] = [action['name'] for action in self._actions]
            serialized['input']['filters'] = dict()
            for _filter in self._filters:
                serialized['input']['filters'][_filter['name']] = _filter['value']
            serialized['input']['hidden_filters'] = dict()
            for _filter in self._hidden_filters:
                serialized['input']['hidden_filters'][_filter['name']] = _filter['value']

            serialized['metadata'] = {
                'search': self._search,
                'filters': self._filters,
                'hidden_filters': self._hidden_filters,
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


class Set(QuerySet):
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
        global AUTH_USER_MODEL
        fromlist = list(map(str, attrs['__module__'].split('.')))
        module = __import__(attrs['__module__'], fromlist=fromlist)
        if hasattr(module, '{}Set'.format(name)):
            queryset_class = getattr(module, '{}Set'.format(name))
            if issubclass(queryset_class, Set):
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
            queryset._caller = dict(
                app_label=self.get_metadata('app_label'),
                model_name=self.get_metadata('model_name'),
                id=self.id,
                attr_name=item,
            )
            return queryset
        return value

    def serialize(self, *lookups):
        fieldsets = []
        tabs = []
        tab = getattr(self, '_current_display_name', None)
        for attr_name in lookups:
            attr = getattr(self, attr_name)
            metadata = getattr(attr, '_metadata')
            if metadata['type'] == 'attrs':
                if tab is None:
                    tab = metadata['name']
                if attr_name == tab:
                    tab_data = attr().serialize()
                else:
                    tab_data = []
                url = '/api/{}/{}/{}/{}'.format(
                    self.get_metadata('app_label'),
                    self.get_metadata('model_name'),
                    self.pk, attr_name
                )
                tabs.append(dict(type='tab', name=attr_name, label=metadata['verbose_name'], path=url, data=tab_data))
            elif metadata['type'] == 'attr':
                fieldsets.append(attr_name)

        data = self.values(*fieldsets, verbose=True, detail=True).serialize()
        if tabs:
            data.append(dict(type='tabs', data=tabs))
        serialized = dict(
            type='object',
            name=str(self),
            icon=self.get_metadata('icon'),
            data=data
        )
        return serialized

    def values(self, *lookups, verbose=True, detail=False):
        return ValueSet(self, *lookups, verbose=verbose, detail=detail)

    def view(self, *fieldsets):
        return self.serialize(*fieldsets)

    def add(self):
        self.save()

    def edit(self):
        self.save()

    @attr('Dados Gerais')
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
        if hasattr(self, attr_name):
            attr = getattr(self, attr_name)
        else:
            attr = getattr(getattr(type(self).objects, '_queryset_class'), attr_name)
        metadata = getattr(attr, '_metadata')
        lookups = metadata['lookups']
        if user is None:
            return True
        if user.pk is None:
            return True
        elif user.is_superuser:
            return True
        elif lookups == ():
            return False
        elif lookups is None:
            return True
        else:
            filters = {}
            for lookup_key in lookups:
                if lookup_key.startswith('self'):
                    model = type(self)
                    if lookup_key == 'self':
                        lookup_key = 'pk'
                    else:
                        lookup_key = lookup_key[6:]
                else:  # group
                    app_label = self.get_metadata('app_label')
                    tokens = lookup_key.split('__')
                    model = apps.get_model(app_label, tokens[0])
                    lookup_key = len(tokens) > 1 and '__'.join(tokens[1:]) or 'pk'
                if model not in filters:
                    filters[model] = []
                filters[model].append(Q(**{lookup_key: user.pk}))
            for model in filters:
                if model.objects.filter(reduce(operator.__or__, filters[model])).exists():
                    return True
        return False

    def check_method_condition(self, method_name):
        attrname = 'can_{}'.format(method_name)
        if hasattr(self, attrname):
            return getattr(self, attrname)()
        return True

    def check_condition(self, condition):
        satisfied = True
        if self.pk and condition:
            model = type(self)
            attr_name = condition.replace('not ', '')
            # the method is defined in the model
            if hasattr(self, attr_name):
                attr = getattr(self, attr_name)
                if callable(attr):
                    satisfied = attr()
                else:
                    satisfied = bool(attr)
            else:
                # the method is defined in the manager as a subset
                qs = model.objects.all()
                if hasattr(qs, attr_name):
                    attr = getattr(qs, attr_name)
                    satisfied = attr().filter(pk=self.pk).exists()
                else:
                    raise Exception(
                        'The condition "{}" is invalid for {} because it is not an attribute or a method of {},'
                        ' neither a method of its manager'.format(condition, self, model))
            if 'not ' in condition:
                satisfied = not satisfied
        return satisfied
