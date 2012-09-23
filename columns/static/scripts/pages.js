var Page = Backbone.Model.extend({
	defaults: {
		title: '',
		content: '',
		visible: true,
		in_main: false,
		in_menu: false,
		can_post: false,
	},
	url: function(){
		if (this.isNew()){
			return '/api/pages/';
		} else {
			return '/api/pages/' + this.id;
		}
	},
	parse: function(resp, xhr) {
		if(resp.resource === undefined)
			return resp; // from a collection
		else
			return resp.resource;
	}
}); 

var PageList = Backbone.Collection.extend({
	model: Page,
	limit: 20,
	offset: 0,
	sort_order: 'slug',
	comparator: function(page) {
		return page.get("slug");
	},
	url: function(){
		return '/api/pages/?limit='+this.limit+'&offset='+this.offset+'&order='+this.sort_order;
	},
    parse : function(resp, xhr) {
      return resp.resources;
    }
});  

var PageView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(){
		$('section#admin-content').unbind()
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
		this.lang = options.lang;
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
		'click .prev-page-page': 'prev_page',
		'click .next-page-page': 'next_page'
	},
	initialize: function(options){
		$('section#admin-content').unbind()
		_.bindAll(this, 'render', 'prev_page', 'next_page'); // fixes loss of context for 'this' within methods
		this.router = options.router;
		this.lang = options.lang;
	},
	render: function(){
		var tmpl = '\
		<a href="#/pages/new" class="new-link">{{ lang.create_new }}</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>{{ lang.page.name_head }}</th>\
					<th>{{ lang.page.visible_head }}</th>\
					<th>{{ lang.page.in_main_head }}</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/pages/{{id}}/edit">{{ lang.edit }}</a></td>\
					<td>{{title}}</td>\
					<td>{{#visible}}{{ lang.true }}{{/visible}}{{^visible}}{{ lang.false }}{{/visible}}</td>\
					<td>{{#in_main}}{{ lang.true }}{{/in_main}}{{^in_main}}{{ lang.false }}{{/in_main}}</td>\
				</tr>\
			{{/resources}}\
			</tbody>\
		</table>\
		<div>\
			<a href="#/pages/" class="prev-page-page" >{{ lang.previous }}</a>\
			<a href="#/pages/" class="next-page-page" >{{ lang.next }}</a>\
		</div>\
		';
		var template_vars = this.collection.toJSON();
		Mustache.zebra = true;
		$(this.el).html(Mustache.to_html(tmpl, {
			lang: this.lang,
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

var PageFormView = Backbone.View.extend({
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
				<label for="title">{{ lang.page.title_label }}</label>\
				<input type="text" name="title" value="{{title}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="visible">{{ lang.page.visible_label }}</label>\
				<input type="checkbox" name="visible" value="1"{{#visible}} checked="checked"{{/visible}} />\
			</div>\
			<div class="field-n-label">\
				<label for="can_post">{{ lang.page.can_post_label }}</label>\
				<input type="checkbox" name="can_post" value="1"{{#can_post}} checked="checked"{{/can_post}} />\
			</div>\
			<div class="field-n-label">\
				<label for="in_menu">{{ lang.page.in_menu_label }}</label>\
				<input type="checkbox" name="in_menu" value="1"{{#in_menu}} checked="checked"{{/in_menu}} />\
			</div>\
			<div class="field-n-label">\
				<label for="in_main">{{ lang.page.in_main_label }}</label>\
				<input type="checkbox" name="in_main" value="1"{{#in_main}} checked="checked"{{/in_main}} />\
			</div>\
			<div class="field-n-label">\
				<label for="content">Content</label>\
				<textarea name="content" class="redactor">{{content}}</textarea>\
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
		$(".redactor").redactor({ fixed: true, imageUpload: '/api/imageupload' });
	},
	save_form: function(){
		var router = this.router;
		var model = this.model;
		var field_names = ['title', 'visible', 'can_post', 'in_menu', 'in_main', 'content'];
		model.save({
			title: this.$('input[name="title"]').val(),
			visible: this.$('input[name="visible"]:checked').val(),
			can_post: this.$('input[name="can_post"]:checked').val(),
			in_menu: this.$('input[name="in_menu"]:checked').val(),
			in_main: this.$('input[name="in_main"]:checked').val(),
			content: this.$('textarea[name="content"]').val(),
		},
		{
			success: function(model, response){
				router.navigate('//pages/', true);
			},
			error: function(model, response){
				if (response.status == 200 || response.status == 201){
					router.navigate('//pages/', true);
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
				router.navigate('//pages/', true);
			},
			error: function(model, response){
				console.log(model);
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
		this.lang = APP_STATE.lang;
	},
	index: function() {
		var router = this;
		var collection = new PageList();
		collection.fetch({
			success: function(model, resp){
				var view = new PageIndexView({collection: collection, router: router, lang: router.lang});
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
		var model = new Page();
		var view = new PageFormView({model: model, router: router, lang: router.lang});
		view.render();
	},
	show: function(id) {
		var router = this;
		var model = new Page();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new PageView({model: model, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('//pages/', true);
			}
		});
	},
	edit: function(id) {
		var router = this;
		var model = new Page();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new PageFormView({model: model, router: router, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('//pages/', true);
			}
		});
	}
});

