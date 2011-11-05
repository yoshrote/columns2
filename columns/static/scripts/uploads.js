
var Upload = Backbone.Model.extend({
	defaults: {
		title: '',
		content: ''
	},
	parse : function(resp, xhr) {
		return resp.resource;
	}
});      
var UploadList = Backbone.Collection.extend({
	model: Upload,
	url: '/api/uploads/',
    parse : function(resp, xhr) {
      return resp.resources;
    }
});  

var UploadView = Backbone.View.extend({ 
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(){
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
	},
	initialize: function(){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var tmpl = '\
		<a href="#/uploads/new" class="new-link">Create New</a>\
		<table id="admin-resource-list">\
			<thead>\
				<tr>\
					<td class="filler-cell">&nbsp;</td>\
					<th>Filename</th>\
					<th>Date</th>\
				</tr>\
			</thead>\
			<tbody>\
			{{#resources}}\
				<tr class="{{zebra}}">\
					<td><a href="#/uploads/{{id}}/edit">Edit</a></td>\
					<td><a href="{{static_base}}{{filepath}}" target="blank_">{{title}}</a></td>\
					<td class="datetime-container">{{updated}}</td>\
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

var UploadNewFormView = Backbone.View.extend({
	el: $('section#admin-content'), // attaches `this.el` to an existing element.
	events: {
	},
	initialize: function(options){
		_.bindAll(this, 'render'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var template_vars = this.model.toJSON();
		var tmpl = '\
		<form id="new-form">\
			<div class="field-n-label">\
				<label for="upload">File</label>\
				<input type="file" name="upload" />\
			</div>\
			<div class="field-n-label">\
				<label for="title">Alternative Text</label>\
				<input type="text" name="title" value="{{title}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="content">Description</label>\
				<textarea name="content">{{content}}</textarea>\
			</div>\
			<input type="submit" name="save" value="Save" />\
		</form>\
		';
		$(this.el).html(Mustache.to_html(tmpl, template_vars));
		$("select, input:checkbox, input:radio, input:file").uniform();
	}
});

var UploadEditFormView = Backbone.View.extend({
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
				<label for="title">Alternative Text</label>\
				<input type="text" name="title" value="{{title}}" />\
			</div>\
			<div class="field-n-label">\
				<label for="content">Description</label>\
				<textarea name="content">{{content}}</textarea>\
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

var UploadCtrl = Backbone.Router.extend({
	routes: {
		"/uploads/":			"index",	// #/
		"/uploads/index":		"index",	// #/index
		"/uploads/new":			"new",		// #/new
		"/uploads/:id":			"show",		// #/13
		"/uploads/:id/edit":	"edit"		// #/13/edit
	},
	index: function() {
		var collection = new UploadList();
		collection.fetch({
			success: function(model, resp){
				var view = new UploadIndexView({collection: collection});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('', true);
			}
		});
	},
	new: function() {
		var model = new Upload();
		var view = new UploadNewFormView({model: model});
		view.render();
	},
	show: function(id) {
		var ctrl = this;
		var model = new Upload();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UploadView({model: model});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/uploads/', true);
			}
		});
	},
	edit: function(id) {
		var ctrl = this;
		var model = new Upload();
		model.set({id: id});
		model.fetch({
			success: function(model, resp){
				var view = new UploadNewFormView({model: model});
				view.render();
			},
			error: function(model, options){
				alert('Something went wrong');
				ctrl.navigate('/uploads/', true);
			}
		});
	}
});

var uploads_app = new UploadCtrl();

