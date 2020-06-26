function Component(){
	this.templateDir = 'components';
	this.getTemplate = function(){
		return this.templateDir+'/'+this.constructor.name+'.html'
	}
	this.toString = function(){
		return renderTemplate(this.getTemplate(), {'this': this});
	}
}

function BrazilMap(title){
	Component.call(this);
	this.title = title;
	this.series = [];
	this.add = function(state, n){
	    this.series.push(['BR-'+state, n])
	}
}

function Timeline(title){
	Component.call(this);
	this.title = title;
	this.uuid = Math.random().toString(36).substring(7);
	this.steps = [
        {date: '01/01/2020', title: 'Inauguração', data: [{key: 'Responsável', value: 'Pedro da Silva'}]},
        {date: '01/03/2020', title: 'Manutencão 01', data: [{key: 'Responsável', value: 'Maria Aparecida'}]},
        {date: null, title: 'Manutencão 02', data: [{key: 'Responsável', value: 'Maria Aparecida'}]},
        {date: null, title: 'Conclusão', data: [{key: 'Responsável', value: 'Pedro da Silva'}]},
	]
}