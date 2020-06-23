import datetime
import collections
from django.apps import apps
from django.conf import settings
from django.db.models import signals
from django.core.exceptions import ValidationError

FOREIGNKEY_GROUP_FIELDS = collections.defaultdict(list)


def m2m_signal(sender, **kwargs):
    from slothy.api.models import Group
    action = kwargs['action']
    instance = kwargs['instance']
    pks = kwargs['pk_set']
    if action in ('post_add', 'post_clear', 'post_remove'):
        field_name = getattr(sender, '_meta').object_name.split('_')[-1]
        field = instance.get_field(field_name)
        group = Group.objects.get_or_create(
            name=field.verbose_name, lookup=field_name
        )[0]
        for user in field.related_model.objects.filter(pk__in=pks):
            if action in ('post_clear', 'post_remove'):
                user.groups.remove(group)
            else:
                user.groups.add(group)


def setup_signals():
    if hasattr(settings, 'AUTH_USER_MODEL'):
        from slothy.api.models import Group
        auth_user_model = apps.get_model(settings.AUTH_USER_MODEL)
        group_related_objects = [
            related_object for related_object in getattr(auth_user_model, '_meta').related_objects if
            hasattr(related_object.field, 'is_group') and related_object.field.is_group
        ]
        for related_object in group_related_objects:
            descriptor = getattr(related_object.field.model, related_object.field.name)
            if hasattr(descriptor, 'through'):
                signals.m2m_changed.connect(
                    m2m_signal, sender=descriptor.through
                )
            else:
                FOREIGNKEY_GROUP_FIELDS[related_object.related_model].append(related_object.field.name)


def pre_save(instance):
    if type(instance) in FOREIGNKEY_GROUP_FIELDS:
        values = type(instance).objects.filter(pk=instance.pk).values(
            *FOREIGNKEY_GROUP_FIELDS[type(instance)]
        )
        setattr(instance, '_foreignkey_group_values', values.first() or {})


def post_save(instance):
    from slothy.api.models import Group
    from slothy.api.models import AbstractUser
    if isinstance(instance, AbstractUser) or hasattr(instance, '__parent_foreignkey_field__'):
        group = Group.objects.get_or_create(
            name=instance.get_metadata('verbose_name'),
            lookup=instance.get_metadata('model_name')
        )[0]
        if hasattr(instance, '__parent_foreignkey_field__'):
            user = getattr(instance, getattr(instance, '__parent_foreignkey_field__'))
        else:
            user = instance
        user.groups.add(group)
    if type(instance) in FOREIGNKEY_GROUP_FIELDS:
        previous_values = getattr(instance, '_foreignkey_group_values')
        for field_name in FOREIGNKEY_GROUP_FIELDS[type(instance)]:
            field = instance.get_field(field_name)
            user = getattr(instance, field_name)
            group = Group.objects.get_or_create(
                name=field.verbose_name,
                lookup=field_name
            )[0]
            if user:
                user.groups.add(group)
            else:
                previous_value = previous_values.get(field_name)
                if previous_value:
                    user = field.related_model.objects.filter(pk=previous_value).first()
                    if user:
                        lookup = {field_name: previous_value}
                        if not type(instance).objects.filter(**lookup).exists():
                            user.groups.remove(group)


def pre_delete(instance):
    if hasattr(instance, '__parent_foreignkey_field__'):
        from slothy.api.models import Group
        group = Group.objects.get_or_create(
            name=instance.get_metadata('verbose_name'),
            lookup=instance.get_metadata('model_name')
        )[0]
        user = getattr(instance, getattr(instance, '__parent_foreignkey_field__'))
        lookup = {getattr(instance, '__parent_foreignkey_field__'): user}
        if type(instance).objects.filter(**lookup).count() == 1:
            user.groups.remove(group)

    if type(instance) in FOREIGNKEY_GROUP_FIELDS:
        from slothy.api.models import Group
        for field_name in FOREIGNKEY_GROUP_FIELDS[type(instance)]:
            field = instance.get_field(field_name)
            user = getattr(instance, field_name)
            group = Group.objects.get_or_create(
                name=field.verbose_name,
                lookup=field_name
            )[0]
            if user:
                lookup = {field_name: user.pk}
                if type(instance).objects.filter(**lookup).count() == 1:
                    user.groups.remove(group)


def pre_new(bases, attrs):
    user_base = [cls for cls in bases if hasattr(cls, 'USERNAME_FIELD')]
    if user_base:
        from django.db.models import Model, ForeignKey
        model = user_base.pop()
        parent_foreignkey_field = model.get_metadata('model_name').lower()
        attrs.update(**{
            '__parent_foreignkey_field__': parent_foreignkey_field,
            parent_foreignkey_field: ForeignKey(model, verbose_name=model.get_metadata('verbose_name')),
        })
        return Model,
    return bases


def post_new(cls):
    if hasattr(cls, '__parent_foreignkey_field__'):
        def __getattr__(self, attribute):
            if attribute in self.__dict__:
                return getattr(self, attribute)
            else:
                return getattr(getattr(self, getattr(cls, '__parent_foreignkey_field__')), attribute)

        cls.__getattr__ = __getattr__


def custom_serialize(obj):
    from slothy.api.models import QuerySet, ValuesDict
    if isinstance(obj, datetime.datetime):
        return obj.strftime('%d/%m/%Y %H:%M')
    elif isinstance(obj, datetime.date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, QuerySet):
        return list(obj.values())
    elif isinstance(obj, ValuesDict):
        return dict(obj)
    return obj


def igetattr(obj, attr):
    for a in dir(obj):
        if a.lower() == attr.lower():
            return getattr(obj, a)


def getattrr(obj, args, request=None):
    if args == '__str__':
        splitargs = [args]
    else:
        splitargs = args.split('__')
    return _getattr_rec(obj, splitargs, request=request)


def _getattr_rec(obj, attrs, request=None):
    attr_name = attrs.pop(0)
    if obj is not None:
        attr = getattr(obj, attr_name)
        # manager or relation
        if hasattr(attr, 'all'):
            value = attr.all()
        # method in model or manager
        elif callable(attr) and (hasattr(obj, 'pk') or hasattr(obj, '_queryset_class')):
            if hasattr(obj, 'pk'):  # model
                metadata = getattr(attr, '_metadata', {})
            else:  # manager
                metadata = getattr(getattr(getattr(obj, '_queryset_class'), attr_name), '_metadata')

            def value(*args, **kwargs):
                _value = attr(*args, **kwargs)
                return _value

            value._metadata = metadata
        # primitive type
        else:
            value = attr
        return _getattr_rec(value, attrs, request=request) if attrs else value
    return None


def apply(model, func, data, user):
    lookups = None
    metadata = {}
    if hasattr(func, '_metadata'):
        metadata = getattr(func, '_metadata')
        lookups = metadata.get('lookups')
    if lookups is None and func.__name__ in ('list', 'add'):
        lookups = model.get_metadata('{}_expose'.format(func.__name__))
    if lookups is None:
        if hasattr(func.__self__, '_queryset_class'):
            manager = getattr(func.__self__, '_queryset_class')
            if hasattr(manager, func.__name__):
                metadata = getattr(getattr(manager, func.__name__), '_metadata', {})
                lookups = metadata.get('lookups')

    if lookups is not None:
        if model.check_lookups(user, lookups):
            for name, value in data.items():
                field = metadata.get('fields', {}).get(name) or model.get_field(name)
                if field:
                    try:
                        form_field = data[name] = field.formfield()
                        if form_field:
                            data[name] = form_field.clean(value)
                    except ValidationError as e:
                        raise ValidationError({name: e.message})
                else:
                    raise BaseException('Type of "{}" is unknown')

            result = func(**data)
            if hasattr(result, 'all'):
                result = list(result.values())
            if hasattr(result, 'pk'):
                result = result.values()
            return result
        else:
            raise BaseException('Permission denied')
    else:
        raise BaseException('This function is not exposed')
