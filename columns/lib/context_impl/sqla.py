import sqlahelper
from sqlalchemy import not_
from zope.interface import implements
from pyramid.util import DottedNameResolver
from ..interfaces import ICollectionContext
dotted_resolver = DottedNameResolver(None)

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
		db_session = sqlahelper.get_session()
		resource = db_session.query(
			self.__model__
		).get(id_)
		if resource is None:
			raise KeyError(key)
			
		resource.__parent__ = self
		resource.__name__ = key
		return resource
	
	def __delitem__(self, key):
		id_ = self._decode_key(key)
		db_session = sqlahelper.get_session()
		resource = db_session.query(
			self.__model__
		).get(id_)
		if resource is None:
			raise KeyError(key)
		try:
			db_session.delete(resource)
			db_session.commit()
		except: # pragma: no cover
			db_session.rollback()
			raise
	
	def __setitem__(self, key, value):
		db_session = sqlahelper.get_session()
		value.set_key(key)
		try:
			saved_resource = db_session.merge(value)
			db_session.commit()
		except: # pragma: no cover
			db_session.rollback()
			raise
		else:
			saved_resource.__name__ = saved_resource.get_key()
			return saved_resource
	
	def __len__(self):
		db_session = sqlahelper.get_session()
		return db_session.query(
			self.__model__
		).count()
	
	def __contains__(self, key):
		id_ = self._decode_key(key)
		db_session = sqlahelper.get_session()
		return db_session.query(
			self.__model__
		).get(id_) is not None
	
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
		db_session = sqlahelper.get_session()
		query = db_session.query(self.__model__)
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
		db_session = sqlahelper.get_session()
		try:
			saved_resource = db_session.merge(resource)
			db_session.commit()
		except: # pragma: no cover
			db_session.rollback()
			raise
		else:
			saved_resource.__name__ = saved_resource.get_key()
			return saved_resource
	
	def clear(self):
		db_session = sqlahelper.get_session()
		try:
			db_session.query(self.__model__).delete()
			db_session.commit()
		except: # pragma: no cover
			db_session.rollback()
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
