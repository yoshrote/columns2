# encoding: utf-8
import sqlahelper
from pyramid.httpexceptions import exception_response
from pyramid.util import DottedNameResolver
from pyramid.compat import json
from columns.lib.interfaces import IMemberContext
from columns.lib.interfaces import ICollectionContext
from columns.lib.interfaces import IResourceView
from zope.interface import implements
from zope.interface.verify import verifyClass

dotted_resolver = DottedNameResolver(None)
from sqlalchemy import not_
class InvalidResource(Exception):
	def __init__(self, form):
		self.form = form
	
	def __str__(self):
		return json.dumps(self.form.errors)
	

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
			def is_negative(value):
				return value is not None and value < 0
			
			def offset_negative(length, value):
				try:
					return length + value if int(value) <= 0 else value
				except TypeError:
					return None
			
			if is_negative(key.start) or is_negative(key.stop):
				length = len(self)
				key = slice(offset_negative(length, key.start), offset_negative(length, key.stop))
			return self.index(offset=key.start, limit=key.stop)
		id_ = self._decode_key(key)
		Session = sqlahelper.get_session()
		resource = Session.query(
			self.__model__
		).get(id_)
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
		if resource is None:
			raise KeyError(key)
		try:
			Session.delete(resource)
			Session.commit()
		except: # pragma: no cover
			Session.rollback()
			raise
	
	def __setitem__(self, key, value):
		Session = sqlahelper.get_session()
		value.set_key(key)
		try:
			saved_resource = Session.merge(value)
			Session.commit()
		except: # pragma: no cover
			Session.rollback()
			raise
		else:
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
	
	remove = __delitem__
	def discard(self, key):
		try:
			self.remove(key)
		except KeyError:
			pass
	
	def get(self, key, default=None):
		try:
			item = self.__getitem__(key)
		except KeyError:
			item = default
		return item
	
	def index(self, offset=None, limit=None, query_spec=None):
		Session = sqlahelper.get_session()
		query = Session.query(self.__model__)
		if query_spec is not None:
			query = self.build_query(query, query_spec)
		
		if 'order' in self.request.GET:
			order = self.request.GET.get('order')
			try:
				field, direction = order.split('.')
				query = query.order_by(getattr(getattr(self.__model__, field), direction)())
			except ValueError:
				query = query.order_by(getattr(self.__model__, order).asc())

		query = query.offset(offset).limit(limit)
		
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
		try:
			saved_resource = Session.merge(resource)
			Session.commit()
		except: # pragma: no cover
			Session.rollback()
			raise
		else:
			saved_resource.__name__ = saved_resource.get_key()
			return saved_resource
	
	def clear(self):
		Session = sqlahelper.get_session()
		try:
			Session.query(self.__model__).delete()
			Session.commit()
		except: # pragma: no cover
			Session.rollback()
			raise
	
	def build_query(self, query, specs):
		"parses a specs dictionary (formatted like a mongo query) into a SQLAlchemy query"
		op_map = {
			'$eq': lambda key, val: query.filter(getattr(self.__model__, key) == val),
			'$ne': lambda key, val: query.filter(getattr(self.__model__, key) != val),
			'$gt': lambda key, val: query.filter(getattr(self.__model__, key) > val),
			'$gte': lambda key, val: query.filter(getattr(self.__model__, key) >= val),
			'$lt': lambda key, val: query.filter(getattr(self.__model__, key) < val),
			'$lte': lambda key, val: query.filter(getattr(self.__model__, key) <= val),
			'$in': lambda key, val: query.filter(getattr(self.__model__, key).in_(val)),
			'$nin': lambda key, val: query.filter(not_(getattr(self.__model__, key).in_(val))),
		}
		for key in specs:
			value = specs[key]
			if isinstance(value, dict):
				for operation, op_value in value.items():
					query = op_map[operation](key, op_value)
			else:
				query = query.filter(getattr(self.__model__, key) == value)
		return query
		

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
			request_param='_method=PUT',
			permission='delete',
		)
	
	config.add_directive('add_resource', generate_routing)

