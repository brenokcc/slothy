
function print(data){
    if(data && typeof data.data == "object") data = data.data; // it is a response proxy
    return JSON.stringify(data, undefined, 2);
}
function dir(endpoint){
    return endpoint.dir();
}

if (typeof require == 'undefined'){ // browser
    function sync_request(method, url, data, token){
        console.log(url);
        //console.log(data);
        var headers = {}
        if(token) headers['Authorization'] = 'Token '+token;
        if(typeof window && $.cookie("token")) headers['Authorization'] = 'Token '+$.cookie("token");
        var options = {
            type: method,
            url: url,
            headers: headers,
            data: data,
            dataType: 'json',
            async: false
        }
        if(data instanceof FormData){
            options['processData'] = false;
            options['contentType'] = false;
        }
        data = $.ajax(options).responseJSON;
        console.log(data)
        return data;
    }
} else { // nodejs
    // npm install sync-request
    const querystring = require('querystring');
    const http = require('http');
    const request = require('sync-request');
    function sync_request(method, url, data, token){
        var headers = {}
        if(token) headers['Authorization'] = 'Token '+token
        if(method=='GET') url += '?'+querystring.stringify(data);
        var res = request(method, url, {headers:headers, json:data})
        data = JSON.parse(res.getBody('utf8'))
        print(data)
        return data
    }
}

function Client(url='http://localhost:8000') {
    this.url = url;
    this.token = null;
    this.lazy = false;
	this.request = function(method, url, data){
	    var request = new Request(method, url, data, this)
	    if(!this.lazy) request.fetch()
        return Response(request);
	 }
	this.get = function(url, data={}){
	    return this.request('GET', url, data)
	}
	this.post = function(url, data={}){
	    return this.request('POST', url, data)
	}
}

function Request(method, url, input, client){
    this.method = method;
    this.url = url;
    this.client = client;
    this.input = input;
    this.response = null;
    this.fetch = function(){
        this.response = sync_request(this.method, this.client.url+url, this.input, this.client.token);
        // the response returned an object
        if(this.response.url) this.url = this.response.url;
    }
    this.print = function(){
        return print(this.response.data);
    }
}

function Response(request){
    return new Proxy(request, {
      get(request, attr) {
        if(request.response==null && attr!='add' && attr!='remove' && attr!='dir') request.fetch()
        if(attr in request){ // getting a request attribute
            return request[attr]
        }
        else if(attr in request.response){ // getting a response attribute
            return request.response[attr]
        }
        else if(attr in request.response.data){ // getting a response data attribute
            return request.response.data[attr]
        }
        else{ // executing a function
            return function(data){
                if(data && typeof data == "number") data = {'id': data} // it is an id
                if(data && typeof data.data == "object") data = data.data; // it is a response proxy
                return request.client.post(request.url+attr+'/', data)
            }
        }
      },
    });
}

function App(url='http://localhost:8000'){
    var client = new Client(url);
    return EndpointProxy(new Endpoint(client));
}

function Endpoint(client){
    this.template = null;
    this.client = client;
    this.data = []
    this.path = []
    this.context = {}
    this.execute = function(){
        var path = window.document.location.pathname.substring(1) || 'index';
        this.template = 'pages/'+path+'.html';
        this.context = this.load('/pages/'+path+'.js');
        this.context['app'] = this;
        this.render()
    }
    this.load = function(script){
        var context = Array();
        var vars = Array();
        for(key in window) vars[key]=true;
        $.ajax({async: false, url: script, dataType: "script"});
        for(key in window){
            if(vars[key]!=true) context[key] = window[key];
        }
        return context;
    }
    this.clone = function(){
        var endpoint = new Endpoint()
        endpoint.template = this.template
        endpoint.client = this.client;
        endpoint.data = this.data;
        endpoint.path = this.path.slice(0);
        return endpoint
    }
    this.getUrl = function(){
        if(this.path.length) var url = '/api/'+this.path.join('/')+'/';
        else var url = '';
        this.path = []
        return url;
    }
    this.lazy = function(lazy=true){
        this.client.lazy = lazy;
    }
    this.dir = function(){
        if(this.path.length){
            data = this.client.get(this.getUrl()+'dir/').data;
        } else {
            data = this.client.get('/api/dir/').data
        }
        return print(data);
    }
    this.login = function(username, password){
        var response = this.client.post('/api/login', {username: username, password: password})
        if(response.data){
            this.client.token = response.data.token;
            if(typeof window) $.cookie("token", this.client.token);
        }
        return response;
    }
    this.logout = function(){
        this.client.token = null;
        if(typeof window) $.removeCookie("token");
        var response = this.client.get('/api/logout');
        return response;
    }
    this.user = function(){return this.client.post('/api/user', {})}
    this.all = function(){return this.client.get(this.getUrl())}
    this.get = function(pk){return this.client.get(this.getUrl()+pk+'/', {})}
    this.add = function(data){return this.client.post(this.getUrl()+'add/', data);}
    this.getRenderer = function(){
        var env = nunjucks.configure(document.location.origin, { autoescape: false, web: {useCache: true} });
        env.addFilter('bold', bold);
        return env;
    }
    this.render = function(){
        try{
            var html = this.getRenderer().render(this.template, this.context);
            $(window.document.body).html(html);
            this.initialize(window.document.body);
        } catch (e) {
            if(e.message.indexOf('template not found')) throw e;
        }
    }
    this.reload = function(element){
        var html = this.getRenderer().getTemplate(this.template).tmplStr;
        html = html.replace(/src/g, 'data-src');
        html = $('<div>'+html+'</div>').find(element).html();
        html = this.getRenderer().renderString(html, this.context);
        html = html.replace(/data-src/g, 'src');
        $(document).find(element).html(html);
        this.initialize(element);
    }
    this.initialize = function(element){
        var app = this;
        app.client.lazy = false;
        $(element).find("form").unbind("submit").submit(function( event2 ) {
          event2.preventDefault();

          //process data
          var action = this.action;

          //var data = {};
          //var fdata = $(this).serializeArray();
          //for(var i=0; i<fdata.length; i++) data[fdata[i].name] = fdata[i].value;

	      var data = new FormData(this);

          var obj = window;
          var tokens = action.split('/').pop().split('.').reverse();
          while(tokens.length>1){
            var token = tokens.pop();
            obj = obj[token];
          }
          var func = obj[tokens.pop()](data);

          var path = $(this).data("redirect");
          if(path){
            app.redirect(path);
          } else {
              // reload elements
              var rdata = $(this).data("reload");
              if(rdata){
                var elements = rdata.split(',');
                for(var i=0; i<elements.length; i++){
                    app.reload(elements[i]);
                }
              }
          }

        });
    }
    this.redirect = function(path){
        document.location.href = path;
    }
    this.context = function(data){
        data['app'] = this;
        this.data = data;
    }
}

function EndpointProxy(endpoint){
    return new Proxy(endpoint, {
      get(endpoint, attr) {
        if(attr in endpoint){
            return endpoint[attr]
        }
        else{
            var tmp = endpoint.clone();
            tmp.path.push(attr);
            if(tmp.path.length>2){
                return function(data){
                    return tmp.client.post(this.getUrl()+attr+'/', data)
                }
            } else {
                return EndpointProxy(tmp);
            }
        }
      },
      set(endpoint, attr, value){
        endpoint[attr] = value;
      }
    });
}

function bold(x){
	return '<b>'+x+'</b>';
}

if (typeof exports != 'undefined'){
    exports.App = App
    exports.print = print
}