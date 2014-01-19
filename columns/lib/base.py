# encoding: utf-8
from pyramid.httpexceptions import exception_response
from pyramid.util import DottedNameResolver
from pyramid.compat import json
from columns.lib.interfaces import IMemberContext
from columns.lib.interfaces import ICollectionContext
from columns.lib.interfaces import IResourceView
from zope.interface import implements
from zope.interface.verify import verifyClass

dotted_resolver = DottedNameResolver(None)
class InvalidResource(Exception):
    def __init__(self, form):
        self.form = form
    
    def __str__(self):
        return json.dumps(self.form.errors)
    

class BaseViews(object):
    implements(IResourceView)
    def __init__(self, context, request):
        self.request = request
        self.context = context
    
    # private methods to extract data from request and validate
    def _create_values_from_request(self): # pragma: no cover
        raise NotImplementedError
    
    def _update_values_from_request(self): # pragma: no cover
        raise NotImplementedError
    
    # collection views
    def index(self):
        def int_or_none(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return None
        
        offset = int_or_none(self.request.GET.get('offset'))
        limit = int_or_none(self.request.GET.get('limit'))
        query_spec = json.loads(self.request.GET.get('q', '{}'))
        
        resources = self.context.index(limit=limit, offset=offset, query_spec=query_spec)
        return {
            'context': self.context, 
            'resources': resources, 
            'offset': offset, 
            'limit': limit
        }
    
    def create(self):
        try:
            values = self._create_values_from_request()
        except InvalidResource, ex:
            raise exception_response(
                400,
                body=unicode(ex),
            )
        except NotImplementedError: # pragma: no cover
            raise exception_response(501)
        else:
            new_resource = self.context.new()
            new_resource = new_resource.build_from_values(values)
            resource = self.context.add(new_resource)
            raise exception_response(
                201,
                location=self.request.resource_url(resource)
            )
    
    def new(self):
        new_resource = self.context.new()
        return {'context':self.context, 'resource': new_resource}
    
    
    # member views
    def show(self):
        return {'resource': self.context}
    
    def update(self):
        collection = self.context.__parent__
        try:
            values = self._update_values_from_request()
        except NotImplementedError: # pragma: no cover
            raise exception_response(501)
        except InvalidResource, ex:
            raise exception_response(
                400,
                body=unicode(ex)
            )
        else:
            self.context.update_from_values(values)
            collection[self.context.__name__] = self.context
            
            raise exception_response(
                200,
                location=self.request.resource_url(self.context)
            )
    
    def delete(self):
        collection = self.context.__parent__
        del collection[self.context.__name__]
        raise exception_response(200, body='{}')
    
def includeme(config):
    def generate_routing(config, collection, view_class_name, collection_factory, collection_context, member_context):
        PATH_PREFIX = config.route_prefix
        def resource_url(self, request, info):
            return '/'.join([
                '',
                PATH_PREFIX,
                info['virtual_path']
            ]).replace('//', '/')
        
        collection_class = dotted_resolver.maybe_resolve(collection_context)
        member_class = dotted_resolver.maybe_resolve(member_context)
        view_class = dotted_resolver.maybe_resolve(view_class_name)
        
        if not verifyClass(ICollectionContext, collection_class): # pragma: no cover
            raise TypeError(
                "%s does not implement ICollectionContext",
                 collection_context
            )
        
        if not verifyClass(IMemberContext, member_class): # pragma: no cover
            raise TypeError(
                "%s does not implement IMemberContext",
                 collection_context
            )
        
        if not verifyClass(IResourceView, view_class): # pragma: no cover
            raise TypeError(
                "%s does not implement IResourceView",
                 view_class_name
            )
        
        setattr(collection_class, '__resource_url__', resource_url)
        setattr(member_class, '__resource_url__', resource_url)
        #base route
        config.add_route(
            collection, 
            '{0}/*traverse'.format(collection),
            factory=collection_factory,
        )
        
        #index (json)
        config.add_view(
            route_name=collection,
            context=collection_context,
            name='',
            view=view_class,
            attr='index',
            accept='application/json',
            request_method='GET',
            renderer='json',
            permission='index',
        )
        
        #new (json)
        config.add_view(
            route_name=collection,
            context=collection_context,
            name='new',
            view=view_class,
            attr='new',
            accept='application/json',
            request_method='GET',
            renderer='json',
            permission='new',
        )
        
        #show (json)
        config.add_view(
            route_name=collection,
            context=member_context,
            name='',
            view=view_class,
            attr='show',
            accept='application/json',
            request_method='GET',
            renderer='json',
            permission='show',
        )
        
        #create (x-form-urlencoded)
        config.add_view(
            route_name=collection,
            context=collection_context,
            name='',
            view=view_class,
            attr='create',
            request_method='POST',
            permission='create',
        )
        
        #update (x-form-urlencoded)
        config.add_view(
            route_name=collection,
            context=member_context,
            name='',
            view=view_class,
            attr='update',
            request_method='PUT',
            permission='update',
        )
        #update (x-form-urlencoded w/ browser fakeout)
        config.add_view(
            route_name=collection,
            context=member_context,
            name='',
            view=view_class,
            attr='update',
            request_method='POST',
            request_param='_method=PUT',
            permission='update',
        )
        
        #delete (x-form-urlencoded)
        config.add_view(
            route_name=collection,
            context=member_context,
            name='',
            view=view_class,
            attr='delete',
            request_method='DELETE',
            permission='delete',
        )
        #delete (x-form-urlencoded w/ browser fakeout)
        config.add_view(
            route_name=collection,
            context=member_context,
            name='',
            view=view_class,
            attr='delete',
            request_method='POST',
            request_param='_method=DELETE',
            permission='delete',
        )

    
    config.add_directive('add_resource', generate_routing)

