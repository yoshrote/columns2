import sqlahelper
import logging
from sqlalchemy import not_
from sqlalchemy import engine_from_config
from sqlalchemy.exc import SQLAlchemyError
from zope.interface import implements
from pyramid.util import DottedNameResolver
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.authentication import CallbackAuthenticationPolicy
from ..interfaces import ICollectionContext
from ...auth import DEFAULT_USER_TYPE
from ...auth import PERMISSIONS
from ...auth import get_permissions
from ...models import User
import os.path
import os

dotted_resolver = DottedNameResolver(None)
LOG = logging.getLogger(__name__)

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

class SessionAuthenticationPolicy(CallbackAuthenticationPolicy):
    implements(IAuthenticationPolicy)
    def __init__(self, prefix='auth.', debug=False):
        self.prefix = prefix or ''
        self.userid_key = prefix + 'userid'
        self.debug = debug
    
    def callback(self, userid, request):
        dbsession = sqlahelper.get_session()
        principals = [userid]
        auth_type = request.session.get('auth.type')
        #load user into cache
        if not auth_type:
            request.session[self.userid_key] = userid
            user = dbsession.query(User).get(userid)
            if user is None:
                return principals
            request.session['auth.type'] = auth_type = user.type
        
        # add in principles according to session stored variables
        inv_permission = get_permissions()
        principals.append(inv_permission.get(request.session['auth.type'], DEFAULT_USER_TYPE))
        LOG.debug('User principals: %r', principals)
        return principals
    
    def remember(self, request, principal, **kw):
        """ Store a principal in the session."""
        auth_type = request.session.get('auth.type')
        #load user into cache
        LOG.debug('auth_type = %r', auth_type)
        if not auth_type:
            user = find_user('id', principal, request)
            if isinstance(user, User):
                request.session[self.userid_key] = principal
                request.session['auth.type'] = user.type
                request.session['auth.name'] = user.name
            LOG.debug('session info: %r', request.session)
        return []
    
    def forget(self, request):
        """ Remove the stored principal from the session."""
        for key in request.session.keys():
            if key.startswith(self.prefix):
                del request.session[key]
        return []
    
    def unauthenticated_userid(self, request):
        return request.session.get(self.userid_key)

def setup_models(config):
    engine = engine_from_config(config.registry.settings, 'sqlalchemy.')
    Base = dotted_resolver.maybe_resolve(config.registry.settings['models.module']).Base
    sqlahelper.add_engine(engine)
    sqlahelper.get_session().configure(extension=None)
    Base.metadata.create_all(engine, checkfirst=True)
    config.add_subscriber(db_session_request, 'pyramid.events.NewRequest')

def db_session_request(event):
    session = sqlahelper.get_session()
    def cleanup(_):
        try:
            session.rollback()
        except: # pragma: no cover
            pass
    event.request.add_finished_callback(cleanup)
    return session

def find_user(attribute, value, request):
    dbsession = sqlahelper.get_session()
    try:
        LOG.debug('Looking for user where %s=%r', attribute, value)
        user = dbsession.query(User).filter(getattr(User, attribute)==value).one()
    except SQLAlchemyError:
        dbsession.rollback()
        return None
    else:
        LOG.debug('User found: %r', user.name)
    return user

########################################
## Context Factory Functions
########################################
def ArticleContextFactory(request):
    return ArticleCollectionContext(request)

def PageContextFactory(request):
    return PageCollectionContext(request)

def UploadContextFactory(request):
    return UploadCollectionContext(request)

def UserContextFactory(request):
    return UserCollectionContext(request)

########################################
## Collection Contexts
########################################
class ArticleCollectionContext(SQLACollectionContext):
    __model__ = 'columns.models:Article'
    __name__ = 'articles'

class PageCollectionContext(SQLACollectionContext):
    __model__ = 'columns.models:Page'
    __name__ = 'pages'

class UploadCollectionContext(SQLACollectionContext):
    __model__ = 'columns.models:Upload'
    __name__ = 'uploads'
    
    def __delitem__(self, key):
        id_ = self._decode_key(key)
        Session = sqlahelper.get_session()
        resource = Session.query(
            self.__model__
        ).get(id_)
        if resource is None:
            raise KeyError(key)
        basepath = self.request.registry.settings.get('upload_basepath')
        resource_path = os.path.join(basepath, resource.filepath)
        Session.delete(resource)
        Session.commit()
        os.remove(resource_path)

class UserCollectionContext(SQLACollectionContext):
    __model__ = 'columns.models:User'
    __name__ = 'users'

def setup_resource_routes(config):
    config.add_resource(
        'articles',
        'columns.views:ArticleViews',
        'columns.lib.context_impl.sqla:ArticleContextFactory',
        'columns.lib.context_impl.sqla:ArticleCollectionContext',
        'columns.models:Article',
    )
    config.add_resource(
        'pages',
        'columns.views:PageViews',
        'columns.lib.context_impl.sqla.PageContextFactory',
        'columns.lib.context_impl.sqla:PageCollectionContext',
        'columns.models:Page',
    )
    config.add_resource(
        'uploads',
        'columns.views:UploadViews',
        'columns.lib.context_impl.sqla.UploadContextFactory',
        'columns.lib.context_impl.sqla:UploadCollectionContext',
        'columns.models:Upload',
    )
    config.add_resource(
        'users',
        'columns.views:UserViews',
        'columns.lib.context_impl.sqla.UserContextFactory',
        'columns.lib.context_impl.sqla:UserCollectionContext',
        'columns.models:User',
    )

