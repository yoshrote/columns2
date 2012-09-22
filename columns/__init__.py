# encoding: utf-8
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.static import static_view
from sqlalchemy import engine_from_config
import sqlahelper

def setup_resource_routes(config):
	config.include('columns.lib.base')
	config.add_resource(
		'articles',
		'columns.contexts:ArticleViews',
		'columns.contexts.ArticleContextFactory',
		'columns.contexts:ArticleCollectionContext',
		'columns.models:Article',
	)
	config.add_resource(
		'pages',
		'columns.contexts:PageViews',
		'columns.contexts.PageContextFactory',
		'columns.contexts:PageCollectionContext',
		'columns.models:Page',
	)
	config.add_resource(
		'uploads',
		'columns.contexts:UploadViews',
		'columns.contexts.UploadContextFactory',
		'columns.contexts:UploadCollectionContext',
		'columns.models:Upload',
	)
	config.add_resource(
		'users',
		'columns.contexts:UserViews',
		'columns.contexts.UserContextFactory',
		'columns.contexts:UserCollectionContext',
		'columns.models:User',
	)

def setup_admin_routes(config):
	config.add_route('admin', '/admin/')
	config.add_view(
		'columns.views.admin_view',
		route_name='admin',
		permission='admin',
	)
	config.add_route('admin_no_slash', '/admin')
	config.add_view(
		'columns.views.admin_no_slash_view',
		route_name='admin_no_slash',
		permission='admin',
	)
	
	config.add_route('settings', '/admin/settings')
	config.add_view(
		'columns.views.settings_view',
		route_name='settings',
		permission='admin'
	)
	
	config.add_route('settings_edit', '/admin/settings/:module/edit')
	config.add_view(
		'columns.views.settings_edit_view',
		request_method='GET',
		route_name='settings_edit',
		permission='admin',
	)
	config.add_view(
		'columns.views.settings_save',
		request_method='POST',
		route_name='settings_edit',
		permission='admin',
	)
	
	
	config.add_route('browse_images', '/admin/browse_images')
	config.add_view(
		'columns.views.browse_images_view',
		route_name='browse_images',
		permission='admin',
	)
	config.add_route('browse_images_ajax', '/admin/browse_images_ajax')
	config.add_view(
		'columns.views.browse_images_ajax',
		route_name='browse_images_ajax',
		renderer='json',
		permission='admin',
	)
	config.add_route('wysiwyg_imageupload', '/api/imageupload')
	config.add_view(
		'columns.views.imageupload',
		route_name='wysiwyg_imageupload',
		renderer='json',
		permission='admin',
	)


def main(global_config, **settings):
	""" This function returns a Pyramid WSGI application.
	"""
	if settings.get('test_engine'):
		from columns.tests import _initTestingDB
		_initTestingDB()
	else: # pragma: no cover
		engine = engine_from_config(settings, 'sqlalchemy.')
		sqlahelper.add_engine(engine)
		sqlahelper.get_session().configure(extension=None)
	config = Configurator(settings=settings)
	config.include('pyramid_beaker')
	session_factory = session_factory_from_settings(settings)
	config.add_static_view('static', settings.get('static_directory'))
	config.add_route('favicon.ico', 'favicon.ico')
	config.add_view(
		static_view(''.join([settings.get('static_directory'),'favicon.ico']), index='', use_subpath=True),
		route_name='favicon.ico'
	)
	config.set_session_factory(session_factory)
	config.include('columns.lib.view')
	config.include('columns.blog')
	config.include('columns.auth', route_prefix='auth')
	config.include(setup_admin_routes)
	config.include(setup_resource_routes, route_prefix='api')
	return config.make_wsgi_app()

