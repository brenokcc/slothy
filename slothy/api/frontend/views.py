from django.views.generic import TemplateView


class Base(TemplateView):
    template_name = 'base.html'

