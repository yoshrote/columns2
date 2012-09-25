# encoding: utf-8
from zope.interface import implements

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.interfaces import IAuthorizationPolicy
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.httpexceptions import exception_response
from pyramid.renderers import render_to_response
from pyramid.response import Response
from pyramid.compat import json

from pyramid.security import Allow
from pyramid.security import Deny
from pyramid.security import Everyone
from pyramid.security import Authenticated
from pyramid.security import authenticated_userid
from pyramid.security import remember
from pyramid.security import forget

import logging
import sqlahelper
from sqlalchemy.exc import InvalidRequestError
from .models import User

LOG = logging.getLogger(__name__)

#############################
## Authentication Policy 
#############################
PERMISSIONS = {
	'super': 1,
	'admin': 2,
	'editor': 3,
	'author': 4,
	'probation': 8,
	'subscriber': 9
}
DEFAULT_PERMISSION = Everyone
DEFAULT_USER_TYPE = 'subscriber'
def get_permissions():
	return dict([(v,k) for k,v in PERMISSIONS.items()])

class SessionAuthenticationPolicy(CallbackAuthenticationPolicy):
	implements(IAuthenticationPolicy)
	def __init__(self, prefix='auth.', debug=False):
		self.prefix = prefix or ''
		self.userid_key = prefix + 'userid'
		self.debug = debug
	
	def callback(self, userid, request):
		DBSession = sqlahelper.get_session()
		principals = [userid]
		auth_type = request.session.get('auth.type')
		#load user into cache
		if not auth_type:
			request.session[self.userid_key] = userid
			user = DBSession.query(User).get(userid)
			if user is None:
				return principals
			request.session['auth.type'] = auth_type = user.type
		
		# add in principles according to session stored variables
		inv_permission = get_permissions()
		principals.append(inv_permission.get(request.session['auth.type'], DEFAULT_USER_TYPE))
		LOG.debug('User principals: %r', principals)
		return principals
	
	def remember(self, request, principal, **kw):
		""" Store a principal in the session."""
		auth_type = request.session.get('auth.type')
		#load user into cache
		LOG.debug('auth_type = %r', auth_type)
		if not auth_type:
			user = find_user('id', principal, create=kw.get('create',False))
			if isinstance(user, User):
				request.session[self.userid_key] = principal
				request.session['auth.type'] = user.type
				request.session['auth.name'] = user.name
			LOG.debug('session info: %r', request.session)
		return []
	
	def forget(self, request):
		""" Remove the stored principal from the session."""
		for key in request.session.keys():
			if key.startswith(self.prefix):
				del request.session[key]
		return []
	
	def unauthenticated_userid(self, request):
		return request.session.get(self.userid_key)
	

def find_user(attribute, value, create=False):
	DBSession = sqlahelper.get_session()
	try:
		LOG.debug('Looking for user where %s=%r', attribute, value)
		user = DBSession.query(User).filter(getattr(User, attribute)==value).one()
	except InvalidRequestError:
		if create:
			# this is a new user
			user = User()
			setattr(user, attribute, value)
			user.type = PERMISSIONS[DEFAULT_USER_TYPE]
			user = DBSession.merge(user)
			DBSession.commit()
			return user
		else:
			return None
	else:
		LOG.debug('User found: %r', user.name)
	return user


#############################
## Authentication Views 
#############################
def settings_module(mod='core'):
	from .models import Setting
	Session = sqlahelper.get_session()
	module = Session.query(Setting).get(mod)
	setting_dict = getattr(module, 'config', {})
	return setting_dict

def xrds_view(request):
	return Response("""<?xml version="1.0" encoding="UTF-8"?>
<xrds:XRDS
	xmlns:xrds="xri://$xrds"
	xmlns:openid="http://openid.net/xmlns/1.0"
	xmlns="xri://$xrd*($v*2.0)">
	<XRD>
		<Service priority="1">
			<Type>http://specs.openid.net/auth/2.0/return_to</Type>
			<URI>{uri}</URI>
		</Service>
	</XRD>
</xrds:XRDS>""".format(uri=request.host_url))


def oid_authentication_callback(context, request, success_dict):
	"""\
	success_dict = {
		'identity_url': info.identity_url,
		'ax': {},
		'sreg': {}
	}
	"""
	user = find_user('open_id', success_dict['identity_url'])
	if user:
		# use standard auth callback to populate session
		#authentication_callback(user.id, request)
		remember(request, user.id)
		return exception_response(302, location=request.route_url('admin'))
	else:
		error_response = "This login is not authorized.\nEmail this to josh@nerdblerp.com: '%s'" % success_dict['identity_url']
		return exception_response(401, body=error_response)
	
def logout_view(request):
	forget(request)
	if request.is_xhr:
		return exception_response(200)
	return exception_response(302, location=request.route_url('admin'))

def whoami_view(request):
	user_type = request.session.get('auth.type')
	if user_type:
		return {
			'id': request.session.get('auth.userid'),
			'user': request.session.get('auth.name'),
			'type': user_type,
		}
	return {}


#############################
## Authorization Policy 
#############################
def minimum_permission(permission_name):
	val = PERMISSIONS.get(permission_name, DEFAULT_USER_TYPE)
	return set([k for k,v in PERMISSIONS.items() if v <= val])

def is_author(context):
	return set([context.author_id])

POLICY_MAP = {
	None: {
		'default': set([DEFAULT_PERMISSION]),
		'settings': [minimum_permission('super')],
		'admin': [minimum_permission('probation')],
	},
	'articles': {
		'index': [minimum_permission('probation')],
		'show': [minimum_permission('probation')],
		'new': [minimum_permission('probation')],
		'create': [minimum_permission('probation')],
		'edit': [minimum_permission('editor'), is_author],
		'update': [minimum_permission('editor'), is_author],
 		'delete': [minimum_permission('editor'), is_author],
		'publish': [minimum_permission('editor'), is_author],
	},
	'pages':  {
		'index': [minimum_permission('probation')],
		'show': [minimum_permission('probation')],
		'new': [minimum_permission('admin')],
		'create': [minimum_permission('admin')],
		'edit': [minimum_permission('admin')],
		'update': [minimum_permission('admin')],
		'delete': [minimum_permission('admin')],
	},
	'users':  {
		'index': [minimum_permission('admin')],
		'show': [minimum_permission('admin')],
		'new': [minimum_permission('admin')],
		'create': [minimum_permission('admin')],
		'edit': [minimum_permission('admin')],
		'update': [minimum_permission('admin')],
		'delete': [minimum_permission('admin')],
	},
	'uploads':  {
		'index': [minimum_permission('probation')],
		'show': [minimum_permission('probation')],
		'new': [minimum_permission('probation')],
		'create': [minimum_permission('probation')],
		'edit': [minimum_permission('probation')],
		'update': [minimum_permission('probation')],
		'delete': [minimum_permission('editor')],
	},
}

class AuthorizationPolicy(object):
	"""An authorization policy
	"""
	implements(IAuthorizationPolicy)
	def __init__(self, policy_map=None):
		self.policy_map = policy_map if policy_map else POLICY_MAP
	
	def permits(self, context, principals, permission):
		allowed_principals = self.principals_allowed_by_permission(context, permission)
		LOG.debug('Permission: %s\nContext: %s\nPrincipals: %s\nAllowed Principals: %s', permission, context, principals, allowed_principals)
		return bool(set(principals).intersection(allowed_principals))
	
	def principals_allowed_by_permission(self, context, permission):
		if context is None:
			context_name = None
		elif getattr(context,'__parent__',None):
			context_name = context.__parent__.__name__
		else:
			context_name = context.__name__
		LOG.debug('Context: %s', context_name)
		permission_context = self.policy_map.get(context_name, self.policy_map[None])
		LOG.debug('Policy: %r', permission_context)

		try:
			principals = []
			for perm in permission_context[permission]:
				if callable(perm):
					principals.extend(perm(context))
				else:
					principals.extend(perm)
			return set(principals)
		except KeyError:
			return self.policy_map[None]['default']
	


#############################
## Auth Config 
#############################
from pyramid.events import NewResponse
def debug_sessions(event):
	LOG.debug('Session: %r', event.request.session)
	event.request.session.pop('_f_', None)

def includeme(config):
	if config.get_settings().get('enable_auth', True):
		config.set_authorization_policy(AuthorizationPolicy(POLICY_MAP))
		config.set_authentication_policy(SessionAuthenticationPolicy())
		config.add_subscriber(debug_sessions, NewResponse)

	config.add_route('logout', '/logout')
	config.add_view(
		'columns.auth.logout_view',
		route_name='logout',
	)

	config.add_route('whoami', '/whoami')
	config.add_view(
		'columns.auth.whoami_view',
		route_name='whoami',
		renderer='json'
	)
	
	config.add_route(
		'verify_openid',
		pattern='openid',
	)
	config.add_view(
		'pyramid_openid.verify_openid',
		route_name='verify_openid',
	)
	
	config.add_route('xrds', '/xrds.xml')
	config.add_view(
		'columns.auth.xrds_view',
		route_name='xrds',
	)

