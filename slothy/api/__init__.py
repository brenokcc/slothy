import django.db.models.options as options
setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + (
    'expose', 'list_display', 'view_display', 'add_lookups', 'list_lookups'
))
