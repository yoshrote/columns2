var User = Backbone.Model.extend({
	defaults: {
		name: '',
		type: ''
	},
	url: function(){
		if (this.isNew()){
			return '/api/users/';
		} else {
			return '/api/users/' + this.id;
		}
	},
	parse : function(resp, xhr) {
		if(resp.resource === undefined)
			return resp; // from a collection
		else
			return resp.resource;
	}
});      

var UserList = Backbone.Collection.extend({
	model: User,
	limit: 20,
	offset: 0,
	sort_order: 'type',
	comparator: function(user) {
		return user.get("type");
	},
	url: function(){
		return '/api/users/?limit='+this.limit+'&offset='+this.offset+'&order='+this.sort_order;
	},
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
		'click .prev-user-page': 'prev_page',
		'click .next-user-page': 'next_page'
	},
	initialize: function(options){
		_.bindAll(this, 'render', 'prev_page', 'next_page'); // fixes loss of context for 'this' within methods
		this.router = options.router;
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
		<div>\
			<a href="#/users/" class="prev-user-page" >Previous</a>\
			<a href="#/users/" class="next-user-page" >Next</a>\
		</div>\
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
	},
	prev_page: function(){
		var router = this.router;
		var collection = this.collection;
		var view = this;
		collection.offset -= collection.limit;
		if(collection.offset < 0){
			collection.offset = 0;
		}
		collection.fetch({
			success: function(model, resp){
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				router.navigate('', true);
			}
		});
	},
	next_page: function(){
		var router = this.router;
		var collection = this.collection;
		var view = this;
		collection.offset += collection.limit;
		collection.fetch({
			success: function(model, resp){
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				router.navigate('', true);
			}
		});
	}
});

var UserFormView = Backbone.View.extend({
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
		'submit #save-form': 'save_form',
		'submit #delete-form': 'delete_form'
	},
	initialize: function(options){
		_.bindAll(this, 'render', 'save_form', 'delete_form'); // fixes loss of context for 'this' within methods
		this.router = options.router;
	},
	render: function(){
		var template_vars = this.model.toJSON();
		template_vars.is_new = this.model.isNew();
		console.log(template_vars);
		var tmpl = '\
		<form id="save-form">\
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
			<input type="submit" name="save" value="Save" class="form-submit-left"/>\
		</form>\
		{{^is_new}}\
		<form id="delete-form">\
			<div>\
				<input type="submit" value="Delete" class="form-submit-right"/>\
			</div>\
		</form>\
		{{/is_new}}\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
	},
	save_form: function(){
		var router = this.router;
		var model = this.model;
		var field_names = ['title', 'type', 'open_id', 'twitter_id', 'fb_id', 'profile'];
		model.save({
			name: $('input[name="name"]').val(),
			type: $('select[name="type"] option:selected').val(),
			open_id: $('input[name="open_id"]').val(),
			twitter_id: $('input[name="twitter_id"]').val(),
			fb_id: $('input[name="fb_id"]').val(),
			profile: $('input[name="profile"]').val()
		},
		{
			success: function(model, response){
				console.log(response);
				console.log(model);
				router.navigate('/users/', true);
			},
			error: function(model, response){
				console.log(response);
				console.log(model);
				if (response.status == 200 || response.status == 201){
					router.navigate('/users/', true);
				} else if (response.status == 400) {
					var errors = JSON.parse(response.responseText);
					for(var i = 0; i < field_names.length; i++){
						var field = field_names[i]
						var field_error = errors[ field ];
						if (field_error === undefined){
						// clear error field if there is no error
							this.$('label[for="' + field + '"] span.error').html('');
						} else {
							var error_label = this.$('label[for="' + field + '"] span.error');
							if (error_label.length == 0){
							// build span.error if it did not exist
								this.$('label[for="' + field + '"]').append(
									' <span class="error">*' + errors[field] + '</span>'
								);
							} else {
							// update the existing span.error
								error_label.html('*' + errors[field]);
							}
						}
					}
				}
			}
		});
		return false;
	},
	delete_form: function(){
		var router = this.router;
		this.model.destroy({
			success: function(model, response){
				router.navigate('/users/', true);
			},
			error: function(model, response){
				console.log(response);
			}
		});
		return false;
	}
});

var UserCtrl = Backbone.Router.extend({
	routes: {
		"/users/":			"index",	// #/
		"/users/new":		"new",		// #/new
		"/users/:id":		"show",		// #/13
		"/users/:id/edit":	"edit"		// #/13/edit
	},
	initialize: function(options){
		_.bindAll(this, 'index', 'edit', 'new', 'show'); // fixes loss of context for 'this' within methods
	},
	index: function() {
		var router = this;
		var collection = new UserList();
		collection.fetch({
			success: function(model, resp){
				var view = new UserIndexView({collection: collection, router: router});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				router.navigate('', true);
			}
		});
	},
	new: function() {
		var router = this;
		var model = new User();
		var view = new UserFormView({model: model, router: router});
		view.render();
	},
	show: function(id) {
		var router = this;
		var model = new User();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UserView({model: model});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				router.navigate('/users/', true);
			}
		});
	},
	edit: function(id) {
		var router = this;
		var model = new User();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UserFormView({model: model, router: router});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				router.navigate('/users/', true);
			}
		});
	}
});

var users_app = new UserCtrl();

