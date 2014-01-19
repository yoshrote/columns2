# encoding: utf-8
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.static import static_view
from .models import setup_models

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
    config.add_route('admin', '/')
    config.add_view(
        renderer='columns:templates/admin.jinja',
        route_name='admin',
    )
    config.add_route('admin_no_slash', '')
    config.add_view(
        'columns.views.admin_no_slash_view',
        route_name='admin_no_slash',
    )
    
    config.add_route('settings', '/settings')
    config.add_view(
        'columns.views.settings_view',
        route_name='settings',
        permission='admin'
    )
    
    config.add_route('settings_edit', '/settings/:module/edit')
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
    
    
    config.add_route('wysiwyg_imageupload', '/imageupload')
    config.add_view(
        'columns.views.imageupload',
        route_name='wysiwyg_imageupload',
        renderer='json',
        permission='admin',
    )

#def setup_app_routes(config):
#   config.add_route('app', '/')
#   config.add_view(
#       renderer='columns:templates/app.jinja',
#       route_name='app',
#   )
#   config.add_route('app_no_slash', '')
#   config.add_view(
#       'columns.views.app_no_slash_view',
#       route_name='app_no_slash',
#   )

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_beaker')
    setup_models(config)
    session_factory = session_factory_from_settings(settings)
    static_path = settings.get('static_path', 'static')
    config.add_static_view(static_path, settings.get('static_directory'))
    config.add_route('favicon.ico', 'favicon.ico')
    config.add_view(
        static_view(''.join([settings.get('static_directory'), 'favicon.ico']), index='', use_subpath=True),
        route_name='favicon.ico'
    )
    config.set_session_factory(session_factory)
    config.include('columns.lib.view')
    config.include('columns.auth', route_prefix='auth')
    config.include(setup_admin_routes, route_prefix='admin')
    config.include(setup_resource_routes, route_prefix='api')
    #config.include(setup_app_routes, route_prefix='app')
    config.include('columns.blog')
    return config.make_wsgi_app()

