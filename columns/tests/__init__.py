# encoding: utf-8
import unittest
from pyramid import testing
from pyramid.request import Request
from webtest import TestApp
from pyramid.httpexceptions import HTTPOk
from pyramid.httpexceptions import HTTPCreated
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPClientError
# SQLACollectionContext.__setitem__
# SQLACollectionContext.__getitem__ w/ slice
# generate_routing w/ bad collection, member or view
# settings_view, settings_edit_view, settings_save
import os
import os.path
import datetime
from cgi import FieldStorage
from StringIO import StringIO

def _populateDB():
	import sqlahelper
	from ..models import Article
	from ..models import Page
	from ..models import Upload
	from ..models import User
	from ..models import Tag
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

def _populateSettings(settings_dict):
	import sqlahelper
	from ..models import Setting
	Session = sqlahelper.get_session()
	for k, v in settings_dict.items():
		Session.add(Setting(module=k, config=v))
	
	Session.commit()

def _initTestingDB():
	import sqlahelper
	from sqlalchemy import create_engine
	from sqlalchemy.exc import IntegrityError
	from ..models import initialize_models
	sqlahelper.add_engine(create_engine('sqlite://'))
	sqlahelper.get_session().configure(extension=None)
	session = sqlahelper.get_session()
	initialize_models({'hostname':'localhost'})
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
		from ..models import Article
		from ..models import User
		self.request = DummyRequest()
		self.config = testing.setUp(request=self.request)
		self.session = _initTestingDB()
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
		from ..models import Article
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
		from ..models import Article
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
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		import sqlahelper
		self.session.remove()
		sqlahelper.reset()
		testing.tearDown()
	
	@staticmethod
	def _makeOne():
		from ..contexts import ArticleCollectionContext
		request = DummyRequest()
		return ArticleCollectionContext(request)
	
	def test___getitem__hit(self):
		from ..models import Article
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
		from ..models import Article
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
		from ..models import Article
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
		from ..models import Article
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
		from ..models import Article
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
		from ..models import Article
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
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		import sqlahelper
		self.session.remove()
		sqlahelper.reset()
		testing.tearDown()
	
	@staticmethod
	def _makeOne():
		from ..contexts import UserCollectionContext
		request = DummyRequest()
		return UserCollectionContext(request)
	
	def test___getitem__hit(self):
		from ..models import User
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
		from ..models import User
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
		from ..models import User
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
		from ..models import User
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
		from ..models import User
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
		from ..models import User
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
		from ..models import User
		root = self._makeOne()
		root.request.GET['order'] = 'name'
		items = root.index()
		
		self.assertEqual(len(items), 2)
		self.assertEqual(items[0].name, 'test_user')
		self.assertEqual(items[1].name, 'test_user2')
	
	def test_query_order_explicit(self):
		from ..models import User
		root = self._makeOne()
		root.request.GET['order'] = 'name.desc'
		items = root.index()
		
		self.assertEqual(len(items), 2)
		self.assertEqual(items[0].name, 'test_user2')
		self.assertEqual(items[1].name, 'test_user')

	def test_query_ops(self):
		from ..models import User
		root = self._makeOne()
		items = root.index(query_spec={'name': 'test_user', 'type': {'$lt': 2}})
		
		self.assertEqual(len(items), 1)
		self.assertEqual(items[0].name, 'test_user')
		self.assert_(items[0].type < 2)
	

class TestUploadCollection(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp(
			settings={'upload_basepath':'test_uploads'}
		)
		self.session = _initTestingDB()
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
		from ..contexts import UploadCollectionContext
		request = DummyRequest()
		return UploadCollectionContext(request)
	
	def test___getitem__hit(self):
		from ..models import Upload
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
		from ..models import Upload
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
		from ..models import Upload
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
		from ..models import Upload
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
		from ..models import Upload
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
		from ..models import Upload
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
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		import sqlahelper
		self.session.remove()
		sqlahelper.reset()
		testing.tearDown()
	
	@staticmethod
	def _makeOne():
		from ..contexts import PageCollectionContext
		request = DummyRequest()
		return PageCollectionContext(request)
	
	def test___getitem__hit(self):
		from ..models import Page
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
		from ..models import Page
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
		from ..models import Page
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
		from ..models import Page
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
		from ..models import Page
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
		from ..models import Page
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
		self.config = testing.setUp(request=self.request)
		self.config.testing_securitypolicy(userid=2)
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makeOne(self):
		from ..contexts import ArticleCollectionContext
		from ..models import Article
		
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
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makeOne(self):
		from ..contexts import UserCollectionContext
		from ..models import User
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
		self.config = testing.setUp(
			settings={'upload_basepath':'test_uploads'}
		)
		self.session = _initTestingDB()
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
		from ..contexts import UploadCollectionContext
		from ..models import Upload
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
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makeOne(self):
		from ..contexts import PageCollectionContext
		from ..models import Page
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
	


########################################
## Views Tests
########################################
class TestArticleView(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp()
	
	def tearDown(self):
		testing.tearDown()
	
	@staticmethod
	def _makeOne():
		from ..contexts import ArticleViews
		return ArticleViews
	
	@staticmethod
	def _makeCreateAtom():
		xmlstr = """<?xml version="1.0"?>
       <entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
         <title>Atom-Powered Robots Run Amok</title>
         <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
         <updated>2003-12-13T18:30:02Z</updated>
         <app:draft>yes</app:draft>
         <author><name>John Doe</name></author>
         <content>Some text.</content>
         <category term="tag1" label="Tag1" />
       </entry>"""
		return xmlstr
	
	@staticmethod
	def _makeInvalidCreateAtom():
		xmlstr = """<?xml version="1.0"?>
       <entry xmlns="http://www.w3.org/2005/Atom">
         <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
         <updated>2003-12-13T18:30:02Z</updated>
         <author><name>John Doe</name></author>
         <content>Some text.</content>
         <category term="tag1" label="Tag1" />
       </entry>"""
		return xmlstr
	
	@staticmethod
	def _makeUpdateAtom():
		xmlstr = """<?xml version="1.0"?>
       <entry xmlns="http://www.w3.org/2005/Atom" xmlns:app="http://www.w3.org/2007/app">
         <title>Atom-Powered Robots Run Amok</title>
         <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
         <updated>2003-12-13T18:30:02Z</updated>
         <app:draft>no</app:draft>
         <author><name>John Doe</name></author>
         <content>Some text.</content>
         <category term="tag1" label="Tag1" />
       </entry>"""
		return xmlstr
	
	@staticmethod
	def _makeInvalidUpdateAtom():
		xmlstr = """<?xml version="1.0"?>
       <entry xmlns="http://www.w3.org/2005/Atom">
         <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
         <updated>2003-12-13T18:30:02Z</updated>
         <author><name>John Doe</name></author>
         <content>Some text.</content>
         <category term="tag1" label="Tag1" />
       </entry>"""
		return xmlstr
	
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
		self.config = testing.setUp()
	
	def tearDown(self):
		testing.tearDown()
	
	@staticmethod
	def _makeOne():
		from ..contexts import UserViews
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
		self.config = testing.setUp()
	
	def tearDown(self):
		testing.tearDown()
	
	@staticmethod
	def _makeOne():
		from ..contexts import UploadViews
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
		self.config = testing.setUp()
	
	def tearDown(self):
		testing.tearDown()
	
	@staticmethod
	def _makeOne():
		from ..contexts import PageViews
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
		settings = {
			'static_directory':'.:static',
			'upload_basepath':'test_uploads'
		}
		self.request = DummyRequest()
		self.config = testing.setUp(
			request=self.request,
			settings=settings
		)
		self.config.include('columns.lib.view')
		self.config.include('columns.auth')
		self.config.include('columns.setup_resource_routes')
		self.config.include('columns.setup_admin_routes')
		self.config.add_static_view(
			'static', 
			settings.get('static_directory')
		)
		self.request.registry = self.config.registry
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def test_logout_view(self):
		from ..auth import logout_view
		response = logout_view(self.request)
		self.assertEquals(response.status_int, 302)

	def test_logout_view_xhr(self):
		from ..auth import logout_view
		self.request.is_xhr = True
		response = logout_view(self.request)
		self.assertEquals(response.status_int, 200)

class TestQuickImageViews(unittest.TestCase):
	def setUp(self):
		settings = {
			'static_directory':'.:static',
			'upload_basepath':'test_uploads',
			'upload_baseurl': 'http://localhost:6543/uploads'
		}
		self.request = DummyRequest()
		self.config = testing.setUp(
			request=self.request,
			settings=settings
		)
		self.config.include('columns.lib.view')
		self.config.include('columns.auth')
		self.config.include('columns.setup_resource_routes')
		self.config.include('columns.setup_admin_routes')
		self.config.add_static_view(
			'static', 
			settings.get('static_directory')
		)
		self.request.registry = self.config.registry
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def test_quick_image_upload(self):
		from ..views import imageupload
		test_file = FieldStorage()
		test_file.filename = 'example.txt'
		test_file.file = StringIO('12345')
		self.request.method = 'POST'
		self.request.POST = {
			'title': 'test_create_upload',
			'file': test_file,
		}
		response = imageupload(self.request)
	

class TestBlogViews(unittest.TestCase):
	def setUp(self):
		settings = {
			'static_directory':'.:static',
		}
		self.request = DummyRequest()
		self.config = testing.setUp(
			request=self.request,
			settings=settings
		)
		self.config.include('columns.lib.view')
		self.config.include('columns.auth')
		self.config.include('columns.blog')
		self.config.include('columns.setup_admin_routes')
		self.config.add_static_view(
			'static', 
			settings.get('static_directory')
		)
		self.request.registry = self.config.registry
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def test_page_view(self):
		from ..blog import page_view
		self.request.matchdict = {'page': 'test_page'}
		response = page_view(self.request)
	
	def test_page_view_invalid(self):
		from ..blog import page_view
		self.request.matchdict = {'page': 'not_a_real_page'}
		self.assertRaises(HTTPNotFound, page_view, self.request)
	
	def test_story_view(self):
		from ..blog import story_view
		self.request.matchdict = {'permalink': 'test_article_permalink'}
		response = story_view(self.request)
	
	def test_story_view_invalid(self):
		from ..blog import story_view
		self.request.matchdict = {'permalink': 'not_a_real_article'}
		self.assertRaises(HTTPNotFound, story_view, self.request)
	
	def test_stream_view(self):
		from ..blog import stream_view
		response = stream_view(self.request)
	
	def test_stream_view_filter_user(self):
		from ..blog import stream_view
		self.request.GET['user'] = 'test_user'
		response = stream_view(self.request)
	
	def test_stream_view_filter_tag(self):
		from ..blog import stream_view
		self.request.GET['tag'] = 'tag1'
		response = stream_view(self.request)
	

class TestSettingsViews(unittest.TestCase):
	def setUp(self):
		settings = {
			'static_directory':'.:static',
		}
		self.request = DummyRequest()
		self.config = testing.setUp(
			request=self.request,
			settings=settings
		)
		self.config.include('columns.lib.view')
		self.config.include('columns.auth')
		self.config.include('columns.blog')
		self.config.include('columns.setup_admin_routes')
		self.config.add_static_view(
			'static', 
			settings.get('static_directory')
		)
		self.request.registry = self.config.registry
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def test_settings_view(self):
		from ..views import settings_view
		response = settings_view(self.request)
	
	def test_settings_edit_view(self):
		from ..views import settings_edit_view
		self.request.matchdict = {'module': 'dummy'}
		_populateSettings({'dummy':{
			'test_field': 'qwerty',
		}})
		response = settings_edit_view(self.request)
	
	def test_settings_save(self):
		from ..views import settings_save
		self.request.matchdict = {'module': 'dummy'}
		_populateSettings({'dummy':{
			'test_field': 'qwerty',
		}})
		self.request.method = 'POST'
		self.request.POST = {
			'save': '1',
			'test_field': 'qwertyuiop',
			'new_field': 'blah blah',
		}
		self.assertRaises(HTTPFound, settings_save, self.request)
	



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
		main_app = main({}, **settings)
		self.app = TestApp(main_app)
	
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
		main_app = main({}, **settings)
		self.app = TestApp(main_app)
	
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
		main_app = main({}, **settings)
		self.app = TestApp(main_app)
	
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
		main_app = main({}, **settings)
		self.app = TestApp(main_app)
	
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
		self.config = testing.setUp(request=self.request)
		self.session = _initTestingDB()

	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makePolicy(self):
		from ..auth import SessionAuthenticationPolicy
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
	
	def test_remember_miss_and_create(self):
		policy = self._makePolicy()
		policy.remember(self.request, 99, create=True)
		
		session = self.request.session
		self.assertEquals(session['auth.userid'], 99)
		self.assertEquals(session['auth.type'], 9)
	
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
		self.config = testing.setUp(request=self.request)
		self.session = _initTestingDB()
		from .. import setup_admin_routes
		self.config.include('columns.lib.view')
		self.config.include(setup_admin_routes)

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
		self.assertEquals(response.status_int, 302)

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
		self.config = testing.setUp(request=self.request)
		self.config.include('columns.lib.view')
		self.config.include('columns.setup_admin_routes')
		self.config.include('columns.auth')
		self.config.add_static_view('static', '.:static/')
		self.request.registry = self.config.registry
		self.session = _initTestingDB()
	
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
	
	
	def test_logout_view(self):
		from ..auth import logout_view
		response = logout_view(self.request)
		self.assertEquals(response.status_int, 302)
	
	
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
		self.config = testing.setUp(request=self.request)
		self.config.testing_securitypolicy(userid='1', permissive=True)
	
	def test_is_allowed(self):
		from ..lib.view import is_allowed
		self.assertEquals(is_allowed('1'), True)
	
	def test_is_not_allowed(self):
		from ..lib.view import is_not_allowed
		self.assertEquals(is_not_allowed('1'), False)
	

