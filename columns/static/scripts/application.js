user_id = {}

NavigationView = Backbone.View.extend({
	el: $('nav#admin-nav'), // attaches `this.el` to an existing element.
	events: {
		'click .login-link': 'do_login',
		'click .logout-link': 'do_logout'
//		'click #login-google': 'google_login'
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
			logged_in: _.isNumber(user_id.id) && _.isNumber(user_id.type),
			settings_access: user_id.type === 1
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
			user_id = {};
			view.render();
		});
	}
});

get_auth_data = function(){
	$.get('/auth/whoami', function(data){
		user_id = data;
		navigation_view.render();
	})
}

main_application = function(){
	articles_app.initialize();
	pages_app.initialize();
	users_app.initialize();
	uploads_app.initialize();
	navigation_view = new NavigationView();
	if(user_id.id === undefined){
		get_auth_data();
	} else {
		navigation_view.render();
	}
	Backbone.history.start({root: "/admin/#"});
}

