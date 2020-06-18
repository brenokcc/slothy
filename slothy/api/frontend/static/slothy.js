
function print(data){
    console.log(data)
}

if (typeof require == 'undefined'){ // browser
    function sync_request(method, url, data, token){
        console.log(url);
        responseText = $.ajax({
            type: method,
            url: url,
            data: data,
            dataType: 'json',
            async: false
        }).responseText
        print(JSON.parse(responseText))
        data = JSON.parse(JSON.parse(responseText));
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
        data = JSON.parse(JSON.parse(res.getBody('utf8')))
        print(data)
        return data
    }
}

function bold(x){
	return '<b>'+x+'</b>';
}

function Endpoint(client){
    this.template = null;
    this.client = client;
    this.data = []
    this.tokens = []
    this.lazy = false;
    this.clone = function(){
        var endpoint = new Endpoint()
        endpoint.template = this.template
        endpoint.client = this.client;
        endpoint.data = this.data;
        endpoint.lazy = this.lazy;
        endpoint.tokens = this.tokens.slice(0);
        return endpoint
    }
    this.getUrl = function(){
        if(this.tokens.length>0) var url = '/api/'+this.tokens.join('/')+'/';
        else var url = '';
        this.tokens = []
        return url;
     }
    this.login = function(username, password){
        var response = this.post('/api/login/', {username: username, password: password})
        this.client.token = response.data.token
        return response;
    }
    this.logout = function(){
        var response = this.get('/api/logout');
        if(response.error==null && response.exception==null){
            this.client.token = null;
        }
    }
    this.user = function(){this.get('/api/user')}
    this.all = function(){
        var client = this.client;
        var url = this.getUrl();
        var response = function(){
            return client.get(url);
        }
        if(this.lazy){
            return response;
        } else{
            return response();
        }
    }
    this.get = function(pk){return this.client.get(this.getUrl()+pk+'/', {})}
    this.add = function(data){return this.client.post(this.getUrl()+'add/', data);}
    this.getData = function(){
        var data = []
        for(key in this.data){
            if(typeof this.data[key] == 'function'){
                data[key] = this.data[key]();
            } else {
                data[key] = this.data[key];
            }
        }
        return data;
    }
    this.render = function(template=null, inline=true){
        if(template==null){
            template = this.template;
        }
        var env = nunjucks.configure('/static', { autoescape: false });
        env.addFilter('bold', bold);
        if(template){
            var html = env.render(template, this.getData());
        } else {
            var html = env.renderString(window.document.body.innerHTML, this.getData());
        }
        if(inline) window.document.body.innerHTML = html;
        return html;
    }
    this.reload = function(element){
        var env = nunjucks.configure('/static', { autoescape: false });
        var html = $('<div>'+env.getTemplate(this.template).tmplStr+'</div>').find(element).html();
        html = env.renderString(html, this.getData());
        $(document).find(element).html(html);
    }
    this.context = function(data){
        data['api'] = this;
        this.data = data;
    }
}

function EndpointProxy(client, endpoint=null){
    return new Proxy(endpoint||new Endpoint(client), {
      get(endpoint, attr) {
        if(attr in endpoint){
            return endpoint[attr]
        }
        else if(attr in endpoint.client){
            return endpoint.client[attr]
        }
        else{
            var tmp = endpoint.clone();
            tmp.tokens.push(attr);
            return EndpointProxy(client, tmp);
        }
      },
      set(endpoint, attr, value){
        endpoint[attr] = value;
      }
    });
}

function Response(response){
    for(attr in response){
        this[attr] = response[attr];
    }
}

function ResponseProxy(client, response){
    return new Proxy(response, {
      get(response, attr) {
        if(attr in response){ // getting a response attribute
            return response[attr]
        }
        if(attr in response.data){ // getting a response data attribute
            return response.data[attr]
        }
        else{ // executing a function
            return function(data){
                client.post(response.url+attr+'/', data)
            }
        }
      },
    });
}

function Client (hostname='localhost', port=8000) {
    this.hostname = hostname;
    this.port = port;
    this.token = null;
	this.request = function(method, url, data){
	    return ResponseProxy(this, new Response(sync_request(method, 'http://'+this.hostname+':'+this.port+url, data, this.token)))
	 }
	this.get = function(url, data={}){return this.request('GET', url, data)}
	this.post = function(url, data={}){return this.request('POST', url, data)}
}

function Api(hostname='localhost', port=8000){
    var client = new Client(hostname, port)
    return EndpointProxy(client)
}

if (typeof exports != 'undefined'){
    exports.Api = Api
    exports.print = print
}