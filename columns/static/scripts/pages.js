var Page = Backbone.Model.extend({
	defaults: {
		title: '',
		content: '',
		visible: true,
		in_main: false,
		in_menu: false,
		can_post: false,
		stream_comment_style: "none", 
		story_comment_style: "none", 
	},
	url: function(){
		if (this.isNew()){
			return '/api/pages/';
		} else {
			return '/api/pages/' + this.id;
		}
	},
	parse: function(resp, xhr) {
		return resp.resource;
	}
}); 

var PageList = Backbone.Collection.extend({
	model: Page,
	url: '/api/pages/',
    parse : function(resp, xhr) {
      return resp.resources;
    }
});  

var PageView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var tmpl = '\
		<div class="page-content">{{{content}}}</div>\
		';
		var template_vars = this.model.toJSON();
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
	}
});

var PageIndexView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var tmpl = '\
		<a href="#/pages/new" class="new-link">Create New</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>Name</th>\
					<th>Visible</th>\
					<th>In Main Feed</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/pages/{{id}}/edit">Edit</a></td>\
					<td>{{title}}</td>\
					<td>{{#visible}}True{{/visible}}{{^visible}}False{{/visible}}</td>\
					<td>{{#in_main}}True{{/in_main}}{{^in_main}}False{{/in_main}}</td>\
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

var PageFormView = Backbone.View.extend({
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
		var tmpl = '\
		<form id="save-form">\
			<div class="field-n-label">\
				<label for="title">Page Title</label>\
				<input type="text" name="title" value="{{title}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="visible">Is Visible</label>\
				<input type="checkbox" name="visible" value="1"{{#visible}} checked="checked"{{/visible}} />\
			</div>\
			<div class="field-n-label">\
				<label for="can_post">Enable Posts</label>\
				<input type="checkbox" name="can_post" value="1"{{#can_post}} checked="checked"{{/can_post}} />\
			</div>\
			<div class="field-n-label">\
				<label for="in_menu">Show Page in Menu</label>\
				<input type="checkbox" name="in_menu" value="1"{{#in_menu}} checked="checked"{{/in_menu}} />\
			</div>\
			<div class="field-n-label">\
				<label for="in_main">Show Posts in Main Stream</label>\
				<input type="checkbox" name="in_main" value="1"{{#in_main}} checked="checked"{{/in_main}} />\
			</div>\
			<div class="field-n-label">\
				<label for="stream_comment_style">Stream Comment Style</label>\
				<select name="stream_comment_style">\
					<option value="none">None</option>\
					<option value="summary">Summary</option>\
					<option value="list">List</option>\
				</select>\
			</div>\
			<div class="field-n-label">\
				<label for="story_comment_style">Story Comment Style</label>\
				<select name="story_comment_style">\
					<option value="none">None</option>\
					<option value="summary">Summary</option>\
					<option value="list">List</option>\
				</select>\
			</div>\
			<div class="field-n-label">\
				<label for="content">Content</label>\
				<textarea name="content" class="jquery_ckeditor">{{content}}</textarea>\
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
		$("select[name='stream_comment_style']").val(template_vars.stream_comment_style);
		$("select[name='story_comment_style']").val(template_vars.story_comment_style);
		$("select, input:checkbox, input:radio, input:file").uniform();
	},
	save_form: function(){
		var router = this.router;
		var model = this.model;
		var field_names = ['title', 'visible', 'can_post', 'in_menu', 'in_main', 'content', 'stream_comment_style', 'story_comment_style'];
		model.save({
			title: this.$('input[name="title"]').val(),
			visible: this.$('input[name="visible"]:checked').val(),
			can_post: this.$('input[name="can_post"]:checked').val(),
			in_menu: this.$('input[name="in_menu"]:checked').val(),
			in_main: this.$('input[name="in_main"]:checked').val(),
			content: this.$('textarea[name="content"]').val(),
			stream_comment_style: this.$('select[name="stream_comment_style"] option:selected').val(),
			story_comment_style: this.$('select[name="story_comment_style"] option:selected').val()
		},
		{
			success: function(model, response){
				console.log(response);
				console.log(model);
				router.navigate('/pages/', true);
			},
			error: function(model, response){
				console.log(response);
				console.log(model);
				if (response.status == 200 || response.status == 201){
					router.navigate('/pages/', true);
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
				router.navigate('/pages/', true);
			},
			error: function(model, response){
				console.log(response);
			}
		});
		return false;
	}
});

var PageCtrl = Backbone.Router.extend({
	routes: {
		"/pages/":			"index",	// #/
		"/pages/new":		"new",		// #/new
		"/pages/:id":		"show",		// #/13
		"/pages/:id/edit":	"edit"		// #/13/edit
	},
	initialize: function(options){
		_.bindAll(this, 'index', 'edit', 'new', 'show'); // fixes loss of context for 'this' within methods
	},
	index: function() {
		var ctrl = this;
		var collection = new PageList();
		collection.fetch({
			success: function(model, resp){
				var view = new PageIndexView({collection: collection});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('', true);
			}
		});
	},
	new: function() {
		var ctrl = this;
		var model = new Page();
		var view = new PageFormView({model: model, router: ctrl});
		view.render();
	},
	show: function(id) {
		var ctrl = this;
		var model = new Page();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new PageView({model: model});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/pages/', true);
			}
		});
	},
	edit: function(id) {
		var ctrl = this;
		var model = new Page();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new PageFormView({model: model, router: ctrl});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/pages/', true);
			}
		});
	}
});

var pages_app = new PageCtrl();

