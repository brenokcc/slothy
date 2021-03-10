from slothy.forms import Form
from django import forms
from slothy.decorators import dashboard


@dashboard.card()
@dashboard.center()
class Teste(Form):
    nome = forms.CharField(label='Nome')
    data = forms.DateField(label='Data')

    class Meta:
        title = 'Formulário'
        icon = 'play'
        lookups = ()
        fieldsets = {
            'Dados Gerais': ('nome', 'data')
        }

    def show(self):
        return super().show()

    def submit(self):
        print(self.data)

