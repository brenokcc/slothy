# -*- coding: utf-8 -*-
import django.db.models.options as options
from django.utils.text import slugify

setattr(options, 'DEFAULT_NAMES', options.DEFAULT_NAMES + (
    'icon', 'lookups', 'add_lookups', 'edit_lookups', 'delete_lookups', 'list_lookups', 'fieldsets', 'list_display', 'list_actions',
    'menu', 'fields', 'exclude', 'search_fields', 'list_filter', 'list_shortcut', 'list_subsets', 'add_shortcut', 'select_display',
    'list_formatter', 'list_per_page', 'view_display'
))

