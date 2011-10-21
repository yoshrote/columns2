# encoding: utf-8
import unittest
from pyramid import testing
from pyramid.request import Request
from webtest import TestApp
from pyramid.httpexceptions import HTTPCreated
from pyramid.httpexceptions import HTTPOk
from pyramid.httpexceptions import HTTPNotImplemented
from pyramid.httpexceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPClientError

import os
import os.path
import datetime
from cgi import FieldStorage
from StringIO import StringIO

def _populateDB():
	import sqlahelper
	from columns.models import Article
	from columns.models import Page
	from columns.models import Upload
	from columns.models import User
	from columns.models import Tag
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
		content='<p>blah</p>',
		published=today,
		created=today,
		updated=today,
		permalink='test_article_permalink'
	)
	article.author = user
	article.tags.add(tag1)
	article.tags.add(tag2)
	page = Page(title='test_page',slug='test_page',visible=True)
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
	from columns.models import Setting
	Session = sqlahelper.get_session()
	for k, v in settings_dict.items():
		Session.add(Setting(module=k, values=v))
	
	Session.commit()

def _initTestingDB():
	import sqlahelper
	from sqlalchemy import create_engine
	from sqlalchemy.exc import IntegrityError
	from columns.models import initialize_database
	sqlahelper.add_engine(create_engine('sqlite://'))
	sqlahelper.get_session().configure(extension=None)
	session = sqlahelper.get_session()
	initialize_database()
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
	def index(self, offset=None, limit=None):
		return dict(self.subs.items()[slice(offset,limit)])
	
	def new(self):
		return DummyMember(parent=self)
	
	def save(self, resource):
		self.subs[resource.__name__] = resource
		return resource
	


########################################
## Context Collection Tests
########################################
class TestArticleCollection(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makeOne(self):
		from columns.contexts import ArticleCollectionContext
		request = testing.DummyRequest()
		return ArticleCollectionContext(request)
	
	def test___getitem__hit(self):
		from columns.models import Article
		root = self._makeOne()
		first = root['1']
		self.assertEqual(first.__class__, Article)
		self.assertEqual(first.__parent__, root)
		self.assertEqual(first.__name__, '1')
	
	def test___getitem__miss(self):
		root = self._makeOne()
		self.assertRaises(KeyError, root.__getitem__, '100')
	
	def test___getitem__notint(self):
		root = self._makeOne()
		self.assertRaises(KeyError, root.__getitem__, 'notint')
	
	def test_get_hit(self):
		from columns.models import Article
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
		from columns.models import Article
		root = self._makeOne()
		model = root.new()
		self.assertEqual(model.__class__, Article)
		self.assertEqual(model.__parent__, root)
	
	def test___delitem__hit(self):
		from columns.models import Article
		root = self._makeOne()
		model = root['1']
		del root['1']
		self.assertRaises(KeyError, root.__getitem__, '1')
	
	def test_save(self):
		from columns.models import Article
		root = self._makeOne()
		model = Article(
			title='test_article2',
			content='<p>blah2</p>',
		)
		root.save(model)
		second = root['2']
		self.assertEqual(second.__class__, Article)
		self.assertEqual(second.__parent__, root)
		self.assertEqual(second.__name__, '2')
	

class TestUserCollection(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makeOne(self):
		from columns.contexts import UserCollectionContext
		request = testing.DummyRequest()
		return UserCollectionContext(request)
	
	def test___getitem__hit(self):
		from columns.models import User
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
	
	def test_get_hit(self):
		from columns.models import User
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
		from columns.models import User
		root = self._makeOne()
		model = root.new()
		self.assertEqual(model.__class__, User)
		self.assertEqual(model.__parent__, root)
	
	def test___delitem__hit(self):
		from columns.models import User
		root = self._makeOne()
		model = root['1']
		del root['1']
		self.assertRaises(KeyError, root.__getitem__, '1')
	
	def test_save(self):
		from columns.models import User
		root = self._makeOne()
		model = User(
			name='test_user3',
			type=1,
			open_id='http://openid.example.com',
		)
		root.save(model)
		second = root['2']
		self.assertEqual(second.__class__, User)
		self.assertEqual(second.__parent__, root)
		self.assertEqual(second.__name__, '2')
	

class TestUploadCollection(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp(
			settings={'upload_basepath':'test_uploads'}
		)
		self.session = _initTestingDB()
		# FIXME: load self.upload_path from DB
		self.upload_path = 'test_uploads/test/dir/upload.txt'
		upload_dir = os.path.dirname(self.upload_path)
		if not os.path.exists(upload_dir): # pragma: no cover
			try:
				os.makedirs(upload_dir)
			except OSError:
				#WTF?
				pass
		upload = open(self.upload_path,'wb')
		upload.write('12345')
		upload.close()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
		if os.path.exists(self.upload_path):
			os.remove(self.upload_path)
	
	def _makeOne(self):
		from columns.contexts import UploadCollectionContext
		request = testing.DummyRequest()
		return UploadCollectionContext(request)
	
	def test___getitem__hit(self):
		from columns.models import Upload
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
	
	def test_get_hit(self):
		from columns.models import Upload
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
		from columns.models import Upload
		root = self._makeOne()
		model = root.new()
		self.assertEqual(model.__class__, Upload)
		self.assertEqual(model.__parent__, root)
	
	def test___delitem__hit(self):
		from columns.models import Upload
		root = self._makeOne()
		model = root['1']
		del root['1']
		self.assertRaises(KeyError, root.__getitem__, '1')
	
	def test_save(self):
		from columns.models import Upload
		root = self._makeOne()
		model = Upload(
			title='test_upload2',
			filepath='/test/upload2.file'
		)
		root.save(model)
		second = root['2']
		self.assertEqual(second.__class__, Upload)
		self.assertEqual(second.__parent__, root)
		self.assertEqual(second.__name__, '2')
	

class TestPageCollection(unittest.TestCase):
	def setUp(self):
		self.config = testing.setUp()
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makeOne(self):
		from columns.contexts import PageCollectionContext
		request = testing.DummyRequest()
		return PageCollectionContext(request)
	
	def test___getitem__hit(self):
		from columns.models import Page
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
	
	def test_get_hit(self):
		from columns.models import Page
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
		from columns.models import Page
		root = self._makeOne()
		model = root.new()
		self.assertEqual(model.__class__, Page)
		self.assertEqual(model.__parent__, root)
	
	def test___delitem__hit(self):
		from columns.models import Page
		root = self._makeOne()
		model = root['1']
		del root['1']
		self.assertRaises(KeyError, root.__getitem__, '1')
	
	def test_save(self):
		from columns.models import Page
		root = self._makeOne()
		model = Page(
			title='test_page2'
		)
		root.save(model)
		second = root['2']
		self.assertEqual(second.__class__, Page)
		self.assertEqual(second.__parent__, root)
		self.assertEqual(second.__name__, '2')
	


########################################
## Context Member Tests
########################################
class TestArticleMember(unittest.TestCase):
	def setUp(self):
		self.request = testing.DummyRequest()
		self.config = testing.setUp(request=self.request)
		self.config.testing_securitypolicy(userid=2)
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makeOne(self):
		from columns.contexts import ArticleCollectionContext
		from columns.models import Article
		
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
		))
	
	def test_update_from_values(self):
		member = self._makeOne()
		mod_member = member.update_from_values(dict(
			title='test_article2',
			content='<p>blah2</p>',
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
		from columns.contexts import UserCollectionContext
		from columns.models import User
		request = testing.DummyRequest()
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
		# FIXME: load self.upload_path from DB
		self.upload_path = 'test_uploads/test/dir/upload.txt'
		upload_dir = os.path.dirname(self.upload_path)
		if not os.path.exists(upload_dir): # pragma: no cover
			try:
				os.makedirs(upload_dir)
			except OSError:
				#WTF?
				pass
		upload = open(self.upload_path,'wb')
		upload.write('12345')
		upload.close()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
		if os.path.exists(self.upload_path):
			os.remove(self.upload_path)
	
	def _makeOne(self):
		from columns.contexts import UploadCollectionContext
		from columns.models import Upload
		request = testing.DummyRequest()
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
		from columns.contexts import PageCollectionContext
		from columns.models import Page
		request = testing.DummyRequest()
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
	
	def _makeOne(self):
		from columns.contexts import ArticleViews
		return ArticleViews
	
	def _makeCreateAtom(self):
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
	
	def _makeInvalidCreateAtom(self):
		xmlstr = """<?xml version="1.0"?>
       <entry xmlns="http://www.w3.org/2005/Atom">
         <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
         <updated>2003-12-13T18:30:02Z</updated>
         <author><name>John Doe</name></author>
         <content>Some text.</content>
         <category term="tag1" label="Tag1" />
       </entry>"""
		return xmlstr
	
	def _makeUpdateAtom(self):
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
	
	def _makeInvalidUpdateAtom(self):
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
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.index()
	
	def test_show(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		viewer = viewer_cls(context, request)
		response = viewer.show()
	
	def test_new(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.show()
	
	def test_create(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest(post={
			'title': 'next_story',
			'content': '<p>test data</p>',
			'tags': 'tag1, tag2, tag3',
		})
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPCreated, viewer.create)
	
	def test_create_invalid(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPClientError, viewer.create)
	
	def test_create_atom(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		request.body = self._makeCreateAtom()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPCreated, viewer.create_atom)
	
	def test_create_atom_invalid(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		request.body = self._makeInvalidCreateAtom()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPClientError, viewer.create_atom)
	
	def test_update(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest(post={
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
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPClientError,
			viewer.update
		)
	
	def test_update_atom(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		request.body = self._makeUpdateAtom()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPOk, viewer.update_atom)
	
	def test_update_atom_invalid(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		request.body = self._makeInvalidUpdateAtom()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPClientError, viewer.update_atom)
	
	def test_delete(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
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
	
	def _makeOne(self):
		from columns.contexts import UserViews
		return UserViews
	
	def test_index(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.index()
	
	def test_show(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		viewer = viewer_cls(context, request)
		response = viewer.show()
	
	def test_new(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.show()
	
	def test_create(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest(post={
			'name': 'new_user',
			'type': 9,
		})
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPCreated, viewer.create)
	
	def test_create_invalid(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPClientError, viewer.create)
	
	def test_create_atom(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPNotImplemented, viewer.create_atom)
	
	def test_update(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest({
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
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPClientError,
			viewer.update
		)
	
	def test_update_atom(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPNotImplemented, viewer.update_atom)
	
	def test_delete(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPOk,
			viewer.delete
		)
	

class TestUploadView(unittest.TestCase):
	def setUp(self):
		self.request = testing.DummyRequest()
		self.config = testing.setUp()
	
	def tearDown(self):
		testing.tearDown()
	
	def _makeOne(self):
		from columns.contexts import UploadViews
		return UploadViews
	
	def test_index(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.index()
	
	def test_show(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		viewer = viewer_cls(context, self.request)
		response = viewer.show()
	
	def test_new(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.show()
	
	def test_create(self):
		viewer_cls = self._makeOne()
		test_file = FieldStorage()
		test_file.filename = 'example.txt'
		test_file.file = StringIO('12345')
		request = testing.DummyRequest(post={
			'title': 'test_create_upload',
			'file': test_file,
		})
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPCreated, viewer.create)
	
	def test_create_invalid(self):
		viewer_cls = self._makeOne()
		test_file = FieldStorage()
		request = testing.DummyRequest(post={
			'title': 'whatever',
			'file': test_file,
		})
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPClientError, viewer.create)
		
		request = testing.DummyRequest(post={
			'title': 'whatever',
		})
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPClientError, viewer.create)
	
	def test_create_atom(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPNotImplemented, viewer.create_atom)
	
	def test_update(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest(post={
			'title': 'test_update_upload',
		})
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPOk,
			viewer.update
		)
	
	def test_update_invalid(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPClientError,
			viewer.update
		)
	
	def test_update_atom(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPNotImplemented, viewer.update_atom)
	
	def test_delete(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
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
	
	def _makeOne(self):
		from columns.contexts import PageViews
		return PageViews
	
	def test_index(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.index()
	
	def test_show(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		viewer = viewer_cls(context, request)
		response = viewer.show()
	
	def test_new(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		response = viewer.show()
	
	def test_create(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest(post={
			'title': 'next_page',
			'content': '<p>test data</p>',
			'stream_comment_style': 'summary',
			'story_comment_style': 'list',
		})
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPCreated, viewer.create)
	
	def test_create_invalid(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPClientError, viewer.create)
	
	def test_create_atom(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		context = DummyCollection()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPNotImplemented, viewer.create_atom)
	
	def test_update(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest(post={
			'title': 'next_page',
			'content': '<p>test data</p>',
			'stream_comment_style': 'summary',
			'story_comment_style': 'list',
		})
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPOk,
			viewer.update
		)
	
	def test_update_invalid(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPClientError,
			viewer.update
		)
	
	def test_update_atom(self):
		viewer_cls = self._makeOne()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		request = testing.DummyRequest()
		viewer = viewer_cls(context, request)
		self.assertRaises(HTTPNotImplemented, viewer.update_atom)
	
	def test_delete(self):
		viewer_cls = self._makeOne()
		request = testing.DummyRequest()
		collection = DummyCollection()
		context = DummyMember(name='1',parent=collection)
		collection['1'] = DummyMember()
		viewer = viewer_cls(context, request)
		self.assertRaises(
		 	HTTPOk,
			viewer.delete
		)
	

class TestAuthViews(unittest.TestCase):
	def setUp(self):
		settings = {
			'static_directory':'columns:static',
			'upload_basepath':'test_uploads'
		}
		self.request = testing.DummyRequest()
		self.config = testing.setUp(
			request=self.request,
			settings=settings
		)
		self.config.include('columns.lib.view')
		self.config.include('columns.auth')
		self.config.include('columns.setup_resource_routes')
		self.config.add_static_view(
			'static', 
			settings.get('static_directory')
		)
		self.request.registry = self.config.registry
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def test_login_view(self):
		from columns.auth import login_view
		response = login_view(self.request)
	
	def test_logout_view(self):
		from columns.auth import logout_view
		response = logout_view(self.request)
	
	def test_admin_view(self):
		from columns.views import admin_view
		response = admin_view(self.request)
	
	def test_xrds_view(self):
		from columns.auth import xrds_view
		response = xrds_view(self.request)
	

class TestQuickUploadViews(unittest.TestCase):
	def setUp(self):
		settings = {
			'static_directory':'columns:static',
			'upload_basepath':'test_uploads'
		}
		self.request = testing.DummyRequest()
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
	
	def test_browse_images(self):
		from columns.views import browse_images_view
		request = testing.DummyRequest()
		response = browse_images_view(request)
	
	def test_browse_images_ajax(self):
		from columns.views import browse_images_ajax
		request = testing.DummyRequest()
		response = browse_images_ajax(request)
	
	def test_quick_image_upload(self):
		from columns.views import quick_image_upload
		test_file = FieldStorage()
		test_file.filename = 'example.txt'
		test_file.file = StringIO('12345')
		self.request.method = 'POST'
		self.request.POST = {
			'title': 'test_create_upload',
			'upload': test_file,
		}
		response = quick_image_upload(self.request)
	

class TestBlogViews(unittest.TestCase):
	def setUp(self):
		settings = {
			'static_directory':'columns:static',
		}
		self.request = testing.DummyRequest()
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
		from columns.blog import page_view
		self.request.matchdict = {'page': 'test_page'}
		response = page_view(self.request)
	
	def test_page_view_invalid(self):
		from columns.blog import page_view
		self.request.matchdict = {'page': 'not_a_real_page'}
		self.assertRaises(HTTPNotFound, page_view, self.request)
	
	def test_story_view(self):
		from columns.blog import story_view
		self.request.matchdict = {'permalink': 'test_article_permalink'}
		response = story_view(self.request)
	
	def test_story_view_invalid(self):
		from columns.blog import story_view
		self.request.matchdict = {'permalink': 'not_a_real_article'}
		self.assertRaises(HTTPNotFound, story_view, self.request)
	
	def test_stream_view(self):
		from columns.blog import stream_view
		response = stream_view(self.request)
	



########################################
## Functional Tests
########################################
class TestFunctionalArticle(unittest.TestCase):
	def setUp(self):
		from columns import main
		settings = {
			'test_engine': True,
			'static_directory': 'columns:static'
		}
		main_app = main({},**settings)
		self.app = TestApp(main_app)
	
	def tearDown(self):
		import sqlahelper
		sqlahelper.reset()
		self.app.reset()
	
	def test_index_html(self):
		response = self.app.get(
			'/api/articles/', 
			headers=[('Accept','text/html')]
		)
	
	def test_index_atom(self):
		response = self.app.get(
			'/api/articles/', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_index_json(self):
		response = self.app.get(
			'/api/articles/', 
			headers=[('Accept','application/json')]
		)
	
	def test_show_html(self):
		response = self.app.get(
			'/api/articles/1', 
			headers=[('Accept','text/html')]
		)
	
	def test_show_atom(self):
		response = self.app.get(
			'/api/articles/1', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_show_json(self):
		response = self.app.get(
			'/api/articles/1', 
			headers=[('Accept','application/json')]
		)
	
	def test_new(self):
		response = self.app.get(
			'/api/articles/new', 
			headers=[('Accept','text/html')]
		)
	
	def test_edit(self):
		response = self.app.get(
			'/api/articles/1/edit', 
			headers=[('Accept','text/html')]
		)
	

class TestFunctionalUser(unittest.TestCase):
	def setUp(self):
		from columns import main
		settings = {
			'test_engine': True,
			'static_directory': 'columns:static'
		}
		main_app = main({},**settings)
		self.app = TestApp(main_app)
	
	def tearDown(self):
		import sqlahelper
		sqlahelper.reset()
		self.app.reset()
	
	def test_index_html(self):
		response = self.app.get(
			'/api/users/', 
			headers=[('Accept','text/html')]
		)
	
	def test_index_atom(self):
		response = self.app.get(
			'/api/users/', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_index_json(self):
		response = self.app.get(
			'/api/users/', 
			headers=[('Accept','application/json')]
		)
	
	def test_show_html(self):
		response = self.app.get(
			'/api/users/1', 
			headers=[('Accept','text/html')]
		)
	
	def test_show_atom(self):
		response = self.app.get(
			'/api/users/1', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_show_json(self):
		response = self.app.get(
			'/api/users/1', 
			headers=[('Accept','application/json')]
		)
	
	def test_new(self):
		response = self.app.get(
			'/api/users/new', 
			headers=[('Accept','text/html')]
		)
	
	def test_edit(self):
		response = self.app.get(
			'/api/users/1/edit', 
			headers=[('Accept','text/html')]
		)
	

class TestFunctionalUpload(unittest.TestCase):
	def setUp(self):
		from columns import main
		settings = {
			'test_engine': True,
			'static_directory': 'columns:static'
		}
		main_app = main({},**settings)
		self.app = TestApp(main_app)
	
	def tearDown(self):
		import sqlahelper
		sqlahelper.reset()
		self.app.reset()
	
	def test_index_html(self):
		response = self.app.get(
			'/api/uploads/', 
			headers=[('Accept','text/html')]
		)
	
	def test_index_atom(self):
		response = self.app.get(
			'/api/uploads/', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_index_json(self):
		response = self.app.get(
			'/api/uploads/', 
			headers=[('Accept','application/json')]
		)
	
	def test_show_html(self):
		response = self.app.get(
			'/api/uploads/1', 
			headers=[('Accept','text/html')]
		)
	
	def test_show_atom(self):
		response = self.app.get(
			'/api/uploads/1', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_show_json(self):
		response = self.app.get(
			'/api/uploads/1', 
			headers=[('Accept','application/json')]
		)
	
	def test_new(self):
		response = self.app.get(
			'/api/uploads/new', 
			headers=[('Accept','text/html')]
		)
	
	def test_edit(self):
		response = self.app.get(
			'/api/uploads/1/edit', 
			headers=[('Accept','text/html')]
		)
	

class TestFunctionalPage(unittest.TestCase):
	def setUp(self):
		from columns import main
		settings = {
			'test_engine': True,
			'static_directory': 'columns:static'
		}
		main_app = main({},**settings)
		self.app = TestApp(main_app)
	
	def tearDown(self):
		import sqlahelper
		sqlahelper.reset()
		self.app.reset()
	
	def test_index_html(self):
		response = self.app.get(
			'/api/pages/', 
			headers=[('Accept','text/html')]
		)
	
	def test_index_atom(self):
		response = self.app.get(
			'/api/pages/', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_index_json(self):
		response = self.app.get(
			'/api/pages/', 
			headers=[('Accept','application/json')]
		)
	
	def test_show_html(self):
		response = self.app.get(
			'/api/pages/1', 
			headers=[('Accept','text/html')]
		)
	
	def test_show_atom(self):
		response = self.app.get(
			'/api/pages/1', 
			headers=[('Accept','application/atom+xml')]
		)
	
	def test_show_json(self):
		response = self.app.get(
			'/api/pages/1', 
			headers=[('Accept','application/json')]
		)
	
	def test_new(self):
		response = self.app.get(
			'/api/pages/new', 
			headers=[('Accept','text/html')]
		)
	
	def test_edit(self):
		response = self.app.get(
			'/api/pages/1/edit', 
			headers=[('Accept','text/html')]
		)
	


########################################
## Other Unit Tests
########################################
class TestAuthenticationPolicy(unittest.TestCase):
	def setUp(self):
		self.request = testing.DummyRequest()
		self.config = testing.setUp(request=self.request)
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makePolicy(self):
		from columns.auth import SessionAuthenticationPolicy
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
		self.assertEquals(session['auth.userid'], 99)
		self.assertEquals(session['auth.type'], None)
	
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
		permissions = policy.callback(userid ,self.request)
		self.assert_(1 in permissions)
		self.assert_('super' in permissions)
	
	def test_user_miss(self):
		policy = self._makePolicy()
		userid = 234
		permissions = policy.callback(userid ,self.request)
	
	def test_oid_callback(self):
		from columns.auth import oid_authentication_callback
		self.config.include('columns.blog')
		success_dict = {
			'identity_url': 'http://openid.example.com',
			'ax': {},
			'sreg': {}
		}
		response = oid_authentication_callback(None, self.request, success_dict)
		self.assertEquals(response.status_int, 302)
	
	def test_twitter_login_view(self):
		_populateSettings({'auth':{
			'FACEBOOK_APP_ID': 'qdefwrth',
			'FACEBOOK_APP_SECRET': 'qwrtyrt',
			'FACEBOOK_SCOPE': 'offline_access,publish_stream,read_stream',
			'TWITTER_CONSUMER_KEY': 'key',
			'TWITTER_CONSUMER_SECRET': 'secret',
			'TWITTER_REQUEST_TOKEN_URL': 'http://term.ie/oauth/example/request_token.php',
			'TWITTER_ACCESS_TOKEN_URL': 'http://term.ie/oauth/example/access_token.php?foo=bar&oauth_token=1234&oauth_token_secret=12345&user_id=1',
			'TWITTER_AUTHORIZE_URL': 'http://twitter.com/oauth/authorize',
			'DEFAULT_RETURN': '/',
		
		}})
		from columns.auth import twitter_login_view
		self.config.include('columns.blog')
		self.config.include('columns.auth')
		response = twitter_login_view(self.request)
		self.request.GET['oauth_verifier'] = 'test_auth_verifier'
		response = twitter_login_view(self.request)
	
	def test_twitter_login_view_with_referer(self):
		_populateSettings({'auth':{
			'FACEBOOK_APP_ID': 'qdefwrth',
			'FACEBOOK_APP_SECRET': 'qwrtyrt',
			'FACEBOOK_SCOPE': 'offline_access,publish_stream,read_stream',
			'TWITTER_CONSUMER_KEY': 'key',
			'TWITTER_CONSUMER_SECRET': 'secret',
			'TWITTER_REQUEST_TOKEN_URL': 'http://term.ie/oauth/example/request_token.php',
			'TWITTER_ACCESS_TOKEN_URL': 'http://term.ie/oauth/example/access_token.php?foo=bar&oauth_token=1234&oauth_token_secret=12345&user_id=1',
			'TWITTER_AUTHORIZE_URL': 'http://twitter.com/oauth/authorize',
			'DEFAULT_RETURN': '/',
		
		}})
		from columns.auth import twitter_login_view
		self.config.include('columns.blog')
		self.config.include('columns.auth')
		self.request = testing.DummyRequest()
		self.request.session.update({
			'twitter_access_token': '123124',
			'twitter_access_token_secret': '123124',
		})
		response = twitter_login_view(self.request)
	
	def test_twitter_login_view_no_oauth_verifier(self):
		_populateSettings({'auth':{
			'FACEBOOK_APP_ID': 'qdefwrth',
			'FACEBOOK_APP_SECRET': 'qwrtyrt',
			'FACEBOOK_SCOPE': 'offline_access,publish_stream,read_stream',
			'TWITTER_CONSUMER_KEY': 'key',
			'TWITTER_CONSUMER_SECRET': 'secret',
			'TWITTER_REQUEST_TOKEN_URL': 'http://term.ie/oauth/example/request_token.php',
			'TWITTER_ACCESS_TOKEN_URL': 'http://term.ie/oauth/example/access_token.php?foo=bar&oauth_token=1234&oauth_token_secret=12345&user_id=1',
			'TWITTER_AUTHORIZE_URL': 'http://twitter.com/oauth/authorize',
			'DEFAULT_RETURN': '/',
		
		}})
		from columns.auth import twitter_login_view
		self.config.include('columns.blog')
		self.config.include('columns.auth')
		response = twitter_login_view(self.request)
		response = twitter_login_view(self.request)
	
	def test_twitter_login_view_bad_request_token(self):
		_populateSettings({'auth':{
			'FACEBOOK_APP_ID': 'qdefwrth',
			'FACEBOOK_APP_SECRET': 'qwrtyrt',
			'FACEBOOK_SCOPE': 'offline_access,publish_stream,read_stream',
			'TWITTER_CONSUMER_KEY': 'key',
			'TWITTER_CONSUMER_SECRET': 'secret',
			'TWITTER_REQUEST_TOKEN_URL': 'http://term.ie/oauth/example/not_a_request_token.php',
			'TWITTER_ACCESS_TOKEN_URL': 'http://term.ie/oauth/example/access_token.php?foo=bar&oauth_token=1234&oauth_token_secret=12345&user_id=1',
			'TWITTER_AUTHORIZE_URL': 'http://twitter.com/oauth/authorize',
			'DEFAULT_RETURN': '/',
		
		}})
		from columns.auth import twitter_login_view
		self.config.include('columns.blog')
		self.config.include('columns.auth')
		response = twitter_login_view(self.request)
		response = twitter_login_view(self.request)
	
	def test_facebook_login_view(self):
		from columns.auth import facebook_login_view
		#response = facebook_login_view(self.request)
	

class TestAuthorizationPolicy(unittest.TestCase):
	def setUp(self):
		self.request = testing.DummyRequest()
		self.config = testing.setUp(request=self.request)
		self.config.include('columns.lib.view')
		self.config.include('columns.auth')
		self.config.add_static_view('static', 'columns:static/')
		self.request.registry = self.config.registry
		self.session = _initTestingDB()
	
	def tearDown(self):
		self.session.remove()
		testing.tearDown()
	
	def _makePolicy(self):
		from columns.auth import AuthorizationPolicy
		from columns.auth import is_author
		from columns.auth import minimum_permission
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
	
	
	def test_xrds_view(self):
		from columns.auth import xrds_view
		response = xrds_view(self.request)
	
	def test_login_view(self):
		from columns.auth import login_view
		self.config.testing_add_renderer('templates/auth/login.jinja')
		response = login_view(self.request)
		self.assertEquals(response.status_int, 200)
	
	def test_logout_view(self):
		from columns.auth import logout_view
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
		context = DummyMember(name='1',parent=collection)
		response = policy.principals_allowed_by_permission(context, 'default')
		self.assertEquals(response, set([self.DEFAULT_PERMISSION]))
	
	def test_principals_allowed_member_composite(self):
		policy = self._makePolicy()
		collection = DummyCollection()
		collection.__name__ = 'test'
		context = DummyMember(name='1',parent=collection)
		context.author_id = 1
		response = policy.principals_allowed_by_permission(context, 'edit')
		self.assertEquals(response, set(['admin', 'super', 'editor', 1]))
	

class TestJinjaFuncs(unittest.TestCase):
	def setUp(self):
		self.request = testing.DummyRequest()
		self.config = testing.setUp(request=self.request)
		self.config.testing_securitypolicy(userid='1', permissive=True)
	
	def test_is_allowed(self):
		from columns.lib.view import is_allowed
		self.assertEquals(is_allowed('1'), True)
	
	def test_is_not_allowed(self):
		from columns.lib.view import is_not_allowed
		self.assertEquals(is_not_allowed('1'), False)
	

