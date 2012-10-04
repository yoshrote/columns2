"use strict";
var Article = Backbone.Model.extend({
	defaults: function(){
		return {
			id: null,
			title: '',
			atom_id: null,
			author_id: null,
			author_meta: {id: APP_STATE.session.get('id')},
			published: null,
			content: '',
			sticky: false,
		}
	},
	url: function(){
		if (this.isNew()){
			return '/api/articles/';
		} else {
			return '/api/articles/' + this.id;
		}
	},
	parse: function(resp, xhr) {
		if(resp.resource === undefined)
			return resp; // from a collection
		else
			return resp.resource;
	},
	initialize: function(){
		_.bindAll(this, 'can_edit', 'is_draft');
	},
	can_edit: function(sess){
		return (sess.get('type') <= 3 || sess.get('id') == this.get('author_id') || this.get('author_id') === null) ? true : false;
	},
	is_draft: function(){
		if(this.get('published') === null){
			return true;
		} else {
			return false;
		}
	}
}); 

var ArticleList = Backbone.Collection.extend({
	model: Article,
	limit: 20,
	offset: 0,
	query_spec: {},
	sort_order: 'updated.desc',
	initialize: function(){
		_.bindAll(this, 'query')
	},
	query : function(spec){
		return this.url+'&q='+encodeURIComponent(JSON.stringify(spec))
	},
	comparator: function(article) {
		return -(new Date(article.get("published")).getTime());
	},
	url: function(){
		return '/api/articles/?limit='+this.limit+'&offset='+this.offset+'&order='+this.sort_order+'&q='+encodeURIComponent(JSON.stringify(this.query_spec));
	},
    parse : function(resp, xhr) {
      return resp.resources;
    }
});  

var ArticleView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {},
	initialize: function(){
		$('section#admin-content').unbind()
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
		this.lang = options.lang;
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
		template_vars.published_friendly = this.model.is_draft() ? 'Draft' : moment(template_vars.published).format(this.lang.display_date_format);
		template_vars.url = '';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
	}
});

var ArticleIndexView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
		'click .prev-article-page': 'prev_page',
		'click .next-article-page': 'next_page'
	},
	initialize: function(options){
		$('section#admin-content').unbind()
		_.bindAll(this, 'render', 'prev_page', 'next_page'); // fixes loss of context for 'this' within methods
		this.router = options.router;
		this.lang = options.lang;
	},
	render: function(){
		var tmpl = '\
		<div>\
			<a href="#/articles/" class="new-link">{{ lang.article.show_posts }}</a> | \
			<a href="#/articles/drafts" class="new-link">{{ lang.article.show_drafts }}</a>\
		</div>\
		<a href="#/articles/new" class="new-link">{{ lang.create_new }}</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>{{ lang.article.subject_head }}</th>\
					<th>{{ lang.article.published_head }}</th>\
					<th>{{ lang.article.author_head }}</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/articles/{{id}}/edit">{{ lang.edit }}</a></td>\
					<td>{{title}}{{#sticky}} - {{ lang.article.sticky }}{{/sticky}}</td>\
					<td>{{published_friendly}}</td>\
					<td>{{author_name}}</td>\
				</tr>\
			{{/resources}}\
			</tbody>\
		</table>\
		<div>\
			<a href="#/articles/{{#drafts}}drafts{{/drafts}}" class="prev-article-page" >{{ lang.previous }}</a>\
			<a href="#/articles/{{#drafts}}drafts{{/drafts}}" class="next-article-page" >{{ lang.next }}</a>\
		</div>\
		';
		var template_vars = this.collection.toJSON();
		for(var i=0;i < template_vars.length; i++){
			template_vars[i].author_name = template_vars[i].author.name;
			template_vars[i].published_friendly = template_vars[i].published == null ? this.lang.article.drafts: moment(template_vars[i].published).format(this.lang.article.published_format);
		}
		Mustache.zebra = true;
		$(this.el).html(Mustache.render(tmpl, {
			lang: this.lang,
			resources: template_vars,
			drafts: this.collection.drafts || false,
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

var ArticleFormView = Backbone.View.extend({
	el: $('section#admin-content'),
	events: {
		'submit #save-form': 'save_form',
		'submit #delete-form': 'delete_form',
		'click #preview-post': 'show_preview',
		'click #save-publish': 'save_publish'
	},
	initialize: function(options){
		$('section#admin-content').unbind()
		_.bindAll(this, 'render', 'save_form', 'save_publish', 'delete_form', 'show_preview'); // fixes loss of context for 'this' within methods
		this.router = options.router;
		this.lang = options.lang;
	},
	render: function(){
		var template_vars = this.model.toJSON();
		template_vars.is_new = this.model.isNew();
		template_vars.can_edit = this.model.can_edit(APP_STATE.session);
		template_vars.lang = this.lang;
		var tmpl = '\
		<form id="save-form">\
			<div class="field-n-label">\
				<label for="title">{{ lang.article.title_label }}</label>\
				<input type="text" name="title" value="{{title}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="sticky">{{ lang.article.sticky_label }}</label>\
				<input type="checkbox" name="sticky" value="1"{{#sticky}} checked="checked"{{/sticky}} />\
			</div>\
			<div class="field-n-label">\
				<label for="content">{{ lang.article.content_label }}</label>\
				<textarea name="content" class="redactor">{{{content}}}</textarea>\
			</div>\
			<div class="field-n-label">\
				<label for="tags">{{ lang.article.tags }}</label>\
				<input type="text" name="tags" value="{{#tags}}{{label}}, {{/tags}}" />\
			</div>\
			<input type="hidden" name="published" value="{{published}}" />\
			<input type="button" id="preview-post" value="{{ lang.article.preview_button }}" class="form-submit-left"/>\
		{{#can_edit}}\
			<input type="submit" name="save" value="{{#published}}{{ lang.save_button }}{{/published}}{{^published}}{{ lang.article.save_draft_button }}{{/published}}"  class="form-submit-left"/>\
			{{^published}}<input type="button" name="save-publish" id="save-publish" value="{{ lang.article.publish_button }}" class="form-submit-left"/>{{/published}}\
		</form>\
		{{^is_new}}\
		<form id="delete-form">\
			<div>\
				<input type="submit" value="{{ lang.delete_button }}" class="form-submit-right"/>\
			</div>\
		</form>\
		{{/is_new}}\
		{{/can_edit}}\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
		$(".redactor").redactor({ fixed: true, imageUpload: '/api/imageupload' });
	},
	save_publish: function(){
		$('input[name="published"]').val(moment.utc().format('YYYY-MM-DDTHH:mm:ss\\Z'));
		this.save_form();
	},
	save_form: function(){
		var router = this.router;
		var model = this.model;
		var field_names = ['title', 'sticky', 'content', 'tags'];
		model.save({
			title: this.$('input[name="title"]').val(),
			sticky: this.$('input[name="sticky"]:checked').val(),
			content: this.$('textarea[name="content"]').val(),
			tags: this.$('input[name="tags"]').val(),
			published: this.$('input[name="published"]').val()
		},
		{
			success: function(model, response){
				router.navigate('//articles/', true);
			},
			error: function(model, response){
				if (response.status == 200 || response.status == 201){
					router.navigate('//articles/', true);
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
				router.navigate('//articles/', true);
			},
			error: function(model, response){
				console.log(model);
				console.log(response);
			}
		});
		return false;
	},
	show_preview: function(){
		var tmpl = '\
		<html><head><link href="{{base_static_url}}/stylesheets/styles.css" media="screen" rel="stylesheet" type="text/css">\
		</head><body>\
		<section id="top-content">\
		<article class="story-container hentry">\
			<h2 class="story-title entry-title">\
				<a href="#" rel="bookmark">{{ title }}</a>\
			</h2>\
			<div class="story-content entry-content">\
				{{{ content }}}\
			</div>\
		</article>\
		</section>\
		</body></html>';

		var preview = window.open('');
		preview.document.write(Mustache.to_html(tmpl, {
			title: this.$('input[name="title"]').val(),
			content: this.$('textarea[name="content"]').val(),
			base_static_url: APP_STATE.base_static_url
		}))
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
	initialize: function(options){
		_.bindAll(this, 'index', 'edit', 'new', 'show', 'drafts'); // fixes loss of context for 'this' within methods
		this.lang = APP_STATE.lang;
	},
	index: function() {
		var collection = new ArticleList();
		collection.query_spec = {'published': {'$ne': null}};
		var router = this;
		collection.fetch({
			success: function(model, resp){
				var view = new ArticleIndexView({collection: collection, router: router, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('', true);
			}
		});
	},
	drafts: function() {
		var collection = new ArticleList();
		var router = this;
		collection.query_spec = {'published': null};
		collection.fetch({
			success: function(model, resp){
				var view = new ArticleIndexView({collection: collection, router: router, lang: router.lang});
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
		var model = new Article();
		var view = new ArticleFormView({model: model, router: router, lang: router.lang});
		view.render();
	},
	show: function(id) {
		var router = this;
		var model = new Article();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new ArticleView({model: model, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('//articles/', true);
			}
		});
	},
	edit: function(id) {
		var router = this;
		var model = new Article();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new ArticleFormView({model: model, router: router, lang: router.lang});
				view.render();
			},
			error: function(model, options){
				alert(router.lang.fetch_error);
				router.navigate('//articles/', true);
			}
		});
	}
});
