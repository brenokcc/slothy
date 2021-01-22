from slothy.views import View
from .models import Cidade
from slothy.decorators import dashboard


@dashboard.shortcut()
class Teste(View):

    class Meta:
        title = 'Teste'
        lookups = ()

    def view(self):
        print(self.request.user)
        return Cidade.objects.all()
