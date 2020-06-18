
if (typeof require != 'undefined')
    var slothy = require('./slothy.js')
    Api = slothy.Api
    print = slothy.print

//sync_request('GET', 'http://localhost:8000/myapp/usuario/1/')

//var client = new Client()
//client.get('/api/group/')
//client.get('/myapp/usuario/1/')
//client.login('bruno_ufrn_natal@yahoo.com.br', '123')
//client.get('/user/')

//endpoint = new Endpoint(client)
//endpoint.append('myapp')
//endpoint.append('usuario')
//endpoint.get(1)
//endpoint.append('myapp')
//endpoint.append('usuario')
//endpoint.all()

//endpoint = EndpointProxy(client)
//endpoint.myapp.usuario.all()
//endpoint.myapp.usuario.get(1)
//endpoint.api.group.all()

api = Api('localhost', 8000)
user = api.app.usuario.add({nome: 'Carlos Breno Pereira Silva', email: 'brenokcc@yahoo.com.br'})
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

