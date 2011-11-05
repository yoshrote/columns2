
var User = Backbone.Model.extend({
	defaults: {
		title: '',
		content: ''
	},
	parse : function(resp, xhr) {
		return resp.resource;
	}
});      
var UserList = Backbone.Collection.extend({
	model: User,
	url: '/api/users/',
    parse : function(resp, xhr) {
      return resp.resources;
    }
});  

var UserView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var tmpl = '\
		';
		var template_vars = this.model;
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
	}
});

var UserIndexView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var tmpl = '\
		<a href="#/users/new" class="new-link">Create New</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>Name</th>\
					<th>Type</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/users/{{id}}/edit">Edit</a></td>\
					<td>{{name}}</td>\
					<td>{{type}}</td>\
				</tr>\
			{{/resources}}\
			</tbody>\
		</table>\
		';
		var template_vars = this.collection.toJSON();
		console.log(template_vars);
		Mustache.zebra = true;
		$(this.el).html(Mustache.to_html(tmpl, {
			resources: template_vars,
			zebra: function(){
				var mode = '';
				if(Mustache.zebra){
					mode = 'odd';
				}else{
					mode = 'even';
				}
				Mustache.zebra = !Mustache.zebra;
				return mode;
			}
		}));
	}
});

var UserNewFormView = Backbone.View.extend({
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
		'submit #new-form': 'save_new'
	},
	initialize: function(options){
		_.bindAll(this, 'render', 'save_new'); // fixes loss of context for 'this' within methods
	},
	save_new: function(){
		var model = this.model;
		console.log(model);
		var formData = $('#new-form').serializeArray();
		console.log(formData);
		/*
		for(var i=0; i<formData.length; i++){
			model.set({
				//formData[i]['name']: formData[i]['value']
			});
		}
		*/
		model.save({
			'name': $('input[name="name"]').val(),
			'type': $('select[name="type"] option:selected').val(),
			'open_id': $('input[name="open_id"]').val(),
			'twitter_id': $('input[name="twitter_id"]').val(),
			'fb_id': $('input[name="fb_id"]').val(),
			'profile': $('input[name="profile"]').val()
		});
		var foo = 'bar';
		Backbone.sync();
	},
	render: function(){
		var template_vars = this.model.toJSON();
		var tmpl = '\
		<form id="new-form">\
			<div class="field-n-label">\
				<label for="name">Name</label>\
				<input type="text" name="name" value="{{name}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="type">User Type</label>\
				<select name="type">\
					<option value="1">Super</option>\
					<option value="2">Admin</option>\
					<option value="3">Editor</option>\
					<option value="4">Author</option>\
					<option value="8">Probation</option>\
					<option value="9">Subscriber</option>\
				</select>\
			</div>\
			<div class="field-n-label">\
				<label for="open_id">OpenID URL</label>\
				<input type="text" name="open_id" value="{{open_id}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="twitter_id">Twitter ID</label>\
				<input type="text" name="twitter_id" value="{{twitter_id}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="fb_id">Facebook ID</label>\
				<input type="text" name="fb_id" value="{{fb_id}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="profile">Profile URL</label>\
				<input type="text" name="profile" value="{{profile}}" />\
			</div>\
			<input type="submit" name="save" value="Save" />\
		</form>\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
		$("select, input:checkbox, input:radio, input:file").uniform();
	}
});

var UserEditFormView = Backbone.View.extend({
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(options){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var template_vars = this.model.toJSON();
		var tmpl = '\
		<form id="edit-form">\
			<div class="field-n-label">\
				<label for="name">Name</label>\
				<input type="text" name="name" value="{{name}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="type">User Type</label>\
				<select name="type">\
					<option value="1">Super</option>\
					<option value="2">Admin</option>\
					<option value="3">Editor</option>\
					<option value="4">Author</option>\
					<option value="8">Probation</option>\
					<option value="9">Subscriber</option>\
				</select>\
			</div>\
			<div class="field-n-label">\
				<label for="open_id">OpenID URL</label>\
				<input type="text" name="open_id" value="{{open_id}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="twitter_id">Twitter ID</label>\
				<input type="text" name="twitter_id" value="{{twitter_id}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="fb_id">Facebook ID</label>\
				<input type="text" name="fb_id" value="{{fb_id}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="profile">Profile URL</label>\
				<input type="text" name="profile" value="{{profile}}" />\
			</div>\
			<input type="submit" name="save" value="Save" />\
		</form>\
		<form id="delete-form">\
			<fieldset>\
				<input type="submit" value="Delete" />\
			</fieldset>\
		</form>\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
		$("select, input:checkbox, input:radio, input:file").uniform();
	}
});

var UserCtrl = Backbone.Router.extend({
	routes: {
		"/users/":			"index",	// #/
		"/users/index":		"index",	// #/index
		"/users/new":		"new",		// #/new
		"/users/:id":		"show",		// #/13
		"/users/:id/edit":	"edit"		// #/13/edit
	},
	index: function() {
		var collection = new UserList();
		collection.fetch({
			success: function(model, resp){
				var view = new UserIndexView({collection: collection});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('', true);
			}
		});
	},
	new: function() {
		var model = new User();
		var view = new UserNewFormView({model: model});
		view.render();
	},
	show: function(id) {
		var ctrl = this;
		var model = new User();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UserView({model: model});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/users/', true);
			}
		});
	},
	edit: function(id) {
		var ctrl = this;
		var model = new User();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UserNewFormView({model: model});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/users/', true);
			}
		});
	}
});

var users_app = new UserCtrl();

