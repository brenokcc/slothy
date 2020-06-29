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
    this.headerText = null;
    this.headerImage = null;
    this.setHeader = function(headerText, headerImage){
        this.headerText = headerText;
        this.headerImage = headerImage;
    }
    this.save = function(filename){
        var content = renderTemplate(this.templateName, this.context);
        if(this.headerImage) content+= '<img src="'+this.headerImage+'" alt="" width="0" height="0">'
        var html = renderTemplate('components/Report.html', {content:content});
        var headerImage = this.headerImage;
        var headerText = this.headerText;
        html2pdf().from(html).set({
           margin: [2.5, 0.5, 1.5, 0.5],
           filename: filename,
           pageBreak: {mode: 'css'},
           jsPDF: {orientation: 'portrait', unit: 'cm', format: 'a4'}
        }).toPdf().get('pdf').then(function (pdf) {
           var totalPages = pdf.internal.getNumberOfPages();
           for (i = 1; i <= totalPages; i++) {
             pdf.setPage(i);
             var startText = 0.5;
             if(headerImage){
                var img = new Image()
                img.src = headerImage;
                pdf.addImage(img, 'jpg', 0.5, 0.5, 2.0, 2.0);
                startText = 3;
             }
             pdf.setFontSize(12);
             pdf.text(
                headerText, startText,
                (pdf.internal.pageSize.getHeight()-29)
             );
             pdf.setFontSize(10);
             pdf.text('Página '+i+' de '+totalPages, 0.5, pdf.internal.pageSize.getHeight()-1.0)
          }}).save();
    }
}