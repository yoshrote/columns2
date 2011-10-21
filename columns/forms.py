# encoding: utf-8
import colander
from lxml import etree
import cgi
from BeautifulSoup import BeautifulSoup

class StrippingString(colander.String):
	def deserialize(self, node, cstruct):
		result = super(StrippingString, self).deserialize(node, cstruct)
		if result:
			return result.strip()
		else:
			return result
	

class FieldStorage(object):
	"""
	Handles cgi.FieldStorage instances that are file uploads.
	
	This doesn't do any conversion, but it can detect empty upload
	fields (which appear like normal fields, but have no filename when
	no upload was given).
	"""
	def deserialize(self, node, cstruct):
		if cstruct is colander.null:
			return cstruct
		if not isinstance(cstruct, cgi.FieldStorage) or \
			not getattr(cstruct, 'filename', None):
			raise colander.Invalid(
				node, 
				'%r is not a FieldStorage instance' % cstruct
			)
		return cstruct
	


class StringList(colander.String):
	def deserialize(self, node, cstruct):
		if cstruct is colander.null:
			return cstruct
		return [
			super(StringList, self).deserialize(node, x).strip() 
			for x in cstruct.split(",") if x.strip() != ""
		]
	

class HTMLString(colander.String):
	def deserialize(self, node, cstruct):
		if cstruct is colander.null:
			return cstruct
		text = super(HTMLString, self).deserialize(node, cstruct)
		try:
			soup = etree.fromstring(u"<div>%s</div>" % text)
			return etree.tostring(soup, encoding=unicode)[5:-6]
		except: # pragma: no cover
			soup = BeautifulSoup(text)
			return unicode(soup)
		


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
	can_comment = colander.SchemaNode(
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
	fb_id = colander.SchemaNode(
		StrippingString(),
		validator=colander.Length(max=255),
		missing=None
	)
	twitter_id = colander.SchemaNode(
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
	stream_comment_style = colander.SchemaNode(
		StrippingString(),
		validator=colander.OneOf(['summary','list','none'])
	)
	story_comment_style = colander.SchemaNode(
		StrippingString(),
		validator=colander.OneOf(['summary','list','none'])
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


