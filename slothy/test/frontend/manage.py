#!/usr/bin/env python
import os
import sys
import warnings

warnings.filterwarnings("ignore", module='(rest_framework|ruamel|scipy|reportlab|django|jinja|corsheaders)')

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
