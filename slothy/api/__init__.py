import django.db.models.options as options
setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + (
    'list_filter', 'list_display', 'search_fields', 'list_per_page', 'exclude'
))
