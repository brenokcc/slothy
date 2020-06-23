import django.db.models.options as options
setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + (
    'add_expose', 'edit_expose', 'delete_expose', 'list_expose', 'list_display', 'view_display', 'add_lookups', 'list_lookups'
))
