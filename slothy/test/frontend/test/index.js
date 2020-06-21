app.lazy();
app.context({
    title: 'That is working!! :)',
    items: {a: 1, b:2},
    usuarios: app.base.usuario.all(),
    grupos: app.api.group.all(),
})

function cadastrar(data){
    app.base.usuario.add(data);
    app.redirect('/')
}
