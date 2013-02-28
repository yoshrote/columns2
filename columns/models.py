# encoding: utf-8
import sqlahelper
import simplejson
import re
import datetime
import os.path
import shutil
import time
from lxml import etree
from lxml.html.soupparser import fromstring as soup_fromstring

from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.types import TypeDecorator
from sqlalchemy.types import Unicode
from sqlalchemy.types import UnicodeText
from sqlalchemy.types import Integer
from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.schema import Table
from sqlalchemy.schema import Column
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy import event
from pyramid.threadlocal import get_current_request
from pyramid.security import authenticated_userid
from zope.interface import implements
from .lib.interfaces import IMemberContext

from .lib import html

class AlwaysUnicode(TypeDecorator):
	impl = Unicode
	
	def process_bind_param(self, value, dialect):
		return unicode(value) if value is not None else None
	
	def process_result_value(self, value, dialect):
		return unicode(value) if value is not None else None
	
	def copy(self):
		return AlwaysUnicode(self.impl.length)
	

class AlwaysUnicodeText(TypeDecorator):
	impl = UnicodeText
	
	def process_bind_param(self, value, dialect):
		return unicode(value) if value is not None else None
	
	def process_result_value(self, value, dialect):
		return unicode(value) if value is not None else None
	
	def copy(self):
		return AlwaysUnicodeText(self.impl.length)
	

class MutationList(Mutable, list):
	@classmethod
	def coerce(cls, key, value):
		"Convert plain list to MutationList."
		if not isinstance(value, MutationList):
			if isinstance(value, list):
				return MutationList(value)
			# this call will raise ValueError
			return Mutable.coerce(key, value) # pragma: no cover
		else:
			return value
	
	def __setitem__(self, key, value):
		list.__setitem__(self, key, value)
		self.changed()
	
	def __delitem__(self, key):
		list.__delitem__(self, key)
		self.changed()
	
	def __getstate__(self):
		return list(self)
	
	def __setstate__(self, state):
		self.extend(state)
	
	def append(self, value):
		list.append(self, value)
		self.changed()
	

class MutationDict(Mutable, dict):
	@classmethod
	def coerce(cls, key, value):
		"Convert plain dictionaries to MutationDict."
		if not isinstance(value, MutationDict):
			if isinstance(value, dict):
				return MutationDict(value)
			# this call will raise ValueError
			return Mutable.coerce(key, value) # pragma: no cover
		else:
			return value
	
	def __setitem__(self, key, value):
		"Detect dictionary set events and emit change events."
		dict.__setitem__(self, key, value)
		self.changed()
	
	def __delitem__(self, key):
		"Detect dictionary del events and emit change events."
		dict.__delitem__(self, key)
		self.changed()
	
	def __getstate__(self):
		return dict(self)
	
	def __setstate__(self, state):
		self.update(state)
	

class JSONUnicode(TypeDecorator):
	impl = AlwaysUnicodeText
	
	def process_bind_param(self, value, dialect):
		value = str(simplejson.dumps(value, use_decimal=True)) if value is not None else None
		return value
	
	def process_result_value(self, value, dialect):
		try:
			value = simplejson.loads(value, use_decimal=True) if value is not None else None
			return value
		except simplejson.JSONDecodeError:
			return None
	
Base = sqlahelper.get_base()

url_host = None
def initialize_models(config):
	global url_host
	url_host = config['hostname']
	engine = sqlahelper.get_engine()
	Base.metadata.create_all(engine)

####################################
## Article Functions
####################################
re_slug = re.compile(r'[^a-z0-9\-]')
def slugify(string):
	tmp = string.lower().replace(' ', '-')
	return unicode(re_slug.sub(u'', tmp))

def create_atom_tag(host, date, value):
	slug = slugify(value)
	return ':'.join([
		'tag',
		', '.join([host.partition('/')[0], date.strftime('%Y-%m-%d')]),
		slug,
	])


####################################
## Default Value Functions
####################################
def get_author_id():
	request = get_current_request()
	return authenticated_userid(request)

def get_static_basepath():
	request = get_current_request()
	return request.registry.settings.get('upload_baseurl')

def get_author_data_from_user():
	user_id = get_author_id()
	session = sqlahelper.get_session()
	try:
		user = session.query(User).get(user_id)
		return {'id':user_id, 'name':user.name, 'uri':user.profile}
	except: # pragma: no cover
		return {}

def get_slug(context):
	return slugify(context.current_parameters['label'])

def get_page_slug(context):
	return slugify(context.current_parameters['title'])


####################################
## Updating Value Functions
####################################
def alter_contributor_value(target):
	author_data = get_author_data_from_user()
	user_id = author_data.get('id')
	contributors = target.contributors
	author_id = target.author_id
	already_contributed = any([user_id == x['id'] for x in contributors])
	is_author = user_id == author_id
	if author_data and not is_author and not already_contributed:
		target.contributors.append(author_data)


####################################
## ORM Model Classes
####################################
"""\
Dota Interface API:
	get_key -> 
		returns usable format of key for urls
	
	update_from_values(values) -> 
		returns itself with updated values from `values`
	
	buils_from_values(values) -> 
		returns itself with updated values from `values`
"""
article_tag_t = Table(
	'article_tag', Base.metadata,
	Column('article_id', Integer(), ForeignKey('article.id'), index=True),
	Column('tag_id', AlwaysUnicode(length=45), ForeignKey('tag.slug'), index=True),
)
upload_tag_t = Table(
	'upload_tag', Base.metadata,
	Column('upload_id', Integer(), ForeignKey('upload.id'), index=True),
	Column('tag_id', AlwaysUnicode(length=45), ForeignKey('tag.slug'), index=True),
)
class Tag(Base):
	__tablename__ = 'tag'
	slug = Column(
		AlwaysUnicode(length=255),
		nullable=False,
		primary_key=True,
		default=get_slug
	)
	label = Column(
		AlwaysUnicode(length=255),
		nullable=False
	)
	
	def to_json(self):
		return {
			'slug': self.slug,
			'label': self.label,
		}
	

class Article(Base):
	implements(IMemberContext)
	__tablename__ = 'article'
	
	id = Column(
		Integer(),
		primary_key=True,
		autoincrement=True
	)
	atom_id = Column(
		AlwaysUnicode(length=255)
	)
	created = Column(
		DateTime(),
		nullable=False,
		index=True,
		default=datetime.datetime.utcnow
	)
	updated = Column(
		DateTime(),
		nullable=False,
		index=True,
		default=datetime.datetime.utcnow,
		onupdate=datetime.datetime.utcnow
	)
	author_id = Column(
		Integer(),
		ForeignKey('user.id'),
		nullable=True,
		default=get_author_id
	)
	author_meta = Column(
		MutationDict.as_mutable(JSONUnicode),
		nullable=False,
		default=get_author_data_from_user
	)
	contributors = Column(
		MutationList.as_mutable(JSONUnicode),
		nullable=False,
		default=list
	)
	
	title = Column(
		AlwaysUnicode(length=255),
		nullable=False
	)
	published = Column(
		DateTime(),
		nullable=True,
		index=True
	)
	content = Column(
		AlwaysUnicodeText(),
		nullable=False,
		default=u''
	)	
	sticky = Column(
		Boolean(),
		nullable=False,
		default=False
	)
	permalink = Column(
		AlwaysUnicode(length=255),
		nullable=True
	)
	
	@property
	def summary(self):
		tree = soup_fromstring(self.content or '')
		hr = tree.find(".//hr")
		if hr is not None:
			for i, x in enumerate(hr.itersiblings()):
				x.getparent().remove(x)
			hr.getparent().remove(hr)
		return etree.tostring(tree)[6:-7]
	
	@property
	def metacontent(self):
		return html.striphtml(self.content)
	
	def to_json(self):
		return {
			'id': self.id,
			'atom_id': self.atom_id,
			'author_id': self.author_id,
			'created': self.created,
			'updated': self.updated,
			'author': self.author_meta,
			'contributors': self.contributors,
			'title': self.title,
			'published': self.published,
			'content': self.content,
			'summary': self.summary,
			'sticky': self.sticky,
			'permalink': self.permalink,
			'tags': list(self.tags),
		}
	
	
	def get_key(self):
		return unicode(self.id)
	
	def set_key(self, key):
		self.id = int(key)
	
	def update_from_values(self, values):
		tags = set([Tag(slug=slugify(tag), label=tag) for tag in values.pop('tags', [])])
		if values.get('published'):
			values['published'] = values['published'].replace(tzinfo=None)
		for k, v in values.items():
			if not k.startswith('_') and hasattr(self, k) and k != 'author_id':
				setattr(self, k, v)
		alter_contributor_value(self)
		
		return self
	
	def build_from_values(self, values):
		if values.get('published'):
			values['published'] = values['published'].replace(tzinfo=None)
		return self.update_from_values(values)
	

class Upload(Base):
	implements(IMemberContext)
	__tablename__ = 'upload'
	
	id = Column(
		Integer(),
		nullable=False,
		primary_key=True,
		autoincrement=True
	)
	atom_id = Column(
		AlwaysUnicode(length=255),
		nullable=True
	)
	created = Column(
		DateTime(),
		nullable=False,
		index=True,
		default=datetime.datetime.utcnow
	)
	updated = Column(
		DateTime(),
		nullable=False,
		index=True,
		default=datetime.datetime.utcnow,
		onupdate=datetime.datetime.utcnow
	)
	author_id = Column(
		Integer(),
		ForeignKey('user.id'),
		default=get_author_id
	)
	author_meta = Column(
		MutationDict.as_mutable(JSONUnicode),
		nullable=False,
		default=get_author_data_from_user
	)
	
	title = Column(
		AlwaysUnicode(length=255),
		nullable=False
	)
	content = Column(
		AlwaysUnicodeText(),
		nullable=False,
		default=u''
	)	
	filepath = Column(
		AlwaysUnicode(length=255),
		nullable=False
	)
	
	def to_json(self):
		return {
			'id': self.id,
			'atom_id': self.atom_id,
			'created': self.created,
			'updated': self.updated,
			'author': self.author_meta,
			'title': self.title,
			'content': self.content,
			'filepath': self.filepath,
			'tags': list(self.tags),
			'static_base': get_static_basepath(),
		}
	
	
	def get_key(self):
		return unicode(self.id)
	
	def set_key(self, key):
		self.id = int(key)
	
	def update_from_values(self, values):
		for k, v in values.items():
			if not k.startswith('_') and hasattr(self, k):
				setattr(self, k, v)
		
		return self
	
	def build_from_values(self, values, request=None):
		upload = values.pop('file')
		self = self.update_from_values(values)
		if request is None:
			request = self.__parent__.request
		basepath = request.registry.settings.get('upload_basepath')
		today = datetime.date.today()
		relative_path = os.path.join(
			str(today.year), str(today.month).zfill(2)
		)
		basename = '_'.join([
			str(int(time.time())),
			upload.filename.replace(os.sep, '_')
		])
		self.filepath = os.path.join(
			relative_path, basename
		)
		absolute_path = os.path.join(basepath, relative_path)
		if not os.path.exists(absolute_path): # pragma: no cover
			os.makedirs(absolute_path)
		full_absolute_path = os.path.join(absolute_path, basename)
		permanent_file = open(full_absolute_path, 'wb')
		shutil.copyfileobj(upload.file, permanent_file)
		upload.file.close()
		permanent_file.close()
		return self
	

class Setting(Base):
	__tablename__ = 'setting'
	
	module = Column(
		AlwaysUnicode(length=255),
		nullable=False,
		primary_key=True
	)
	config = Column(
		MutationDict.as_mutable(JSONUnicode),
		nullable=False
	)

class Page(Base):
	implements(IMemberContext)
	__tablename__ = 'page'
	
	id = Column(
		Integer(),
		autoincrement=True,
		primary_key=True,
		nullable=False
	)
	title = Column(
		AlwaysUnicode(length=255),
		nullable=False
	)
	slug = Column(
		AlwaysUnicode(length=255),
		nullable=False,
		unique=True,
		default=get_page_slug,
	)
	content = Column(
		AlwaysUnicodeText(),
		nullable=True
	)
	visible = Column(
		Boolean(),
		default=True,
		nullable=False
	)
	can_post = Column(
		Boolean(),
		default=True,
		nullable=False
	)
	in_main = Column(
		Boolean(),
		default=True,
		nullable=False
	)
	in_menu = Column(
		Boolean(),
		default=False,
		nullable=False
	)
	
	def to_json(self):
		return {
			'id': self.id,
			'title': self.title,
			'slug': self.slug,
			'content': self.content,
			'visible': self.visible,
			'can_post': self.can_post,
			'in_main': self.in_main,
			'in_menu': self.in_menu,
		}
	
	
	def get_key(self):
		return unicode(self.id)
	
	def set_key(self, key):
		self.id = int(key)
	
	def update_from_values(self, values):
		for k, v in values.items():
			if not k.startswith('_') and hasattr(self, k):
				setattr(self, k, v)
		
		return self
	
	def build_from_values(self, values):
		return self.update_from_values(values)
	

class User(Base):
	implements(IMemberContext)
	__tablename__ = 'user'
	
	id = Column(
		Integer(),
		autoincrement=True,
		primary_key=True,
		nullable=False
	)
	name = Column(
		AlwaysUnicode(length=255),
		nullable=True,
		unique=True
	)
	open_id = Column(
		AlwaysUnicode(length=255),
		nullable=True,
		index=True
	)
	type = Column(
		Integer(),
		nullable=False
	)
	profile = Column(
		AlwaysUnicode(length=255),
		nullable=True
	)
	
	def to_json(self):
		return {
			'id': self.id,
			'name': self.name,
			'open_id': self.open_id,
			'type': self.type,
			'profile': self.profile,
		}
	
	
	def get_key(self):
		return unicode(self.id)
	
	def set_key(self, key):
		self.id = int(key)
	
	def update_from_values(self, values):
		for k, v in values.items():
			if not k.startswith('_') and hasattr(self, k):
				setattr(self, k, v)
		
		return self
	
	def build_from_values(self, values):
		return self.update_from_values(values)
	

Article.tags = relationship(
	Tag,
	secondary=article_tag_t,
	collection_class=set,
	backref=backref('articles', lazy='dynamic')
)
Article.author = relationship(
	User,
	primaryjoin=Article.author_id==User.id,
	backref=backref('articles', lazy='dynamic'),
	single_parent=True,
	uselist=False
)
Upload.tags = relationship(
	Tag,
	secondary=upload_tag_t,
	collection_class=set,
	backref=backref('uploads', lazy='dynamic')
)
Upload.author = relationship(
	User,
	backref=backref('uploads', lazy='dynamic'),
	single_parent=True,
	uselist=False
)

####################################
## ORM Event Handlers
####################################
def trigger_article(mapper, connection, target):
	if target.title and target.published and not target.permalink:
		slug = slugify(target.title)
		dt_str = target.published.strftime('%Y-%m-%d')
		target.permalink = '-'.join([dt_str, slug])
		target.atom_id = 'tag:{host},{date}:{path}'.format(
			host=url_host,
			date=target.published.strftime('%Y-%m-%d'),
			path=target.permalink,
		)
	target.updated = datetime.datetime.utcnow()

event.listen(Article, 'before_insert', trigger_article)
event.listen(Article, 'before_update', trigger_article)

def upload_before_insert(mapper, connection, target):
	title = target.title or os.path.basename(target.filepath)
	if target.created is None:
		target.created = datetime.datetime.utcnow()
	try:
		request = get_current_request()
		host = request.host
	except:
		target.atom_id = create_atom_tag('localhost', target.created, title)
	else:
		target.atom_id = create_atom_tag(host, target.created, title)
	
event.listen(Upload, 'before_insert', upload_before_insert)
