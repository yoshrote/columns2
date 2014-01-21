# encoding: utf-8
import unittest
from pyramid import testing
from webtest import TestApp
from pyramid.httpexceptions import HTTPOk
from pyramid.httpexceptions import HTTPCreated
from pyramid.httpexceptions import HTTPClientError
import datetime
from cgi import FieldStorage
from StringIO import StringIO
from pyramid.util import DottedNameResolver
dotted_resolver = DottedNameResolver(None)

SETTINGS = {
    'hostname': 'localhost',
    'sqlalchemy.url':'sqlite://',
    'upload_basepath':'test_uploads',
    'static_directory':'.:static',
    'upload_baseurl': 'http://localhost:6543/uploads',
    'models.routes': 'columns.lib.context_impl.sqla:setup_resource_routes',
    'models.module': 'columns.models',
    'models.setup': 'columns.lib.context_impl.sqla:setup_models',
    'models.find_user': 'columns.lib.context_impl.sqla:find_user',
    'models.session_policy': 'columns.lib.context_impl.sqla:SessionAuthenticationPolicy'
}

def _populateDB():
    import sqlahelper
    models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
    Article = models.Article
    Page = models.Page
    Upload = models.Upload
    User = models.User
    Tag = models.Tag
    from sqlalchemy.exc import IntegrityError
    Session = sqlahelper.get_session()
    today = datetime.datetime.utcnow()
    
    tag1 = Tag(label='tag1')
    tag2 = Tag(label='tag2')
    
    tag1 = Session.merge(tag1)
    tag2 = Session.merge(tag2)
    
    user = User(
        name='test_user',
        type=1,
        open_id='http://openid.example.com',
    )
    user2 = User(
        name='test_user2',
        type=2,
        open_id='http://openid2.example.com',
    )
    article = Article(
        id=1,
        title='test_article',
        content='<p>blah</p><hr/><p>blah part 2</p>',
        published=today,
        created=today,
        updated=today,
        permalink='test_article_permalink'
    )
    article.author = user
    article.tags.add(tag1)
    article.tags.add(tag2)

    page = Page(title='test_page', slug='test_page', visible=True)
    upload = Upload(
        title='test_upload',
        filepath='test/dir/upload.txt'
    )
    upload.author = user
    upload.tags.add(tag1)
    upload.tags.add(tag2)
    try:
        Session.add(user)
        Session.add(user2)
        article = Session.merge(article)
        Session.add(page)
        Session.add(upload)
        Session.commit()
    except IntegrityError: # pragma: no cover
        Session.rollback()

def _initTestingDB(config):
    import sqlahelper
    setup_models = dotted_resolver.maybe_resolve(SETTINGS['models.setup'])    
    models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
    models.url_host = SETTINGS['hostname']
    setup_models(config)
    session = sqlahelper.get_session()
    _populateDB()
    return session


class DummyMember(object):
    __parent__ = None
    __name__ = None
    def __init__(self, name=None, parent=None):
        self.__name__ = name
        self.__parent__ = parent
    
    def update_from_values(self, values):
        return self
    
    def build_from_values(self, values):
        return self

class DummyCollection(testing.DummyResource):
    def index(self, offset=None, limit=None, query_spec=None):
        return dict(self.subs.items()[slice(offset, limit)])
    
    def new(self):
        return DummyMember(parent=self)
    
    def add(self, resource):
        self.subs[resource.__name__] = resource
        return resource

class DummyRequest(testing.DummyRequest):
    content_type = 'application/x-form-urlencoded'
    is_xhr = False


########################################
## Views Tests
########################################
class TestArticleView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
    
    def tearDown(self):
        testing.tearDown()
    
    @staticmethod
    def _makeOne():
        from ..views import ArticleViews
        return ArticleViews
    
    def test_index(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.index()
    
    def test_show(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, request)
        response = viewer.show()
    
    def test_new(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.new()
    
    def test_create(self):
        viewer_cls = self._makeOne()
        request = DummyRequest(post={
            'title': 'next_story',
            'content': '<p>test data</p>',
            'tags': 'tag1, tag2, tag3',
        })
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPCreated, viewer.create)
    
    def test_create_invalid(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPClientError, viewer.create)
    
    def test_update(self):
        viewer_cls = self._makeOne()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest(post={
            'title': 'next_story',
            'content': '<p>test data</p>',
        })
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.update
        )
    
    def test_update_invalid(self):
        viewer_cls = self._makeOne()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPClientError,
            viewer.update
        )
    
    def test_delete(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.delete
        )

class TestUserView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
    
    def tearDown(self):
        testing.tearDown()
    
    @staticmethod
    def _makeOne():
        from ..views import UserViews
        return UserViews
    
    def test_index(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.index()
    
    def test_show(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, request)
        response = viewer.show()
    
    def test_new(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.new()
    
    def test_create(self):
        viewer_cls = self._makeOne()
        request = DummyRequest(post={
            'name': 'new_user',
            'type': 9,
        })
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPCreated, viewer.create)
    
    def test_create_invalid(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPClientError, viewer.create)
    
    def test_update(self):
        viewer_cls = self._makeOne()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest({
            'name': 'old_user',
            'type': '1',
        })
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.update
        )
    
    def test_update_invalid(self):
        viewer_cls = self._makeOne()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPClientError,
            viewer.update
        )
    
    def test_delete(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.delete
        )

class TestUploadView(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.config = testing.setUp(settings=SETTINGS)
    
    def tearDown(self):
        testing.tearDown()
    
    @staticmethod
    def _makeOne():
        from ..views import UploadViews
        return UploadViews
    
    def test_index(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.index()
    
    def test_show(self):
        viewer_cls = self._makeOne()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, self.request)
        response = viewer.show()
    
    def test_new(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.new()
    
    def test_create(self):
        viewer_cls = self._makeOne()
        test_file = FieldStorage()
        test_file.filename = 'example.txt'
        test_file.file = StringIO('12345')
        request = DummyRequest(post={
            'title': 'test_create_upload',
            'file': test_file,
        })
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPCreated, viewer.create)
    
    def test_create_invalid(self):
        viewer_cls = self._makeOne()
        test_file = FieldStorage()
        request = DummyRequest(post={
            'title': 'whatever',
            'file': test_file,
        })
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPClientError, viewer.create)
        
        request = DummyRequest(post={
            'title': 'whatever',
        })
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPClientError, viewer.create)
    
    def test_update(self):
        viewer_cls = self._makeOne()
        request = DummyRequest(post={
            'title': 'test_update_upload',
        })
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.update
        )
    
    def test_update_invalid(self):
        viewer_cls = self._makeOne()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPClientError,
            viewer.update
        )
    
    def test_delete(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.delete
        )

class TestPageView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
    
    def tearDown(self):
        testing.tearDown()
    
    @staticmethod
    def _makeOne():
        from ..views import PageViews
        return PageViews
    
    def test_index(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.index()
    
    def test_show(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, request)
        response = viewer.show()
    
    def test_new(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        response = viewer.new()
    
    def test_create(self):
        viewer_cls = self._makeOne()
        request = DummyRequest(post={
            'title': 'next_page',
            'content': '<p>test data</p>',
        })
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPCreated, viewer.create)
    
    def test_create_invalid(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        context = DummyCollection()
        viewer = viewer_cls(context, request)
        self.assertRaises(HTTPClientError, viewer.create)
    
    def test_update(self):
        viewer_cls = self._makeOne()
        request = DummyRequest(post={
            'title': 'next_page',
            'content': '<p>test data</p>',
        })
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.update
        )
    
    def test_update_invalid(self):
        viewer_cls = self._makeOne()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        request = DummyRequest()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPClientError,
            viewer.update
        )
    
    def test_delete(self):
        viewer_cls = self._makeOne()
        request = DummyRequest()
        collection = DummyCollection()
        context = DummyMember(name='1', parent=collection)
        collection['1'] = DummyMember()
        viewer = viewer_cls(context, request)
        self.assertRaises(
            HTTPOk,
            viewer.delete
        )

class TestAuthViews(unittest.TestCase):
    def setUp(self):

        self.request = DummyRequest()
        self.config = testing.setUp(
            request=self.request,
            settings=SETTINGS
        )
        self.config.include('columns.lib.view')
        self.config.include('columns.auth')
        self.config.include('columns.lib.base')
        self.config.include(dotted_resolver.maybe_resolve(SETTINGS['models.routes']))
        #columns.setup_resource_routes')
        self.config.add_static_view(
            'static', 
            SETTINGS.get('static_directory')
        )
        self.request.registry = self.config.registry
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        self.session.remove()
        testing.tearDown()
    
    def test_logout_view(self):
        from ..auth import logout_view
        response = logout_view(self.request)
        self.assertEquals(response.status_int, 200)


########################################
## Functional Tests
########################################
class TestFunctionalArticle(unittest.TestCase):
    def setUp(self):
        from .. import main
        settings = {
            'test_engine': True,
            'static_directory': '.:static',
            'enable_auth': False,
        }
        settings.update(SETTINGS)
        main_app = main({}, **settings)
        self.app = TestApp(main_app)
        _populateDB()
    
    def tearDown(self):
        import sqlahelper
        sqlahelper.reset()
        self.app.reset()
    
    def test_index_json(self):
        response = self.app.get(
            '/api/articles/', 
            headers=[('Accept', 'application/json')]
        )
    
    def test_show_json(self):
        response = self.app.get(
            '/api/articles/1', 
            headers=[('Accept', 'application/json')]
        )

class TestFunctionalUser(unittest.TestCase):
    def setUp(self):
        from .. import main
        settings = {
            'test_engine': True,
            'static_directory': '.:static',
            'enable_auth': False,
        }
        settings.update(SETTINGS)
        main_app = main({}, **settings)
        self.app = TestApp(main_app)
        _populateDB()
    
    def tearDown(self):
        import sqlahelper
        sqlahelper.reset()
        self.app.reset()
    
    def test_index_json(self):
        response = self.app.get(
            '/api/users/', 
            headers=[('Accept', 'application/json')]
        )
    
    def test_show_json(self):
        response = self.app.get(
            '/api/users/1', 
            headers=[('Accept', 'application/json')]
        )

class TestFunctionalUpload(unittest.TestCase):
    def setUp(self):
        from .. import main
        settings = {
            'test_engine': True,
            'static_directory': '.:static',
            'enable_auth': False,
        }
        settings.update(SETTINGS)
        main_app = main({}, **settings)
        self.app = TestApp(main_app)
        _populateDB()
    
    def tearDown(self):
        import sqlahelper
        sqlahelper.reset()
        self.app.reset()
    
    def test_index_json(self):
        response = self.app.get(
            '/api/uploads/', 
            headers=[('Accept', 'application/json')]
        )
    
    def test_show_json(self):
        response = self.app.get(
            '/api/uploads/1', 
            headers=[('Accept', 'application/json')]
        )

class TestFunctionalPage(unittest.TestCase):
    def setUp(self):
        from .. import main
        settings = {
            'test_engine': True,
            'static_directory': '.:static',
            'enable_auth': False,
        }
        settings.update(SETTINGS)
        main_app = main({}, **settings)
        self.app = TestApp(main_app)
        _populateDB()
    
    def tearDown(self):
        import sqlahelper
        sqlahelper.reset()
        self.app.reset()
    
    def test_index_json(self):
        response = self.app.get(
            '/api/pages/', 
            headers=[('Accept', 'application/json')]
        )
    
    def test_show_json(self):
        response = self.app.get(
            '/api/pages/1', 
            headers=[('Accept', 'application/json')]
        )
    


########################################
## Other Unit Tests
########################################
class TestAuthenticationPolicy(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.config = testing.setUp(request=self.request, settings=SETTINGS)
        self.session = _initTestingDB(self.config)

    def tearDown(self):
        self.session.remove()
        testing.tearDown()
    
    def _makePolicy(self):
        SessionAuthenticationPolicy = dotted_resolver.maybe_resolve(SETTINGS['models.session_policy'])
        return SessionAuthenticationPolicy()
    
    def test_remember(self):
        policy = self._makePolicy()
        policy.remember(self.request, 1)
        
        session = self.request.session
        self.assertEquals(session['auth.userid'], 1)
        self.assertEquals(session['auth.type'], 1)
    
    def test_remember_miss(self):
        policy = self._makePolicy()
        policy.remember(self.request, 99)
        
        session = self.request.session
        self.assert_('auth.userid' not in session)
        self.assert_('auth.type' not in session)
    
    def test_forget(self):
        self.request.session.update({
            'auth.userid':'1',
            'auth.type': 1,
            'auth.misc': 'foo',
            'othervar': 'bar'
        })
        policy = self._makePolicy()
        policy.forget(self.request)
        
        session = self.request.session
        self.assert_('auth.userid' not in session)
        self.assert_('auth.type' not in session)
        self.assert_('auth.misc' not in session)
        self.assert_('othervar' in session)
    
    def test_unauthenticated_userid(self):
        policy = self._makePolicy()
        self.request.session.update({
            'auth.userid':'1',
            'auth.type': 1,
            'auth.misc': 'foo',
            'othervar': 'bar'
        })
        res = policy.unauthenticated_userid(self.request)
        
        self.assertEquals(res, '1')
    
    def test_user_hit(self):
        policy = self._makePolicy()
        userid = 1
        permissions = policy.callback(userid , self.request)
        self.assert_(1 in permissions)
        self.assert_('super' in permissions)
    
    def test_user_miss(self):
        policy = self._makePolicy()
        userid = 234
        permissions = policy.callback(userid , self.request)
    
    def test_debug_sessions(self):
        from ..auth import debug_sessions
        from pyramid.events import NewResponse
        self.request.session['_f_'] = "Some error message"
        event = NewResponse(self.request, None)
        debug_sessions(event)
        self.assert_('_f_' not in self.request.session)
        
class TestSessionViews(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.config = testing.setUp(request=self.request, settings=SETTINGS)
        self.session = _initTestingDB(self.config)
        self.config.include('columns.lib.view')

    def tearDown(self):
        self.session.remove()
        testing.tearDown()
    
    def test_oid_callback_hit(self):
        from ..auth import oid_authentication_callback
        success_dict = {
            'identity_url': 'http://openid.example.com',
            'ax': {},
            'sreg': {}
        }
        response = oid_authentication_callback(None, self.request, success_dict)
        self.assertEquals(response.status_int, 200)

    def test_oid_callback_miss(self):
        from ..auth import oid_authentication_callback
        success_dict = {
            'identity_url': 'http://fake.example.com',
            'ax': {},
            'sreg': {}
        }
        response = oid_authentication_callback(None, self.request, success_dict)
        self.assertEquals(response.status_int, 401)
    
    def test_whoami_view(self):
        from ..auth import whoami_view
        response = whoami_view(self.request)
        self.assertDictEqual(response, {})

        self.request.session.update({
            'auth.userid':'1',
            'auth.type': 1,
            'auth.misc': 'foo',
            'othervar': 'bar'
        })

        response = whoami_view(self.request)
        self.assertDictEqual(response, {
            'id': self.request.session.get('auth.userid'),
            'user': self.request.session.get('auth.name'),
            'type': self.request.session.get('auth.type'),
        })

class TestAuthorizationPolicy(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.config = testing.setUp(request=self.request, settings=SETTINGS)
        self.config.include('columns.lib.view')
        self.config.include('columns.auth')
        self.config.add_static_view('static', '.:static/')
        self.request.registry = self.config.registry
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        self.session.remove()
        testing.tearDown()
    
    def _makePolicy(self):
        from ..auth import AuthorizationPolicy
        from ..auth import is_author
        from ..auth import minimum_permission
        PERMISSIONS = {
            'super': 1,
            'admin': 2,
            'editor': 3,
            'author': 4,
            'probation': 8,
            'subscriber': 9
        }
        self.DEFAULT_PERMISSION = 'subscriber'
        POLICY_MAP = {
            None: {
                'default': set([self.DEFAULT_PERMISSION]),
                'test': [set(['test_value'])],
            },
            'test': {
                'view': [minimum_permission('probation')],
                'edit': [minimum_permission('editor'), is_author],
            }
        }
        return AuthorizationPolicy(POLICY_MAP)
    
    
    def test_permits(self):
        policy = self._makePolicy()
        response = policy.permits(None, ['test_value'], 'test')
        self.assertEquals(response, True)
    
    def test_permits_false(self):
        policy = self._makePolicy()
        response = policy.permits(None, [], 'test')
        self.assertEquals(response, False)
    
    def test_principals_allowed_collection(self):
        policy = self._makePolicy()
        context = DummyCollection()
        context.__name__ = 'test'
        response = policy.principals_allowed_by_permission(context, 'view')
        self.assertEquals(response, set(['admin', 'probation', 'super', 'editor', 'author']))
    
    def test_principals_allowed_member(self):
        policy = self._makePolicy()
        collection = DummyCollection()
        collection.__name__ = 'test'
        context = DummyMember(name='1', parent=collection)
        response = policy.principals_allowed_by_permission(context, 'default')
        self.assertEquals(response, set([self.DEFAULT_PERMISSION]))
    
    def test_principals_allowed_member_composite(self):
        policy = self._makePolicy()
        collection = DummyCollection()
        collection.__name__ = 'test'
        context = DummyMember(name='1', parent=collection)
        context.author_id = 1
        response = policy.principals_allowed_by_permission(context, 'edit')
        self.assertEquals(response, set(['admin', 'super', 'editor', 1]))

class TestJinjaFuncs(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.config = testing.setUp(request=self.request, settings=SETTINGS)
        self.config.testing_securitypolicy(userid='1', permissive=True)
    
    def test_is_allowed(self):
        from ..lib.view import is_allowed
        self.assertEquals(is_allowed('1'), True)
    
    def test_is_not_allowed(self):
        from ..lib.view import is_not_allowed
        self.assertEquals(is_not_allowed('1'), False)
    

