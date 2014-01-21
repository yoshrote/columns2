# encoding: utf-8
import unittest
from pyramid import testing
from webtest import TestApp
# SQLACollectionContext.__setitem__
# SQLACollectionContext.__getitem__ w/ slice
# generate_routing w/ bad collection, member or view
# settings_view, settings_edit_view, settings_save
import os
import os.path
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
    'models.module': 'columns.models',
    'models.routes': 'columns.lib.context_impl.sqla:setup_resource_routes',
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
## Model Collection Tests
########################################
class TestArticleModel(unittest.TestCase):
    def setUp(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        User = models.User
        self.request = DummyRequest()
        self.config = testing.setUp(request=self.request, settings=SETTINGS)
        self.session = _initTestingDB(self.config)
        today = datetime.datetime.utcnow()
        unpublished_article = Article(
            title='unpublished article',
            content='<p>blah</p><hr/><p>blah part 5</p>',
            created=today,
            updated=today,
        )
        user = self.session.query(User).first()
        unpublished_article.author = user
        unpublished_article = self.session.merge(unpublished_article)

    
    def tearDown(self):
        import sqlahelper
        self.session.remove()
        sqlahelper.reset()
        testing.tearDown()

    def test_publish(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        article = self.session.query(Article).filter(Article.title == 'unpublished article').one()
        pubtime = datetime.datetime(2013, 2, 28, 13, 14, 15)
        article.update_from_values({'published': pubtime})
        updated_article = self.session.merge(article)
        self.assertEquals(
            updated_article.permalink, 
            "2013-02-28-unpublished-article"
        )
        self.assertEquals(
            updated_article.atom_id, 
            'tag:localhost,2013-02-28:2013-02-28-unpublished-article'
        )

    def test_add_contributor(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        self.config.testing_securitypolicy(userid=2)
        # update the article
        article = self.session.query(Article).filter(Article.title == 'unpublished article').one()
        article.update_from_values({'title': 'foobar'})
        updated_article = self.session.merge(article)
        self.assertEquals(len(updated_article.contributors), 1)
        self.assertDictEqual(updated_article.contributors[0], {'uri': None, 'id': 2, 'name': u'test_user2'})


########################################
## Context Collection Tests
########################################
class TestArticleCollection(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        import sqlahelper
        self.session.remove()
        sqlahelper.reset()
        testing.tearDown()
    
    @staticmethod
    def _makeOne():
        from ..lib.context_impl.sqla import ArticleCollectionContext
        request = DummyRequest()
        return ArticleCollectionContext(request)
    
    def test___getitem__hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        root = self._makeOne()
        first = root['1']
        self.assertEqual(first.__class__, Article)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
        self.assertEqual(first.summary, '<p>blah</p>')
    
    def test___getitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, '100')
    
    def test___getitem__notint(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, 'notint')
    
    def test_getslice_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        root = self._makeOne()
        result = root[:2]
        self.assertEquals(len(result), 1)
        first = result[0]
        last = root[-1:][0]
        self.assertEqual(first.__class__, Article)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
        self.assertEquals(first.__name__, last.__name__)
    
    def test_getslice_miss(self):
        root = self._makeOne()
        result = root[5:6]
        self.assertEquals(len(result), 0)
    
    def test_get_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        root = self._makeOne()
        first = root.get('1')
        self.assertEqual(first.__class__, Article)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
    
    def test_get_miss(self):
        root = self._makeOne()
        self.assertEqual(root.get('100', 'default'), 'default')
        self.assertEqual(root.get('100'), None)
    
    def test_index(self):
        root = self._makeOne()
        iterable = iter(root.index())
        result = list(iterable)
        self.assertEqual(len(result), 1)
        model = result[0]
        self.assertEqual(model.id, 1)
    
    def test_new(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        root = self._makeOne()
        model = root.new()
        self.assertEqual(model.__class__, Article)
        self.assertEqual(model.__parent__, root)
    
    def test___delitem__hit(self):
        root = self._makeOne()
        del root['1']
        self.assertRaises(KeyError, root.__getitem__, '1')
    
    def test___delitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__delitem__, '10000')
    
    def test_discard(self):
        root = self._makeOne()
        root.discard('1')
        self.assertRaises(KeyError, root.__getitem__, '1')
        root.discard('1')
    
    def test___contains__hit(self):
        root = self._makeOne()
        self.assertTrue(root.__contains__('1'))
    
    def test___contains__miss(self):
        root = self._makeOne()
        self.assertFalse(root.__contains__('10000'))
    
    def test___len__(self):
        root = self._makeOne()
        self.assertEquals(root.__len__(), 1)
    
    def test_clear(self):
        root = self._makeOne()
        root.clear()
        self.assertEquals(root.__len__(), 0)
    
    def test_add(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        root = self._makeOne()
        first = root['1']
        
        model = Article(
            title='test_article2',
            content='<p>blah2</p>',
        )
        root.add(model)
        second = root['2']
        self.assertEqual(second.__class__, Article)
        self.assertEqual(second.__parent__, root)
        self.assertEqual(second.__name__, '2')
    
    def test___setitem__(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Article = models.Article
        root = self._makeOne()
        first = root['1']
        first.title = 'test_article2'
        first.content = '<p>blah2</p>'
        root['1'] = first
        
        first_repeat = root['1']
        self.assertEqual(first_repeat.__class__, Article)
        self.assertEqual(first_repeat.__parent__, root)
        self.assertEqual(first_repeat.__name__, '1')
        self.assertEqual(first_repeat.title, 'test_article2')
        self.assertEqual(first_repeat.content, '<p>blah2</p>')
    

class TestUserCollection(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        import sqlahelper
        self.session.remove()
        sqlahelper.reset()
        testing.tearDown()
    
    @staticmethod
    def _makeOne():
        from ..lib.context_impl.sqla import UserCollectionContext
        request = DummyRequest()
        return UserCollectionContext(request)
    
    def test___getitem__hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        User = models.User
        root = self._makeOne()
        first = root['1']
        self.assertEqual(first.__class__, User)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
    
    def test___getitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, '100')
    
    def test___getitem__notint(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, 'notint')

    def test___getitem__view(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, 'index')
    
    def test_getslice_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        User = models.User
        root = self._makeOne()
        result = root[:2]
        self.assertEquals(len(result), 2)
        first = result[0]
        second = result[1]
        last = root[-1:][0]
        self.assertEqual(first.__class__, User)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
        self.assertEquals(second.__name__, last.__name__)
    
    def test_getslice_miss(self):
        root = self._makeOne()
        result = root[5:6]
        self.assertEquals(len(result), 0)
    
    def test_get_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        User = models.User
        root = self._makeOne()
        first = root.get('1')
        self.assertEqual(first.__class__, User)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
    
    def test_get_miss(self):
        root = self._makeOne()
        self.assertEqual(root.get('100', 'default'), 'default')
        self.assertEqual(root.get('100'), None)
    
    def test_index(self):
        root = self._makeOne()
        iterable = iter(root.index())
        result = list(iterable)
        self.assertEqual(len(result), 2)
        model = result[0]
        self.assertEqual(model.id, 1)
    
    def test_new(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        User = models.User
        root = self._makeOne()
        model = root.new()
        self.assertEqual(model.__class__, User)
        self.assertEqual(model.__parent__, root)
    
    def test___delitem__hit(self):
        root = self._makeOne()
        del root['1']
        self.assertRaises(KeyError, root.__getitem__, '1')
    
    def test___delitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__delitem__, '10000')
    
    def test_discard(self):
        root = self._makeOne()
        root.discard('1')
        self.assertRaises(KeyError, root.__getitem__, '1')
        root.discard('1')
    
    def test___contains__hit(self):
        root = self._makeOne()
        self.assertTrue(root.__contains__('1'))
    
    def test___contains__miss(self):
        root = self._makeOne()
        self.assertFalse(root.__contains__('10000'))
    
    def test___len__(self):
        root = self._makeOne()
        self.assertEquals(root.__len__(), 2)
    
    def test_clear(self):
        root = self._makeOne()
        root.clear()
        self.assertEquals(root.__len__(), 0)
    
    def test_add(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        User = models.User
        root = self._makeOne()
        model = User(
            name='test_user4',
            type=1,
            open_id='http://openid.example.com',
        )
        root.add(model)
        second = root['2']
        self.assertEqual(second.__class__, User)
        self.assertEqual(second.__parent__, root)
        self.assertEqual(second.__name__, '2')
    
    def test___setitem__(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        User = models.User
        root = self._makeOne()
        first = root['1']
        first.name = 'test_user4'
        first.type = 8
        root['1'] = first
        
        first_repeat = root['1']
        self.assertEqual(first_repeat.__class__, User)
        self.assertEqual(first_repeat.__parent__, root)
        self.assertEqual(first_repeat.__name__, '1')
        self.assertEqual(first_repeat.name, 'test_user4')
        self.assertEqual(first_repeat.type, 8)
    
    def test_query_order(self):
        root = self._makeOne()
        root.request.GET['order'] = 'name'
        items = root.index()
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].name, 'test_user')
        self.assertEqual(items[1].name, 'test_user2')
    
    def test_query_order_explicit(self):
        root = self._makeOne()
        root.request.GET['order'] = 'name.desc'
        items = root.index()
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].name, 'test_user2')
        self.assertEqual(items[1].name, 'test_user')

    def test_query_ops(self):
        root = self._makeOne()
        items = root.index(query_spec={'name': 'test_user', 'type': {'$lt': 2}})
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, 'test_user')
        self.assert_(items[0].type < 2)
    

class TestUploadCollection(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
        self.session = _initTestingDB(self.config)
        self.upload_path = 'test_uploads/test/dir/upload.txt'
        upload_dir = os.path.dirname(self.upload_path)
        if not os.path.exists(upload_dir): # pragma: no cover
            try:
                os.makedirs(upload_dir)
            except OSError:
                #WTF?
                pass
        upload = open(self.upload_path, 'wb')
        upload.write('12345')
        upload.close()
    
    def tearDown(self):
        import sqlahelper
        self.session.remove()
        sqlahelper.reset()
        testing.tearDown()
        if os.path.exists(self.upload_path):
            os.remove(self.upload_path)
    
    @staticmethod
    def _makeOne():
        from ..lib.context_impl.sqla import UploadCollectionContext
        request = DummyRequest()
        return UploadCollectionContext(request)
    
    def test___getitem__hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Upload = models.Upload
        root = self._makeOne()
        first = root['1']
        self.assertEqual(first.__class__, Upload)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
    
    def test___getitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, '100')
    
    def test___getitem__notint(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, 'notint')
    
    def test_getslice_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Upload = models.Upload
        root = self._makeOne()
        result = root[:2]
        self.assertEquals(len(result), 1)
        first = result[0]
        last = root[-1:][0]
        self.assertEqual(first.__class__, Upload)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
        self.assertEquals(first.__name__, last.__name__)
    
    def test_getslice_miss(self):
        root = self._makeOne()
        result = root[5:6]
        self.assertEquals(len(result), 0)
    
    def test_get_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Upload = models.Upload
        root = self._makeOne()
        first = root.get('1')
        self.assertEqual(first.__class__, Upload)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
    
    def test_get_miss(self):
        root = self._makeOne()
        self.assertEqual(root.get('100', 'default'), 'default')
        self.assertEqual(root.get('100'), None)
    
    def test_index(self):
        root = self._makeOne()
        iterable = iter(root.index())
        result = list(iterable)
        self.assertEqual(len(result), 1)
        model = result[0]
        self.assertEqual(model.id, 1)
    
    def test_new(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Upload = models.Upload
        root = self._makeOne()
        model = root.new()
        self.assertEqual(model.__class__, Upload)
        self.assertEqual(model.__parent__, root)
    
    def test___delitem__hit(self):
        root = self._makeOne()
        del root['1']
        self.assertRaises(KeyError, root.__getitem__, '1')
    
    def test___delitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__delitem__, '10000')
    
    def test_discard(self):
        root = self._makeOne()
        root.discard('1')
        self.assertRaises(KeyError, root.__getitem__, '1')
        root.discard('1')
    
    def test___contains__hit(self):
        root = self._makeOne()
        self.assertTrue(root.__contains__('1'))
    
    def test___contains__miss(self):
        root = self._makeOne()
        self.assertFalse(root.__contains__('10000'))
    
    def test___len__(self):
        root = self._makeOne()
        self.assertEquals(root.__len__(), 1)
    
    def test_clear(self):
        root = self._makeOne()
        root.clear()
        self.assertEquals(root.__len__(), 0)
    
    def test_add(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Upload = models.Upload
        root = self._makeOne()
        model = Upload(
            title='test_upload2',
            filepath='/test/upload2.file'
        )
        root.add(model)
        second = root['2']
        self.assertEqual(second.__class__, Upload)
        self.assertEqual(second.__parent__, root)
        self.assertEqual(second.__name__, '2')
    
    def test___setitem__(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Upload = models.Upload
        root = self._makeOne()
        first = root['1']
        first.title = 'test_upload2'
        root['1'] = first
        
        first_repeat = root['1']
        self.assertEqual(first_repeat.__class__, Upload)
        self.assertEqual(first_repeat.__parent__, root)
        self.assertEqual(first_repeat.__name__, '1')
        self.assertEqual(first_repeat.title, 'test_upload2')
    

class TestPageCollection(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        import sqlahelper
        self.session.remove()
        sqlahelper.reset()
        testing.tearDown()
    
    @staticmethod
    def _makeOne():
        from ..lib.context_impl.sqla import PageCollectionContext
        request = DummyRequest()
        return PageCollectionContext(request)
    
    def test___getitem__hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Page = models.Page
        root = self._makeOne()
        first = root['1']
        self.assertEqual(first.__class__, Page)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
    
    def test___getitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, '100')
    
    def test___getitem__notint(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__getitem__, 'notint')
    
    def test_getslice_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Page = models.Page
        root = self._makeOne()
        result = root[:2]
        self.assertEquals(len(result), 1)
        first = result[0]
        last = root[-1:][0]
        self.assertEqual(first.__class__, Page)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
        self.assertEquals(first.__name__, last.__name__)
    
    def test_getslice_miss(self):
        root = self._makeOne()
        result = root[5:6]
        self.assertEquals(len(result), 0)
    
    def test_get_hit(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Page = models.Page
        root = self._makeOne()
        first = root.get('1')
        self.assertEqual(first.__class__, Page)
        self.assertEqual(first.__parent__, root)
        self.assertEqual(first.__name__, '1')
    
    def test_get_miss(self):
        root = self._makeOne()
        self.assertEqual(root.get('100', 'default'), 'default')
        self.assertEqual(root.get('100'), None)
    
    def test_index(self):
        root = self._makeOne()
        iterable = iter(root.index())
        result = list(iterable)
        self.assertEqual(len(result), 1)
        model = result[0]
        self.assertEqual(model.id, 1)
    
    def test_new(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Page = models.Page
        root = self._makeOne()
        model = root.new()
        self.assertEqual(model.__class__, Page)
        self.assertEqual(model.__parent__, root)
    
    def test___delitem__hit(self):
        root = self._makeOne()
        del root['1']
        self.assertRaises(KeyError, root.__getitem__, '1')
    
    def test___delitem__miss(self):
        root = self._makeOne()
        self.assertRaises(KeyError, root.__delitem__, '10000')
    
    def test_discard(self):
        root = self._makeOne()
        root.discard('1')
        self.assertRaises(KeyError, root.__getitem__, '1')
        root.discard('1')
    
    def test___contains__hit(self):
        root = self._makeOne()
        self.assertTrue(root.__contains__('1'))
    
    def test___contains__miss(self):
        root = self._makeOne()
        self.assertFalse(root.__contains__('10000'))
    
    def test___len__(self):
        root = self._makeOne()
        self.assertEquals(root.__len__(), 1)
    
    def test_clear(self):
        root = self._makeOne()
        root.clear()
        self.assertEquals(root.__len__(), 0)
    
    def test_add(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Page = models.Page
        root = self._makeOne()
        model = Page(
            title='test_page2'
        )
        root.add(model)
        second = root['2']
        self.assertEqual(second.__class__, Page)
        self.assertEqual(second.__parent__, root)
        self.assertEqual(second.__name__, '2')
    
    def test___setitem__(self):
        models = dotted_resolver.maybe_resolve(SETTINGS['models.module'])
        Page = models.Page
        root = self._makeOne()
        first = root['1']
        first.title = 'test_page2'
        first.slug = 'test_page2'
        root['1'] = first
        
        first_repeat = root['1']
        self.assertEqual(first_repeat.__class__, Page)
        self.assertEqual(first_repeat.__parent__, root)
        self.assertEqual(first_repeat.__name__, '1')
        self.assertEqual(first_repeat.title, 'test_page2')
        self.assertEqual(first_repeat.slug, 'test_page2')
    


########################################
## Context Member Tests
########################################
class TestArticleMember(unittest.TestCase):
    def setUp(self):
        self.request = DummyRequest()
        self.config = testing.setUp(request=self.request, settings=SETTINGS)
        self.config.testing_securitypolicy(userid=2)
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        self.session.remove()
        testing.tearDown()
    
    def _makeOne(self):
        from ..lib.context_impl.sqla import ArticleCollectionContext     
        collection = ArticleCollectionContext(self.request)
        return collection.index()[0]
    
    def test_get_key(self):
        member = self._makeOne()
        self.assertEquals(member.get_key(), member.__name__)
    
    def test_build_from_values(self):
        member = self._makeOne()
        new_member = member.build_from_values(dict(
            title='test_article2',
            content='<p>blah2</p>',
            tags=[]
        ))
    
    def test_update_from_values(self):
        member = self._makeOne()
        mod_member = member.update_from_values(dict(
            title='test_article2',
            content='<p>blah2</p>',
            tags=[]
        ))
        self.session.commit()
    

class TestUserMember(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        self.session.remove()
        testing.tearDown()
    
    def _makeOne(self):
        from ..lib.context_impl.sqla import UserCollectionContext
        request = DummyRequest()
        collection = UserCollectionContext(request)
        return collection.index()[0]
    
    def test_get_key(self):
        member = self._makeOne()
        self.assertEquals(member.get_key(), member.__name__)
    
    def test_build_from_values(self):
        member = self._makeOne()
        new_member = member.build_from_values(dict(
            name='test_user3',
            type=1,
            open_id='http://openid.example.com',
        ))
    
    def test_update_from_values(self):
        member = self._makeOne()
        mod_member = member.update_from_values(dict(
            name='test_user3',
            type=1,
            open_id='http://openid.example.com',
        ))
    

class TestUploadMember(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
        self.session = _initTestingDB(self.config)
        self.upload_path = 'test_uploads/test/dir/upload.txt'
        upload_dir = os.path.dirname(self.upload_path)
        if not os.path.exists(upload_dir): # pragma: no cover
            try:
                os.makedirs(upload_dir)
            except OSError:
                #WTF?
                pass
        upload = open(self.upload_path, 'wb')
        upload.write('12345')
        upload.close()
    
    def tearDown(self):
        self.session.remove()
        testing.tearDown()
        if os.path.exists(self.upload_path):
            os.remove(self.upload_path)
    
    def _makeOne(self):
        from ..lib.context_impl.sqla import UploadCollectionContext
        request = DummyRequest()
        collection = UploadCollectionContext(request)
        return collection.index()[0]
    
    def test_get_key(self):
        member = self._makeOne()
        self.assertEquals(member.get_key(), member.__name__)
    
    def test_build_from_values(self):
        member = self._makeOne()
        test_file = FieldStorage()
        test_file.filename = 'example.txt'
        test_file.file = StringIO('12345')
        new_member = member.build_from_values(dict(
            title='test_upload2',
            content='blah blah blah',
            file=test_file
        ))
    
    def test_update_from_values(self):
        member = self._makeOne()
        mod_member = member.update_from_values(dict(
            title='test_upload2',
            content='blah blah blah'
        ))
    

class TestPageMember(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp(settings=SETTINGS)
        self.session = _initTestingDB(self.config)
    
    def tearDown(self):
        self.session.remove()
        testing.tearDown()
    
    def _makeOne(self):
        from ..lib.context_impl.sqla import PageCollectionContext
        request = DummyRequest()
        collection = PageCollectionContext(request)
        return collection.index()[0]
    
    def test_get_key(self):
        member = self._makeOne()
        self.assertEquals(member.get_key(), member.__name__)
    
    def test_build_from_values(self):
        member = self._makeOne()
        new_member = member.build_from_values(dict(
            title='test_page2'
        ))
    
    def test_update_from_values(self):
        member = self._makeOne()
        mod_member = member.update_from_values(dict(
            title='test_page2'
        ))

