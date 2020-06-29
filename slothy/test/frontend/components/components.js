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

function Report(templateName, context){
    this.templateName = templateName;
    this.context = context;
    this.save = function(filename){
        var html = renderTemplate(this.templateName, this.context);
        html2pdf().from(html).set({
           margin: [2.0, 0.5, 1.5, 0.5],
           filename: filename,
           pageBreak: {mode: 'css'},
           jsPDF: {orientation: 'portrait', unit: 'cm', format: 'a4'}
        }).toPdf().get('pdf').then(function (pdf) {
           var totalPages = pdf.internal.getNumberOfPages();
           for (i = 1; i <= totalPages; i++) {
             var img = new Image()
             img.src = '/images/sample.jpg'
             pdf.setPage(i);
             pdf.addImage(img, 'jpg', 0, 0, 2.0, 2.0)
             pdf.setFontSize(14);
             pdf.setTextColor(150);
             pdf.text(
                'Lorem Ipsum is simply dummy text of the printing \nThis is theheader text',
                (3),
                (pdf.internal.pageSize.getHeight()-29.2)
             );
             pdf.setFontSize(10);
             pdf.text('Página '+i+' de '+totalPages, 0.5, pdf.internal.pageSize.getHeight()-1.0)
          }}).save();
    }
}