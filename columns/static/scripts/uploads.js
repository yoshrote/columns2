var Upload = Backbone.Model.extend({
	defaults: {
		title: '',
		content: ''
	},
	url: function(){
		if (this.isNew()){
			return '/api/uploads/';
		} else {
			return '/api/uploads/' + this.id;
		}
	},
	parse : function(resp, xhr) {
		if(resp.resource === undefined)
			return resp; // from a collection
		else
			return resp.resource;
	}
});
     
var UploadList = Backbone.Collection.extend({
	model: Upload,
	limit: 20,
	offset: 0,
	sort_order: 'updated.desc',
	comparator: function(upload) {
		return -(new Date(upload.get("updated")).getTime());
	},
	url: function(){
		return '/api/uploads/?limit='+this.limit+'&offset='+this.offset+'&order='+this.sort_order;
	},
    parse : function(resp, xhr) {
      return resp.resources;
    }
});  

var UploadView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(){
		$('section#admin-content').unbind()
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		//we need the base static url
		var tmpl = '\
		<div class="pictures-show">\
			<h2>{{title}}</h2>\
			<img src="{{static_base}}{{filepath}} alt="{{title}}" />\
			<p>{{ resource.content }} </p>\
		</div>\
		';
		var template_vars = this.model;
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
	}
});

var UploadIndexView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
		'click .prev-upload-page': 'prev_page',
		'click .next-upload-page': 'next_page'
	},
	initialize: function(options){
		$('section#admin-content').unbind()
		_.bindAll(this, 'render', 'prev_page', 'next_page'); // fixes loss of context for 'this' within methods
		this.router = options.router;
		this.lang = options.lang;
	},
	render: function(){
		var tmpl = '\
		<a href="#/uploads/new" class="new-link">{{ lang.create_new }}</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>{{ lang.upload.filename_head }}</th>\
					<th>{{ lang.upload.date_head }}</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/uploads/{{id}}/edit">{{ lang.edit }}</a></td>\
					<td><a href="{{static_base}}{{filepath}}" target="blank_">{{title}}</a></td>\
					<td>{{updated}}</td>\
				</tr>\
			{{/resources}}\
			</tbody>\
		</table>\
		<div>\
			<a href="#/uploads/" class="prev-upload-page" >{{ lang.previous }}</a>\
			<a href="#/uploads/" class="next-upload-page" >{{ lang.next }}</a>\
		</div>\
		';
		var template_vars = this.collection.toJSON();
		for(var i=0;i < template_vars.length; i++){
			template_vars[i].updated = moment(template_vars[i].updated).format(this.lang.update_format);
		}
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

var UploadFormView = Backbone.View.extend({
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
			{{#is_new}}\
			<div class="field-n-label">\
				<label for="upload">{{ lang.upload.file_label }}</label>\
				<input type="file" name="upload" />\
			</div>\
			{{/is_new}}\
			<div class="field-n-label">\
				<label for="title">{{ lang.upload.title_label }}</label>\
				<input type="text" name="title" value="{{title}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="content">{{ lang.upload.content_label }}</label>\
				<textarea name="content">{{content}}</textarea>\
			</div>\
			<input type="submit" name="save" value="{{ lang.save_button }}" class="form-submit-left"/>\
		</form>\
		{{^is_new}}\
		<form id="delete-form">\
			<div>\
				<input type="submit" value="{{ lang.delete_button }}" class="form-submit-right"/>\
			</div>\
		</form>\
		{{/is_new}}\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
		$("input:file").uniform();
	},
	save_form: function(){
		var router = this.router;
		var model = this.model;
		var field_names = ['title', 'content'];
		model.save({
			title: this.$('input[name="title"]').val(),
			content: this.$('textarea[name="content"]').val(),
		},
		{
			success: function(model, response){
				router.navigate('//uploads/', true);
			},
			error: function(model, response){
				if (response.status == 200 || response.status == 201){
					router.navigate('//uploads/', true);
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
				router.navigate('//uploads/', true);
			},
			error: function(model, response){
				console.log(view.lang.delete_error);
				console.log(model);
				console.log(response);
			}
		});
		return false;
	}
});


var UploadCtrl = Backbone.Router.extend({
	routes: {
		"/uploads/":			"index",	// #/
		"/uploads/new":			"new",		// #/new
		"/uploads/:id":			"show",		// #/13
		"/uploads/:id/edit":	"edit"		// #/13/edit
	},
	initialize: function(options){
		_.bindAll(this, 'index', 'edit', 'new', 'show'); // fixes loss of context for 'this' within methods
		this.lang = APP_STATE.lang;
	},
	index: function() {
		var router = this;
		var collection = new UploadList();
		collection.fetch({
			success: function(model, resp){
				var view = new UploadIndexView({collection: collection, router: router, lang: router.lang});
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
		var model = new Upload();
		var view = new UploadFormView({model: model, router: router, lang: router.lang});
		view.render();
	},
	show: function(id) {
		var router = this;
		var model = new Upload();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UploadView({model: model});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('//uploads/', true);
			}
		});
	},
	edit: function(id) {
		var router = this;
		var model = new Upload();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UploadFormView({model: model, router: router, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('//uploads/', true);
			}
		});
	}
});

