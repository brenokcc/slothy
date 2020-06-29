//app.debug();
title = 'That is working!! :)',
items = {a: 1, b:2}

function usuarios(){
 return app.base.usuario.all();
}


function cadastrar(data){
    app.base.usuario.add(data);
    app.redirect('/')
}

function relatorio(){
    report = new Report('pages/test/relatorio.html', {});
    report.save('Relatorio.html');
}
