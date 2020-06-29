var world = 'World!!!!';

function currentDate(){
    return Date();
}

var map = new BrazilMap('Mapa do Brasil');
map.add('SP', 30);
map.add('RN', 70);

var timeline = new Timeline('Linha do Tempo');
timeline.add('Lorem Ipsum', '01/01/2020', [['Key', 'Value']]);
timeline.add('Lorem Ipsum', '01/02/2020', [['Key', 'Value']]);
timeline.add('Lorem Ipsum', null, []);


function printReport(){
    report = new Report('pages/report.html', {});
    report.setHeader('EMPRESA FICTÍCIA LTDA\nRua das Flores\nTelefone (84) 2222-2387', '/images/slothy.png');
    report.save('Relatorio.pdf');
}

function greet(data){
    reload('greeting', data);
}



