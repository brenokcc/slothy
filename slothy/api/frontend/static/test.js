if (typeof require != 'undefined')
    var slothy = require('./slothy.js')
    Api = slothy.Api
    print = slothy.print

api = Api('localhost', 8000)
user = api.app.usuario.add({nome: 'Bruno José', email: 'bruno_ufrn_natal@yahoo.com.br'})
api.app.usuario.all()
user = api.app.usuario.get(user.id)
user.change_password({raw_password: '123'})
api.login(user.email, '123')
api.user()
api.logout()
api.user()
user.delete()
api.app.usuario.all()

api.backend.group.all()

//api.app.usuario.add
//api.app.usuario.all

