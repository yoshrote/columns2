# encoding: utf-8
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.static import static_view
from pyramid.util import DottedNameResolver

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


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_beaker')
    dotted_resolver = DottedNameResolver(None)
    setup_models = dotted_resolver.maybe_resolve(settings['models.setup'])
    config.registry['models.module'] = dotted_resolver.maybe_resolve(settings['models.module'])
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
    config.include(setup_resource_routes, route_prefix='api')
    #config.include('columns.blog')
    return config.make_wsgi_app()

