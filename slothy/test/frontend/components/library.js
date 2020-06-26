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

function Timeline(title, steps=[]){
	Component.call(this);
	this.title = title;
	this.uuid = Math.random().toString(36).substring(7);
	this.steps = steps;
}