UserSession = Backbone.Model.extend({
	defaults: {
		id: null,
		name: '',
		type: 9,
	},
	url: '/auth/whoami',
	initialize: function(options){
		_.bindAll(this, 'logged_in', 'settings_access');
	},
	logged_in: function(){
		return _.isNumber(this.get('id')) && _.isNumber(this.get('type')) ? true : false
	},
	settings_access: function(){
		return this.get('type') === 1 ? true : false
	}
}); 

ARTICLE_LANGUAGE = {
	display_date_format: 'LLLL',
	published_format: 'L LT',
	show_posts: 'Show Posts',
	show_drafts: 'Show Drafts',
	create_new: 'Create New',
	subject_head: 'Subject',
	published_head: 'Date Published',
	author_head: 'Author',
	edit: 'Edit',
	sticky: 'Sticky',
	drafts: 'Drafts',
	previous: 'Previous',
	next: 'Next',
	fetch_error: 'Something went wrong',
	delete_error: 'Something went wrong',
	title_label: 'Title',
	sticky_label: 'Make Sticky',
	content_label: 'Content',
	tags_label: 'Tags',
	preview_button: 'Preview Post',
	publish_button: 'Publish',
	save_button: 'Save',
	save_draft_button: ' Save As Draft'
};
