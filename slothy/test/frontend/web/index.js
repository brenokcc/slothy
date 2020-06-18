api.lazy = true;
api.context({
    title: 'That is working!! :)',
    items: {a: 1, b:2},
    usuarios: api.app.usuario.all(),
    grupos: api.backend.group.all(),
})
api.render();
