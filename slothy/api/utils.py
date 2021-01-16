import datetime
import collections
from django.conf import settings
from django.db.models import signals
from django.apps import apps

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
            type(related_object.field).__name__ in ('RoleForeignKey', 'RoleManyToManyField')
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


def check_group_membership(instance, remove=False):
    from slothy.api.models import Group
    role_field_name = getattr(type(instance), '_metadata', {}).get('role_field_name')
    if role_field_name:
        group_name = instance.get_metadata('verbose_name')
        group_lookup = instance.get_metadata('model_name')
        group = Group.objects.get_or_create(name=group_name, lookup=group_lookup)[0]
        if role_field_name == 'id':
            user = instance
        else:
            user = getattr(instance, role_field_name)
        if remove:
            remove_lookup = {role_field_name: user}
            if type(instance).objects.filter(**remove_lookup).count() == 1:
                user.groups.remove(group)
        else:
            user.groups.add(group)


def post_save(instance):
    check_group_membership(instance)
    if type(instance) in FOREIGNKEY_GROUP_FIELDS:
        from slothy.api.models import Group
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
    check_group_membership(instance, remove=True)

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


def format_value(value):
    from slothy.api.models import QuerySet
    if value is not None:
        if isinstance(value, datetime.datetime):
            return value.strftime('%d/%m/%Y %H:%M')
        elif isinstance(value, datetime.date):
            return value.strftime('%d/%m/%Y')
        elif isinstance(value, bool):
            return 'Sim' if value else 'Não'
        elif isinstance(value, QuerySet) or isinstance(value, list):
            if value:
                return ','.join([str(obj) for obj in value])
        else:
            return str(value)
    return None


def custom_serialize(obj, detail=False):
    from django.db.models.fields.files import FieldFile
    from slothy.api.models import QuerySet, ValueSet, Model
    if isinstance(obj, bool):
        return obj and 'Sim' or 'Não'
    elif isinstance(obj, datetime.datetime):
        return obj.strftime('%d/%m/%Y %H:%M')
    elif isinstance(obj, datetime.date):
        return obj.strftime('%d/%m/%Y')
    elif isinstance(obj, QuerySet):
        if detail:
            return obj.serialize()
        else:
            return ', '.join((str(instance) for instance in obj)) or None
    elif isinstance(obj, ValueSet):
        return dict(type='valueset', fields=obj.get_nested_values(), actions=obj.actions)
    elif isinstance(obj, Model):
        return str(obj)
    elif isinstance(obj, FieldFile):
        return obj.name or None
    return obj


def make_choices(name, field, custom_choices):
    from django.forms.fields import BooleanField
    if name in custom_choices:
        choices = []
        for obj in custom_choices[name]:
            choices.append([obj.id, str(obj)])
        return choices
    elif hasattr(field, 'choices'):
        if hasattr(field.choices, 'queryset'):
            if field.choices.queryset.count() < 1:
                choices = []
                for obj in field.choices.queryset:
                    choices.append([obj.id, str(obj)])
                return choices
            else:
                return field.choices.queryset.display('__str__').serialize(field.label)
        else:
            return field.choices
    else:
        if isinstance(field, BooleanField):
            return [[True, 'Sim'], [False, 'Não']]
    return None


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

