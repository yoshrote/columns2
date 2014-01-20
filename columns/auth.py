# encoding: utf-8
from zope.interface import implements

from pyramid.interfaces import IAuthorizationPolicy
from pyramid.httpexceptions import exception_response

from pyramid.security import Everyone
from pyramid.security import remember
from pyramid.security import forget

import logging
import sqlahelper

from pyramid.util import DottedNameResolver
dotted_resolver = DottedNameResolver(None)

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
DEFAULT_USER_TYPE = 'subscriber'
DEFAULT_PERMISSION = [set([Everyone])]
def get_permissions():
    return dict([(v, k) for k, v in PERMISSIONS.items()])


#############################
## Authentication Views 
#############################
def oid_authentication_callback(context, request, success_dict):
    """\
    success_dict = {
        'identity_url': info.identity_url,
        'ax': {},
        'sreg': {}
    }
    """
    LOG.debug("looking for user")
    find_user = dotted_resolver.maybe_resolve(request.registry.settings['models.find_user'])
    user = find_user('open_id', success_dict['identity_url'])
    if user:
        LOG.info("found user")
        # use standard auth callback to populate session
        #authentication_callback(user.id, request)
        remember(request, user.id)
        return exception_response(200)
    else:
        LOG.debug("invalid login")
        error_response = "This login is not authorized.\nEmail this to josh@nerdblerp.com: '%s'" % success_dict['identity_url']
        return exception_response(401, body=error_response)
    
def logout_view(request):
    forget(request)
    return exception_response(200)

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
    return set([k for k, v in PERMISSIONS.items() if v <= val])

def is_author(context):
    return set([context.author_id])

POLICY_MAP = {
    None: {
        'default': DEFAULT_PERMISSION,
        'settings': [minimum_permission('super')],
        'admin': [minimum_permission('probation')],
    },
    'articles': {
        'index': DEFAULT_PERMISSION, #[minimum_permission('probation')],
        'show': DEFAULT_PERMISSION, #[minimum_permission('probation')],
        'new': [minimum_permission('probation')],
        'create': [minimum_permission('probation')],
        'edit': [minimum_permission('editor'), is_author],
        'update': [minimum_permission('editor'), is_author],
        'delete': [minimum_permission('editor'), is_author],
        'publish': [minimum_permission('editor'), is_author],
    },
    'pages':  {
        'index': DEFAULT_PERMISSION, #[minimum_permission('probation')],
        'show': DEFAULT_PERMISSION, #[minimum_permission('probation')],
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
        elif getattr(context, '__parent__', None):
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
    SessionAuthenticationPolicy = dotted_resolver.maybe_resolve(config.registry.settings['models.session_policy'])
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
        renderer='columns:templates/xrds.jinja',
        route_name='xrds',
    )

