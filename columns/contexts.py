# encoding: utf-8
import sqlahelper

from .lib.context_impl.sqla import SQLACollectionContext
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

import os.path

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
