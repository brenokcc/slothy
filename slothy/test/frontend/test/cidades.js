e = app.base.estado.add({sigla: 'SP'})
c = e.get_cidades().add({nome: 'São Paulo'})
e.get_cidades().remove(c)