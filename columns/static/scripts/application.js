NavigationView = Backbone.View.extend({
	el: $('nav#admin-nav'), // attaches `this.el` to an existing element.
	events: {
		'click .login-link': 'do_login',
		'click .logout-link': 'do_logout'
		//'click #login-google': 'google_login'
	},
	initialize: function(options){
		_.bindAll(this, 'render', 'do_login', 'do_logout', 'google_login'); // fixes loss of context for 'this' within methods
	},
	render: function(){
		var view = this;
		var tmpl = '\
		<a href="/admin/#/articles/" data-nav-name="articles" class="nav-link" title="Articles">Articles</a>\
		<a href="/admin/#/pages/" data-nav-name="pages" class="nav-link" title="Pages">Pages</a>\
		<a href="/admin/#/uploads/" data-nav-name="uploads" class="nav-link" title="Uploads">Uploads</a>\
		<a href="/admin/#/users/" data-nav-name="users" class="nav-link" title="Users">Users</a>\
		{{#settings_access}}\
		<a href="/admin/#/settings/" data-nav-name="settings" class="nav-link" title="Settings">Settings</a>\
		{{/settings_access}}\
		{{^logged_in}}\
		<button class="auth-btn login-link">Login</button>\
		<div id="login-dialog">\
		<ul>\
			<li><button id="login-google">Google</button></li>\
			<li>\
				<form id="login-form" action="/auth/openid">\
					<div>\
					<input type="submit" value="OpenID"></input>\
					<input type="text" name="openid" id="openid"></input>\
					</div>\
				</form>\
			</li>\
		</ul>\
		</div>\
		</div>\
		{{/logged_in}}\
		{{#logged_in}}<button class="auth-btn logout-link">Logout</button>{{/logged_in}}\
		';
		$(this.el).html(Mustache.to_html(tmpl, {
			logged_in: APP_STATE.session.logged_in(),
			settings_access: APP_STATE.session.settings_access()
		}));
		$("#login-dialog button, #login-dialog input[type='submit']").button();

		$('#login-google').click(function(){
			view.google_login();
		})
		$('#login-dialog').dialog({
			title: 'Login',
			autoOpen: false,
			modal: true,
			resizable: false,
			draggable: false,
			width: 500,
		});
	},
	do_login: function(){
		$('#login-dialog').dialog('open');
	},
	google_login: function(){
		$('input#openid').val('https://www.google.com/accounts/o8/id');
		$('form#login-form').submit();
	},
	do_logout: function(){
		var view = this;
		$.get('/auth/logout', function(){
			APP_STATE.session.clear(APP_STATE.session.defaults)
			window.location = '/admin/';
		});
	}
});

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

APP_STATE = {
	lang: {
		display_date_format: 'LLLL',
		create_new: 'Create New',
		edit: 'Edit',
		previous: 'Previous',
		next: 'Next',
		true: 'True',
		false: 'False',
		fetch_error: 'Something went wrong',
		delete_error: 'Something went wrong',
		article:{
			show_posts: 'Show Posts',
			show_drafts: 'Show Drafts',
			save_button: 'Save',
			delete_button: 'Delete',
			published_format: 'L LT',
			drafts: 'Drafts',
			preview_button: 'Preview Post',
			publish_button: 'Publish',
			save_draft_button: ' Save As Draft',
			subject_head: 'Subject',
			published_head: 'Date Published',
			author_head: 'Author',
			sticky: 'Sticky',
			title_label: 'Title',
			sticky_label: 'Make Sticky',
			content_label: 'Content',
			tags_label: 'Tags',
		},
		page:{
			name_head: 'Name',
			visible_head: 'Visible',
			in_main_head: 'In Main Feed',
			title_label: 'Page Title',
			visible_label: 'Is Visible',
			can_post_label: 'Enable Posts',
			in_menu_label: 'Show Page in Menu',
			in_main_label: 'Show Posts in Main Stream'
			save_button: 'Save',
			delete_button: 'Delete',
		},
		user:{
			name_head: 'Name',
			type_head: 'Type',
			name_label: 'Name',
			type_label: 'User Type',
			open_id_label: 'OpenID URL',
			profile_label: 'Profile URL',
			save_button: 'Save',
			delete_button: 'Delete',
		}
	},
	session: null
}

main_application = function(){
	$('body').append('<div class="loading-modal"></div>');
	$("body").on({
		ajaxStart: function() { 
			$(this).addClass("loading"); 
		},
		ajaxStop: function() { 
			$(this).removeClass("loading"); 
		}
	});
	APP_STATE.session = new UserSession();
	navigation_view = null;
	APP_STATE.session.fetch().complete(function(){
		navigation_view = new NavigationView();
		navigation_view.render();
		articles_app = new ArticleCtrl();
		pages_app = new PageCtrl();
		users_app = new UserCtrl();
		uploads_app = new UploadCtrl();
		Backbone.history.start({root: "/admin/#"});
	});
}
