api.context({
    title: 'That is working!! :)',
    items: {a: 1, b:2},
    usuarios: api.app.usuario.all(),
})
api.render();
