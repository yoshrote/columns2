# encoding: utf-8
import sqlahelper
from pyramid.httpexceptions import exception_response
from pyramid.security import has_permission

from .lib.base import SQLACollectionContext
from .lib.base import BaseViews
from .lib.base import InvalidResource

from .lib.form import Form
from .forms import CreateUser
from .forms import UpdateUser
from .forms import CreateArticle
from .forms import UpdateArticle
from .forms import CreatePage
from .forms import UpdatePage
from .forms import CreateUpload
from .forms import UpdateUpload

from .models import Article
from .models import Page
from .models import Upload
from .models import User

import os.path
from lxml import etree
from urllib import unquote

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
	def index(self, offset=None, limit=None, query_spec=None):
		def int_or_none(val):
			try:
				return int(val)
			except (TypeError,ValueError):
				return None
		
		Session = sqlahelper.get_session()
		query = Session.query(self.__model__)
		drafts = bool(int_or_none(self.request.GET.get('drafts')))
		query = query.filter(Article.published == None) if drafts \
			else query.filter(Article.published != None)
		
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
	
	def __delitem__(self, key):
		id_ = self._decode_key(key)
		Session = sqlahelper.get_session()
		resource = Session.query(
			Article
		).get(id_)
		if resource is None:
			raise KeyError(key)
		Session.delete(resource)
		try:
			Session.commit()
		except Exception, ex: # pragma: no cover
			Session.rollback()
			raise ex

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
		resource_path = os.path.join(basepath,resource.filepath)
		Session.delete(resource)
		Session.commit()
		os.remove(resource_path)

class UserCollectionContext(SQLACollectionContext):
	__model__ = 'columns.models:User'
	__name__ = 'users'

########################################
## Views
########################################
class ArticleViews(BaseViews):
	def _create_values_from_request(self):
		create_form = Form(
			self.request, 
			schema=CreateArticle()
		)
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if create_form.validate(params=params, force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdateArticle(), 
		)
		
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if update_form.validate(params=params, force_validate=True):
			return update_form.data
		else:
			raise InvalidResource(update_form)
	
	def _create_values_from_atom(self):
		tree = etree.fromstring(self.request.body)
		values = {}
		title_el = tree.xpath(
			"/atom:entry/atom:title",
			namespaces={'atom':"http://www.w3.org/2005/Atom"}
		)
		content_el = tree.xpath(
			"/atom:entry/atom:content",
			namespaces={'atom':"http://www.w3.org/2005/Atom"}
		)
		tags_el = tree.xpath(
			"/atom:entry/atom:category",
			namespaces={'atom':"http://www.w3.org/2005/Atom"}
		)
		draft_el = tree.xpath(
			"/atom:entry/app:draft",
			namespaces={
				'atom':"http://www.w3.org/2005/Atom",
				'app':"http://www.w3.org/2007/app"
			}
		)
		
		if draft_el:
			values['published'] = draft_el[0].text == "no"
		values['tags'] = ', '.join([
			tag.attrib.get('label',tag.attrib.get('term')) for tag in tags_el
		])
		
		try:
			values['title'] = unquote(title_el[0].text)
			formatting = content_el[0].attrib.get('type','text')
			values['content'] = \
				content_el[0].text if formatting == 'xhtml' \
				else unquote(content_el[0].text)
		except IndexError:
			pass
		
		create_form = Form(self.request, schema=CreateArticle())
		if create_form.validate(force_validate=True, params=values):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_atom(self):
		tree = etree.fromstring(self.request.body)
		values = {}
		title_el = tree.xpath(
			"/atom:entry/atom:title",
			namespaces={'atom':"http://www.w3.org/2005/Atom"}
		)
		content_el = tree.xpath(
			"/atom:entry/atom:content",
			namespaces={'atom':"http://www.w3.org/2005/Atom"}
		)
		tags_el = tree.xpath(
			"/atom:entry/atom:category",
			namespaces={'atom':"http://www.w3.org/2005/Atom"}
		)
		draft_el = tree.xpath(
			"/atom:entry/app:draft",
			namespaces={
				'atom':"http://www.w3.org/2005/Atom",
				'app':"http://www.w3.org/2007/app"
			}
		)
		
		if draft_el:
			values['published'] = None
		values['tags'] = ', '.join([
			tag.attrib.get('label',tag.attrib.get('term')) for tag in tags_el
		])
		
		try:
			values['title'] = unquote(title_el[0].text)
			formatting = content_el[0].attrib.get('type','text')
			values['content'] = \
				content_el[0].text if formatting == 'xhtml' \
				else unquote(content_el[0].text)
		except IndexError:
			pass
		
		update_form = Form(self.request, schema=UpdateArticle())
		if update_form.validate(force_validate=True, params=values):
			return update_form.data
		else:
			raise InvalidResource(update_form)

class PageViews(BaseViews):
	def _create_values_from_request(self):
		create_form = Form(
			self.request, 
			schema=CreatePage()
		)
		
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if create_form.validate(params=params, force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdatePage(), 
		)
		
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if update_form.validate(params=params, force_validate=True):
			return update_form.data
		else:
			raise InvalidResource(update_form)
	
	def _create_values_from_atom(self):
		raise exception_response(501)
	
	def _update_values_from_atom(self):
		raise exception_response(501)

class UploadViews(BaseViews):
	def _create_values_from_request(self):
		create_form = Form(
			self.request, 
			schema=CreateUpload()
		)
		
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if create_form.validate(params=params, force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdateUpload(), 
		)
		
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if update_form.validate(params=params, force_validate=True):
			return update_form.data
		else:
			raise InvalidResource(update_form)
	
	def _create_values_from_atom(self):
		raise exception_response(501)
	
	def _update_values_from_atom(self):
		raise exception_response(501)

class UserViews(BaseViews):
	def _create_values_from_request(self):
		create_form = Form(
			self.request, 
			schema=CreateUser()
		)
		
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if create_form.validate(params=params, force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdateUser(), 
		)
		
		params = self.request.json_body if 'json' in self.request.content_type else None
		
		if update_form.validate(params=params, force_validate=True):
			return update_form.data
		else:
			raise InvalidResource(update_form)
	
	def _create_values_from_atom(self):
		raise exception_response(501)
	
	def _update_values_from_atom(self):
		raise exception_response(501)
