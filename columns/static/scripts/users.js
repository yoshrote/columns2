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
		$('section#admin-content').unbind()
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
		$('section#admin-content').unbind()
		_.bindAll(this, 'render', 'prev_page', 'next_page'); // fixes loss of context for 'this' within methods
		this.router = options.router;
		this.lang = options.lang;
	},
	render: function(){
		var tmpl = '\
		<a href="#/users/new" class="new-link">{{ lang.create_new }}</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>{{ lang.user.name_head }}</th>\
					<th>{{ lang.user.type_head }}</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/users/{{id}}/edit">{{ lang.edit }}</a></td>\
					<td>{{name}}</td>\
					<td>{{type}}</td>\
				</tr>\
			{{/resources}}\
			</tbody>\
		</table>\
		<div>\
			<a href="#/users/" class="prev-user-page" >{{ lang.previous }}</a>\
			<a href="#/users/" class="next-user-page" >{{ lang.next }}</a>\
		</div>\
		';
		var template_vars = this.collection.toJSON();
		template_vars.lang = this.lang
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
				alert(view.lang.fetch_error);
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
				alert(view.lang.fetch_error);
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
		$('section#admin-content').unbind()
		_.bindAll(this, 'render', 'save_form', 'delete_form'); // fixes loss of context for 'this' within methods
		this.router = options.router;
		this.lang = options.lang;
	},
	render: function(){
		var template_vars = this.model.toJSON();
		template_vars.is_new = this.model.isNew();
		template_vars.lang = this.lang;
		var tmpl = '\
		<form id="save-form">\
			<div class="field-n-label">\
				<label for="name">{{ lang.user.name_label }}</label>\
				<input type="text" name="name" value="{{name}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="type">{{ lang.user.type_label }}</label>\
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
				<label for="open_id">{{ lang.user.open_id_label }}</label>\
				<input type="text" name="open_id" value="{{open_id}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="profile">{{ lang.user.profile_label }}</label>\
				<input type="text" name="profile" value="{{profile}}" />\
			</div>\
			<input type="submit" name="save" value="{{ lang.user.save_button }}" class="form-submit-left"/>\
		</form>\
		{{^is_new}}\
		<form id="delete-form">\
			<div>\
				<input type="submit" value="{{ lang.user.delete_button }}" class="form-submit-right"/>\
			</div>\
		</form>\
		{{/is_new}}\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
	},
	save_form: function(){
		var router = this.router;
		var model = this.model;
		var field_names = ['title', 'type', 'open_id', 'profile'];
		model.save({
			name: $('input[name="name"]').val(),
			type: $('select[name="type"] option:selected').val(),
			open_id: $('input[name="open_id"]').val(),
			profile: $('input[name="profile"]').val()
		},
		{
			success: function(model, response){
				router.navigate('//users/', true);
			},
			error: function(model, response){
				if (response.status == 200 || response.status == 201){
					router.navigate('//users/', true);
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
		var view = this;
		this.model.destroy({
			success: function(model, response){
				router.navigate('//users/', true);
			},
			error: function(model, response){
				console.log(view.lang.delete_error);
				console.log(model);
				console.log(response);
			}
		});
		//return false;
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
		this.lang = APP_STATE.lang;
	},
	index: function() {
		var router = this;
		var collection = new UserList();
		collection.fetch({
			success: function(model, resp){
				var view = new UserIndexView({collection: collection, router: router, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('', true);
			}
		});
	},
	new: function() {
		var router = this;
		var model = new User();
		var view = new UserFormView({model: model, router: router, lang: router.lang});
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
				alert(router.lang.fetch_error);
				router.navigate('//users/', true);
			}
		});
	},
	edit: function(id) {
		var router = this;
		var model = new User();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UserFormView({model: model, router: router, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('//users/', true);
			}
		});
	}
});

