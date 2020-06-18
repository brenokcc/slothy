
if (typeof require != 'undefined')
    Api = require('./api.js').Api

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

app = Api('localhost', 8000)
//app.login('bruno_ufrn_natal@yahoo.com.br', '123')
//app.myapp.usuario.all()
//u = app.myapp.usuario.get(2)
//u.set_password({raw_password: '321'})
//app.logout();
//app.login('bruno_ufrn_natal@yahoo.com.br', '321')

app.context({
    title: 'Title',
    items: {a: 1, b:2},
    usuarios: app.myapp.usuario.all(),
    usuario: app.myapp.usuario.get(2)
})
app.render('test.html', true);


//app.myapp.usuario.all()
//app.myapp.usuario.all()
//app.myapp.usuario.get(1)
//app.api.group.all()
//o = app.api.group.get(4)
//o.x({z:4})
//g = app.api.group.add({name: 'Superusuário', lookup: 'superuser'})

//app.myapp.usuario.add
//app.myapp.usuario.all

