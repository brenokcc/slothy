import django.db.models.options as options
setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + (
    'list_filter', 'list_display', 'list_per_page'
))
