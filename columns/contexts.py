import sqlahelper
from pyramid.httpexceptions import exception_response

from columns.lib.base import SQLACollectionContext
from columns.lib.base import BaseViews
from columns.lib.base import InvalidResource

from columns.lib.form import Form
from columns.forms import CreateUser
from columns.forms import UpdateUser
from columns.forms import CreateArticle
from columns.forms import UpdateArticle
from columns.forms import CreatePage
from columns.forms import UpdatePage
from columns.forms import CreateUpload
from columns.forms import UpdateUpload

from columns.models import Article
from columns.models import Page
from columns.models import Upload
from columns.models import User

import os.path
import datetime
import time
import shutil
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
	def index(self, offset=None, limit=None):
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
		
		query = query.offset(offset).limit(limit)
		
		results = []
		for item in query:
			item.__parent__ = self
			item.__name__ = item.get_key()
			results.append(item)
		
		return results
	
	def __delitem__(self, key):
		id = self._decode_key(key)
		Session = sqlahelper.get_session()
		resource = Session.query(
			Article
		).get(id)
		Session.delete(resource)
		Session.commit()
	

class PageCollectionContext(SQLACollectionContext):
	__model__ = 'columns.models:Page'
	__name__ = 'pages'

class UploadCollectionContext(SQLACollectionContext):
	__model__ = 'columns.models:Upload'
	__name__ = 'uploads'
	
	def __delitem__(self, key):
		id = self._decode_key(key)
		Session = sqlahelper.get_session()
		resource = Session.query(
			self.__model__
		).get(id)
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
		
		if create_form.validate(force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdateArticle(), 
		)
		
		if update_form.validate(force_validate=True):
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
		
		if create_form.validate(force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdatePage(), 
		)
		
		if update_form.validate(force_validate=True):
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
		
		if create_form.validate(force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdateUpload(), 
		)
		
		if update_form.validate(force_validate=True):
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
		
		if create_form.validate(force_validate=True):
			return create_form.data
		else:
			raise InvalidResource(create_form)
	
	def _update_values_from_request(self):
		update_form = Form(
			self.request, 
			schema=UpdateUser(), 
		)
		
		if update_form.validate(force_validate=True):
			return update_form.data
		else:
			raise InvalidResource(update_form)
	
	def _create_values_from_atom(self):
		raise exception_response(501)
	
	def _update_values_from_atom(self):
		raise exception_response(501)
	

