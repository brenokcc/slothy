from django.views.generic import TemplateView


class Base(TemplateView):
    template_name = 'base.html'

    def get(self, request, *args, path=None):
        src = '/static/{}.js'.format(path or 'index')
        template = '{}.html'.format(path or 'index')
        return super().get(request, src=src, template=template)

