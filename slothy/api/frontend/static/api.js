
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
    this.append = function(token){this.tokens.push(token)}
    this.getUrl = function(){
        if(this.tokens.length>0) var url = '/api/'+this.tokens.join('/')+'/';
        else var url = '';
        this.tokens = []
        return url;
     }
    this.all = function(){return this.client.get(this.getUrl())}
    this.get = function(pk){return this.client.get(this.getUrl()+pk+'/', {})}
    this.add = function(data){return this.client.post(this.getUrl()+'add/', data);}
    this.render = function(template=null, inline=true){
        if(template==null){
            template = this.template;
        }
        var env = nunjucks.configure('/static', { autoescape: false });
        env.addFilter('bold', bold);
        if(template){
            var html = env.render(template, this.data);
        } else {
            var html = env.renderString(window.document.body.innerHTML, this.data);
        }
        if(inline) window.document.body.innerHTML = html;
        return html;
    }
    this.context = function(data){this.data = data}
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
            endpoint.append(attr)
            return EndpointProxy(client, endpoint)
        }
      },
      set(endpoint, attr, value){
        endpoint[attr] = value;
      }
    });
}

function Response(url, response){
    this.url = url;
    this.data = response;
}

function ResponseProxy(client, response){
    return new Proxy(response, {
      get(response, attr) {
        if(attr in response){
            return response[attr]
        }
        else{
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
	    return ResponseProxy(this, new Response(url, sync_request(method, 'http://'+this.hostname+':'+this.port+url, data, this.token)))
	 }
	this.get = function(url, data={}){return this.request('GET', url, data)}
	this.post = function(url, data={}){return this.request('POST', url, data)}
    this.login = function(username, password){
        var response = this.post('/api/login/', {username: username, password: password})
        this.client.token = response.data.token
        return response;
    }
    this.logout = function(){this.get('/api/logout/')}
}

function Api(hostname='localhost', port=8000){
    var client = new Client(hostname, port)
    return EndpointProxy(client)
}

if (typeof exports != 'undefined')
    exports.Api = Api