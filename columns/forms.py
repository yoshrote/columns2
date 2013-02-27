# encoding: utf-8
import colander
from .lib.validators import StrippingString, StringList, HTMLString, FieldStorage

########################################
## Article Schema 
########################################
class CreateArticle(colander.MappingSchema):
	title = colander.SchemaNode(
		StrippingString(),
		validator=colander.Length(max=255)
	)
	published = colander.SchemaNode(
		colander.DateTime(),
		missing=None
	)
	content = colander.SchemaNode(
		HTMLString()
	)
	sticky = colander.SchemaNode(
		colander.Boolean(),
		missing=False
	)
	tags = colander.SchemaNode(
		StringList(),
		missing=[]
	)

class UpdateArticle(CreateArticle):
	pass


########################################
## User Schema 
########################################
class CreateUser(colander.MappingSchema):
	name = colander.SchemaNode(
		StrippingString(),
		validator=colander.Length(max=255)
	)
	type = colander.SchemaNode(
		colander.Integer(),
	)
	open_id = colander.SchemaNode(
		StrippingString(),
		validator=colander.Length(max=255),
		missing=None
	)
	profile = colander.SchemaNode(
		StrippingString(),
		validator=colander.Length(max=255),
		missing=None
	)

class UpdateUser(CreateUser):
	pass


########################################
## Page Schema 
########################################
class CreatePage(colander.MappingSchema):
	title = colander.SchemaNode(
		StrippingString(),
		validator=colander.Length(max=255)
	)
	content = colander.SchemaNode(
		HTMLString()
	)
	visible = colander.SchemaNode(
		colander.Boolean(),
		missing=False
	)
	can_post = colander.SchemaNode(
		colander.Boolean(),
		missing=False
	)
	in_main = colander.SchemaNode(
		colander.Boolean(),
		missing=False
	)
	in_menu = colander.SchemaNode(
		colander.Boolean(),
		missing=False
	)

class UpdatePage(CreatePage):
	pass


########################################
## Upload Schema 
########################################
class UpdateUpload(colander.MappingSchema):
	title = colander.SchemaNode(
		StrippingString(),
		validator=colander.Length(max=255)
	)
	content = colander.SchemaNode(
		StrippingString(),
		missing=u''
	)
	tags = colander.SchemaNode(
		StringList(),
		missing=[]
	)

class CreateUpload(UpdateUpload):
	file = colander.SchemaNode(
		FieldStorage()
	)


