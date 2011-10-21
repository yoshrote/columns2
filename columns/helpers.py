# encoding: utf-8
from webhelpers.html.tools import button_to
from webhelpers.html.tags import javascript_link
from webhelpers.html.tags import stylesheet_link
from webhelpers.html.tags import link_to
from webhelpers.html.tags import image
from webhelpers.html.tags import submit
from webhelpers.html.tags import file
from webhelpers.html.tags import text
from webhelpers.html.tags import textarea
from webhelpers.html.tags import hidden
from webhelpers.html.tags import select
from webhelpers.html.tags import checkbox
from webhelpers.html.tags import password
from webhelpers.html.tags import form
from webhelpers.html.tags import end_form

from pyramid.security import effective_principals
from pyramid.security import unauthenticated_userid
from pyramid.security import authenticated_userid

from columns.auth import get_permissions

#############################
## Blog Helpers
#############################
def main_pages():
	import sqlahelper
	from columns.models import Page
	Session = sqlahelper.get_session()
	pages = Session.query(Page.slug, Page.title).\
		filter(Page.in_main == True).\
		all()
	return [(slug,title) for slug, title in pages]

'''
def top_tags(top_count=5):
	import sqlahelper
	from sqlalchemy import sql
	from columns.models import Tag
	from columns.models import article_tag_t
	Session = sqlahelper.get_session()
	
	tag_counts = Session.query(Tag,sql.func.count('*').label('counter')).\
		join(article_tag_t).\
		group_by(Tag.slug).\
		order_by('counter DESC').\
		limit(top_count).all()
	return [(tag.slug,tag.label) for tag, counter in tag_counts]

def top_authors(top_count=5):
	import sqlahelper
	from sqlalchemy import sql
	from columns.models import User
	from columns.models import Article
	Session = sqlahelper.get_session()
	
	user_counts = Session.query(User,sql.func.count().label('counter')).\
		join(Article).\
		group_by(Article.author_id).\
		order_by('counter DESC').\
		limit(top_count).all()
	return [user.name for user, counter in user_counts]

'''
