# encoding: utf-8
from pyramid.response import Response
from pyramid.renderers import get_renderer
from pyramid.threadlocal import get_current_request
from pyramid.url import static_url
from pyramid.traversal import resource_path
from pyramid.security import has_permission
from operator import attrgetter as op_attrgetter
import colander
import datetime
import pytz
from pyramid.compat import json

# To auto-load the filters and tests
def includeme(config):
	"""Setup template paths and add all custom tests and filters into the 
	environment.
	"""
	
	config.include('pyramid_jinja2')
	config.add_renderer('json', json_renderer_factory)
	config.add_renderer('.jinja', 'pyramid_jinja2.renderer_factory')
	jinja_env = config.get_jinja2_environment()
	
	#globals
	import columns.helpers
	jinja_env.globals['h'] = columns.helpers
	jinja_env.globals['app_settings'] = app_settings
	jinja_env.globals['request'] = get_current_request
	jinja_env.globals['static_basepath'] = config.get_settings()['upload_baseurl']
	
	# Assign filters
	jinja_env.filters['resource_url'] = config.maybe_dotted(
		'pyramid_jinja2.filters:model_url_filter'
	)
	jinja_env.filters['route_url'] = config.maybe_dotted(
		'pyramid_jinja2.filters:route_url_filter'
	)
	jinja_env.filters['static_url'] = static_url_filter
	jinja_env.filters['rfc3339'] = rfc3339_format
	jinja_env.filters['maximum'] = max
	
	# Assign tests
	jinja_env.tests['allowed'] = is_allowed
	jinja_env.tests['not_allowed'] = is_not_allowed


#############################################
## Rendering Functions
#############################################
def json_renderer_factory(info):
	def default_encoder(o):
		if hasattr(o,'to_json'):
			return o.to_json()
		elif isinstance(o, datetime.datetime):
			return o.strftime("%Y-%m-%dT%H:%M:%SZ")
		raise TypeError(type(o)) # pragma: no cover
	
	def _render(value, system):
		request = system.get('request')
		if request is not None:
			response = request.response
			ct = response.content_type
			if ct == response.default_content_type:
				response.content_type = 'application/json'
		return json.dumps(value, default=default_encoder)
	
	return _render


#############################################
## Template Globals
#############################################
def app_settings(key, mod='core'):
	import sqlahelper
	from columns.models import Setting
	Session = sqlahelper.get_session()
	module = Session.query(Setting).get(mod)
	setting_dict = getattr(module, 'config', {})
	return setting_dict.get(key)


#############################################
## Custom Filters
#############################################
def static_url_filter(value):
	request = get_current_request()
	prefix = request.registry.settings.get('static_directory','')
	full_value = '/'.join([prefix,value])
	try:
		url = request.static_url(full_value)
	except ValueError: #pragma: no cover
		url = ''
	return url

def rfc3339_format(value):
	if value.tzinfo is None:
		value = pytz.utc.localize(value)
	
	return value.strftime("%Y-%m-%dT%H:%M:%S%z")


#############################################
## Authorization Tests
#############################################
def is_allowed(permission):
	request = get_current_request()
	context = request.context
	return has_permission(permission, context, request)

def is_not_allowed(permission):
	return not is_allowed(permission)

