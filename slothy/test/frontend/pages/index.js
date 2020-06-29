var world = 'World!!!!';

function currentDate(){
    return Date();
}

var map = new BrazilMap('Mapa do Brasil');
map.add('SP', 30);
map.add('RN', 70);

var steps = [
    {date: '01/01/2020', title: 'Inauguração', data: [{key: 'Responsável', value: 'Pedro da Silva'}]},
    {date: '01/03/2020', title: 'Manutencão 01', data: [{key: 'Responsável', value: 'Maria Aparecida'}]},
    {date: null, title: 'Manutencão 02', data: [{key: 'Responsável', value: 'Maria Aparecida'}]},
    {date: null, title: 'Conclusão', data: [{key: 'Responsável', value: 'Pedro da Silva'}]},
]
var timeline1 = new Timeline('Linha do Tempo Horizontal', steps);
var timeline2 = new Timeline('Linha do Tempo Vertical', steps);

function printReport(){
    report = new Report('pages/report.html', {});
    report.setHeader( 'EMPRESA FICTÍCIA LTDA\nRua das Flores\nTelefone (84) 2222-2387');
    report.save('Relatorio.pdf');
}



