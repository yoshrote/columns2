var Article = Backbone.Model.extend({
	defaults: {
		title: '',
		content: ''
	},
	url: function(){
		if (this.isNew()){
			return '/api/articles/';
		} else {
			return '/api/articles/' + this.id;
		}
	},
	parse: function(resp, xhr) {
		return resp.resource;
	}
}); 

var ArticleList = Backbone.Collection.extend({
	model: Article,
	url: function(){
		if (this.drafts == true){
			return '/api/articles/?drafts=1';
		} else {
			return '/api/articles/';
		}
	},
    parse : function(resp, xhr) {
      return resp.resources;
    }
});  

var ArticleView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {},
	initialize: function(){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var tmpl = '\
		<div class="hentry">\
			<div class="entry-title">\
				<h1><a href="{{url}}" rel="bookmark">{{title}}</a></h1>\
			</div>\
			<div class="author">\
				by {{author.name}}\
			</div>\
			<div class="published">\
				<abbr title="{{published}}">{{published_friendly}}</abbr>\
			</div>\
			<div class="entry-content">\
				{{{content}}}\
			</div>\
			<div class="story-tags">\
				<h3>Tags:</h3>\
				{{#has_tags}}\
				<ul class="story-tags-list">\
					{{#tags}}\
					<li class="story-tags-item"><a href="#" rel="tag">{{label}}</a></li>\
					{{/tags}}\
				</ul>\
				{{/has_tags}}\
			</div>\
		</div>\
		';
		var template_vars = this.model.toJSON();
		template_vars.has_tags = template_vars.tags.length > 0 ? true:false;
		template_vars.published_friendly = template_vars.published == null ? 'Draft' : template_vars.published.toLocaleString();
		template_vars.url = '';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
	}
});

var ArticleIndexView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {},
	initialize: function(){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var tmpl = '\
		<div>\
			<a href="#/articles/" class="new-link">Show Posts</a> | \
			<a href="#/articles/drafts" class="new-link">Show Drafts</a>\
		</div>\
		<a href="#/articles/new" class="new-link">Create New</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>Subject</th>\
					<th>Date Published</th>\
					<th>Author</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/articles/{{id}}/edit">Edit</a></td>\
					<td>{{title}}{{#sticky}} - Sticky{{/sticky}}</td>\
					<td>{{^published}}Draft{{/published}}{{#published}}{{published}}{{/published}}</td>\
					<td>{{author_name}}</td>\
				</tr>\
			{{/resources}}\
			</tbody>\
		</table>\
		';
		var template_vars = this.collection.toJSON();
		for(var i=0;i < template_vars.length; i++){
			template_vars[i].author_name = template_vars[i].author.name;
		}
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

var ArticleFormView = Backbone.View.extend({
	el: $('section#admin-content'),
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
				<label for="title">Title</label>\
				<input type="text" name="title" value="{{title}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="can_comment">Enable Comments</label>\
				<input type="checkbox" name="can_comment" value="1"{{#can_comment}} checked="checked"{{/can_comment}} />\
			</div>\
			<div class="field-n-label">\
				<label for="sticky">Make Sticky</label>\
				<input type="checkbox" name="sticky" value="1"{{#sticky}} checked="checked"{{/sticky}} />\
			</div>\
			<div class="field-n-label">\
				<label for="content">Content</label>\
				<textarea name="content" class="jquery_ckeditor">{{{content}}}</textarea>\
			</div>\
			<div class="field-n-label">\
				<label for="tags">Tags</label>\
				<input type="text" name="tags" value="{{#tags}}{{label}}, {{/tags}}" />\
			</div>\
			<input type="hidden" name="published" value="{{published}}" />\
			<input type="button" id="preview_post" value="Preview Post" />\
			<input type="submit" name="save" value="Save{{^published}} As Draft{{/published}}" />\
		</form>\
		{{^is_new}}\
		<form id="delete-form">\
			<fieldset>\
				<input type="submit" value="Delete" />\
			</fieldset>\
		</form>\
		{{/is_new}}\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
		//$("select, input:checkbox, input:radio, input:file").uniform();
	},
	save_form: function(){
		var router = this.router;
		var model = this.model;
		var field_names = ['title', 'can_comment', 'sticky', 'content', 'tags'];
		model.save({
			title: this.$('input[name="title"]').val(),
			can_comment: this.$('input[name="can_comment"]:checked').val(),
			sticky: this.$('input[name="sticky"]:checked').val(),
			content: this.$('textarea[name="content"]').val(),
			tags: this.$('input[name="tags"]').val(),
			published: this.$('input[name="published"]').val()
		},
		{
			success: function(model, response){
				console.log(response);
				console.log(model);
				router.navigate('/articles/', true);
			},
			error: function(model, response){
				console.log(response);
				console.log(model);
				if (response.status == 200 || response.status == 201){
					router.navigate('/articles/', true);
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
				router.navigate('/articles/', true);
			},
			error: function(model, response){
				console.log(response);
			}
		});
		return false;
	}
});

var ArticleCtrl = Backbone.Router.extend({
	routes: {
		"/articles/":			"index",	// #/
		"/articles/drafts":		"drafts",	// #/drafts
		"/articles/new":		"new",		// #/new
		"/articles/:id":		"show",		// #/13
		"/articles/:id/edit":	"edit"		// #/13/edit
	},
	index: function() {
		var collection = new ArticleList();
		collection.fetch({
			success: function(model, resp){
				var view = new ArticleIndexView({collection: collection});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('', true);
			}
		});
	},
	drafts: function() {
		var collection = new ArticleList();
		var router = this;
		collection.drafts = true;
		collection.fetch({
			success: function(model, resp){
				var view = new ArticleIndexView({collection: collection});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				router.navigate('', true);
			}
		});
	},
	new: function() {
		var model = new Article();
		var view = new ArticleFormView({model: model, router: this});
		view.render();
	},
	show: function(id) {
		var ctrl = this;
		var model = new Article();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new ArticleView({model: model});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/articles/', true);
			}
		});
	},
	edit: function(id) {
		var ctrl = this;
		var model = new Article();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new ArticleFormView({model: model, router: ctrl});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/articles/', true);
			}
		});
	}
});

var articles_app = new ArticleCtrl();
