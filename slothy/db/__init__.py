import django.db.models.options as options
setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + (
    'icon', 'fieldsets'
))
