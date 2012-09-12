BaseModel = Backbone.Model.extend({
	http_url: '',
	url: function(){
		if (this.isNew()){
			return this.http_url;
		} else {
			return this.http_url + this.id;
		}
	},
	parse: function(resp, xhr) {
		if(resp.resource === undefined)
			return resp; // from a collection
		else
			return resp.resource;
	}
}); 

BaseCollection = Backbone.Collection.extend({
	model: Page,
	limit: 20,
	offset: 0,
	sort_order: 'id',
	http_url: '',
	comparator: function(page) {
		return page.get(this.sort_order);
	},
    parse : function(resp, xhr) {
      return resp.resources;
    }
	url: function(){
		return this.http_url+'?limit='+this.limit+'&offset='+this.offset+'&order='+this.sort_order;
	},
});  

PagedView = Backbone.View.extend({ 
	initialize: function(options){
		_.bindAll(this, 'render', 'prev_page', 'next_page'); // fixes loss of context for 'this' within methods
		this.router = options.router;
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

form_error_callback = function(router, model, field_names, response){
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
