# encoding: utf-8
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
