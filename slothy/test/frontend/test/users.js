if (typeof require != "undefined"){
    var slothy = require('slothy-nodejs/slothy')
    Api = slothy.Api
    print = slothy.print
}

app = App('http://localhost:8000')
user = app.base.usuario.add({nome: 'Bruno José', email: 'bruno_ufrn_natal@yahoo.com.br'})
app.base.usuario.all()
user = app.base.usuario.get(user.id)
user.change_password({raw_password: '123'})
app.login(user.email, '123')
app.user()
app.logout()
app.user()
user.delete()
app.base.usuario.all()


//app.base.usuario.add
//app.base.usuario.all

