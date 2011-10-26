# encoding: utf-8
import sqlahelper
from pyramid.httpexceptions import exception_response
from pyramid.util import DottedNameResolver
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
		err_list = [
			': '.join([k,';'.join(self.form.errors_for(k))]) 
			for k in self.form.errors
		]
			
		return '\n'.join(err_list)
	

class SQLACollectionContext(object):
	implements(ICollectionContext)
	collection_views = ['', 'index', 'new', 'create']
	__parent__ = None
	__name__ = None
	__model__ = None
	def to_json(self):
		return None
	
	def __init__(self, request, *args, **kwargs):
		self.__model__ = dotted_resolver.maybe_resolve(self.__model__)
		self.request = request
	
	def _decode_key(self, key):
		try:
			return int(key)
		except (TypeError, ValueError):
			raise KeyError(key)
	
	
	def __getitem__(self, key):
		if key in self.collection_views:
			raise KeyError(key)
		if isinstance(key, slice):
			return self.index(offset=key.start, limit=key.stop)
		id = self._decode_key(key)
		Session = sqlahelper.get_session()
		resource = Session.query(
			self.__model__
		).get(id)
		if resource is None:
			raise KeyError(key)
			
		resource.__parent__ = self
		resource.__name__ = key
		return resource
	
	def __delitem__(self, key):
		id = self._decode_key(key)
		Session = sqlahelper.get_session()
		resource = Session.query(
			self.__model__
		).get(id)
		Session.delete(resource)
		Session.commit()
	
	def __setitem__(self, key, value):
		Session = sqlahelper.get_session()
		value = value.set_key(key)
		saved_resource = Session.merge(value)
		Session.commit()
		saved_resource.__name__ = saved_resource.get_key()
		return saved_resource
	
	def __len__(self):
		Session = sqlahelper.get_session()
		return Session.query(
			self.__model__
		).count()
	
	def __contains__(self, key):
		id = self._decode_key(key)
		Session = sqlahelper.get_session()
		return Session.query(
			self.__model__
		).get(id) is not None
	
	def get(self, key, default=None):
		try:
			item = self.__getitem__(key)
		except KeyError:
			item = default
		return item
	
	def index(self, offset=None, limit=None):
		Session = sqlahelper.get_session()
		query = Session.query(self.__model__).\
			offset(offset).\
			limit(limit)
		
		results = []
		for item in query:
			item.__parent__ = self
			item.__name__ = item.get_key()
			results.append(item)
		
		return results
	
	def new(self):
		resource = self.__model__()
		resource.__parent__ = self
		return resource
	
	def add(self, resource):
		Session = sqlahelper.get_session()
		saved_resource = Session.merge(resource)
		Session.commit()
		saved_resource.__name__ = saved_resource.get_key()
		return saved_resource
	

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
	
	def _create_values_from_atom(self): # pragma: no cover
		raise NotImplementedError
	
	def _update_values_from_atom(self): # pragma: no cover
		raise NotImplementedError
	
	
	# collection views
	def index(self):
		def int_or_none(val):
			try:
				return int(val)
			except (TypeError,ValueError):
				return None
		
		offset = int_or_none(self.request.GET.get('offset'))
		limit = int_or_none(self.request.GET.get('limit'))
		resources = self.context.index(limit=limit,offset=offset)
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
				detail=str(ex)
			)
		except NotImplementedError: # pragma: no cover
			raise exception_reponse(501)
		else:
			new_resource = self.context.new()
			new_resource = new_resource.build_from_values(values)
			resource = self.context.add(new_resource)
			raise exception_response(
				201,
				location=self.request.resource_url(resource)
			)
	
	def create_atom(self):
		try:
			values = self._create_values_from_atom()
		except NotImplementedError: # pragma: no cover
			raise exception_reponse(501)
		except InvalidResource, ex:
			raise exception_response(
				400,
				detail=unicode(ex)
			)
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
			raise exception_reponse(501)
		except InvalidResource, ex:
			raise exception_response(
				400,
				detail=unicode(ex)
			)
		else:
			self.context = self.context.update_from_values(values)
			collection[self.context.__name__] = self.context
			
			raise exception_response(
				200,
				location=self.request.resource_url(self.context)
			)
	
	def update_atom(self):
		collection = self.context.__parent__
		try:
			values = self._update_values_from_atom()
		except InvalidResource, ex:
			raise exception_response(
				400,
				detail=unicode(ex)
			)
		except NotImplementedError: # pragma: no cover
			raise exception_reponse(501)
		else:
			self.context = self.context.update_from_values(values)
			collection[self.context.__name__] = self.context
			
			raise exception_response(
				200,
				location=self.request.resource_url(self.context)
			)
	
	def delete(self):
		collection = self.context.__parent__
		collection_name = collection.__name__
		del collection[self.context.__name__]
		raise exception_response(200)
	


def includeme(config):
	def generate_routing(config, collection, view_class_name, collection_factory, collection_context, member_context):
		PATH_PREFIX = config.route_prefix
		def resource_url(self, request, info):
			return '/'.join([
				'',
				PATH_PREFIX,
				info['virtual_path']
			]).replace('//','/')
		
		collection_class = dotted_resolver.maybe_resolve(collection_context)
		member_class = dotted_resolver.maybe_resolve(member_context)
		view_class = dotted_resolver.maybe_resolve(view_class_name)
		
		if not verifyClass(collection_class, ICollectionContext):
			raise TypeError(
				"%s does not implement ICollectionContext",
				 collection_context
			)
		
		if not verifyClass(member_class, IMemberContext):
			raise TypeError(
				"%s does not implement IMemberContext",
				 collection_context
			)
		
		if not verifyClass(view_class, IResourceView):
			raise TypeError(
				"%s does not implement IResourceView",
				 view_class_name
			)
		
		setattr(collection_class,'__resource_url__',resource_url)
		setattr(member_class,'__resource_url__',resource_url)
		#base route
		config.add_route(
			collection, 
			'{0}/*traverse'.format(collection),
			factory=collection_factory,
		)
		
		#index (html)
		config.add_view(
			route_name=collection,
			context=collection_context,
			name='',
			view=view_class,
			attr='index',
			accept='text/html',
			request_method='GET',
			renderer='columns:templates/{0}/index.jinja'.format(collection)
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
			renderer='json'
		)
		#index (atom)
		config.add_view(
			route_name=collection,
			context=collection_context,
			name='',
			view=view_class,
			attr='index',
			accept='application/atom+xml', #[does_accept_atom],
			request_method='GET',
			renderer='columns:templates/{0}/index.atom.jinja'.format(
				collection
			)
		)
		
		#new (html)
		config.add_view(
			route_name=collection,
			context=collection_context,
			name='new',
			view=view_class,
			attr='new',
			request_method='GET',
			renderer='columns:templates/{0}/new.jinja'.format(collection)
		)
		
		#show (html)
		config.add_view(
			route_name=collection,
			context=member_context,
			name='',
			view=view_class,
			attr='show',
			accept='text/html',
			request_method='GET',
			renderer='columns:templates/{0}/show.jinja'.format(collection)
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
			renderer='json'
		)
		#show (atom)
		config.add_view(
			route_name=collection,
			context=member_context,
			name='',
			view=view_class,
			attr='show',
			accept='application/atom+xml', #[does_accept_atom],
			request_method='GET',
			renderer='columns:templates/{0}/show.atom.jinja'.format(
				collection
			)
		)
		
		#edit (html)
		config.add_view(
			route_name=collection,
			context=member_context,
			name='edit',
			view=view_class,
			attr='show',
			request_method='GET',
			renderer='columns:templates/{0}/edit.jinja'.format(collection)
		)
		
		#create (x-form-urlencoded)
		config.add_view(
			route_name=collection,
			context=collection_context,
			name='',
			view=view_class,
			attr='create',
			request_method='POST',
		)
		#create (atom)
		config.add_view(
			route_name=collection,
			context=collection_context,
			name='',
			view=view_class,
			attr='create_atom',
			custom_predicates=[
				lambda ctxt,req: 'atom' in req.content_type
			],
			request_method='POST',
		)
		
		#update (x-form-urlencoded)
		config.add_view(
			route_name=collection,
			context=member_context,
			name='',
			view=view_class,
			attr='update',
			request_method='PUT',
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
		)
		#update (atom)
		config.add_view(
			route_name=collection,
			context=member_context,
			name='',
			view=view_class,
			attr='update_atom',
			custom_predicates=[
				lambda ctxt,req: 'atom' in req.content_type
			],
			request_method='PUT',
		)
		
		#delete (x-form-urlencoded)
		config.add_view(
			route_name=collection,
			context=member_context,
			name='',
			view=view_class,
			attr='delete',
			request_method='DELETE',
		)
		#delete (x-form-urlencoded w/ browser fakeout)
		config.add_view(
			route_name=collection,
			context=member_context,
			name='',
			view=view_class,
			attr='delete',
			request_method='POST',
			request_param='_method=PUT',
		)
	
	config.add_directive('add_resource', generate_routing)


"""
class BaseMemberContext(object):
	def get_key(self):
		return unicode(self.id)
	
	def update_from_values(self, values):
		for k,v in values.items():
			if not k.startswith('_') and hasattr(self, k):
				setattr(self, k, v)
		
		return self
	
	def build_from_values(self, values):
		return self.update_from_values(values)
	

"""