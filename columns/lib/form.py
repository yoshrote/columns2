# encoding: utf-8
import colander
from formencode import NestedVariables
from webhelpers.html import tags
from webhelpers.html.builder import HTML

def _fixed_bind(data, obj, children, include=None, exclude=None):
	fields = [node.name for node in children]
	for node in children:
		f = node.name
		if include and f not in include:
			continue
				
		if exclude and f in exclude:
			continue
		if getattr(obj, f, colander.null) is not colander.null:
			data[f] = node.serialize(getattr(obj, f))
	return data

class Form(object):
	"""
	`request` : Pyramid request instance
	
	`schema`  : Colander Schema class or instance
	
	`defaults`   : a dict of default values
	
	`obj`		: instance of an object (e.g. SQLAlchemy model)
	
	`method`		: HTTP method
	
	Also note that values of ``obj`` supercede those of ``defaults``. Only
	fields specified in your schema or validators will be taken from the 
	object.
	"""
	
	
	def __init__(self, request, schema=None, defaults=None,
				 obj=None, extra=None, include=None, exclude=None,
				 method="POST", multipart=False):
				
		self.request = request
		self.schema = schema
		self.method = method
		self.multipart = multipart
		
		self.is_validated = False
		
		self.errors = {}
		self.data = {}
		
		self.non_field_errors = []
		
		if defaults:
			self.data.update(defaults)
			
		if obj:
			_fixed_bind(
				self.data, 
				obj, 
				self.schema.children, 
				include=include, 
				exclude=exclude
			)
	
	def is_error(self, field):
		"""
		Checks if individual field has errors.
		"""
		return field in self.errors
	
	def all_errors(self):
		"""
		Returns all errors in a single list.
		"""
		errors = self.non_field_errors[:]
		for node in self.schema:
			errors += self.errors_for(node.name)
		return errors
	
	def errors_for(self, field):
		"""
		Returns any errors for a given field as a list.
		"""
		errors = self.errors.get(field, [])
		if isinstance(errors, basestring):
			errors = [errors]
		return errors
	
	def validate(self, force_validate=False, params=None):
		"""
		Runs validation and returns True/False whether form is 
		valid.
		
		This will check if the form should be validated (i.e. the
		request method matches) and the schema validates.
		
		Validation will only be run once; subsequent calls to 
		validate() will have no effect, i.e. will just return
		the original result.
		
		The `errors` and `data` dicts will be updated accordingly.
		
		`force_validate`  : will run validation regardless of request method.
		
		`params`		  : dict or MultiDict of params. By default 
		will use **request.POST** (if HTTP POST) or **request.params**.
		"""
		
		if self.is_validated:
			return not(self.errors)
			
		if not force_validate:
			if self.method and self.method != self.request.method:
				return False
				
		if params is None:
			if self.method == "POST":
				params = self.request.POST
			else:
				params = self.request.params
			
		params = NestedVariables.to_python(params, None)
		self.data.update(params)
		
		if self.schema:
			try:
				self.data = self.schema.deserialize(params)
			except colander.Invalid, e:
				self.errors = e.asdict()
				
		self.is_validated = True
		
		return not(self.errors)
	
	def bind(self, obj, include=None, exclude=None):
		"""
		Binds validated field values to an object instance, for example a
		SQLAlchemy model instance.
		
		`include` : list of included fields. If field not in this list it 
		will not be bound to this object.
		
		`exclude` : list of excluded fields. If field is in this list it 
		will not be bound to the object.
		
		Returns the `obj` passed in.
		
		Note that any properties starting with underscore "_" are ignored
		regardless of ``include`` and ``exclude``. If you need to set these
		do so manually from the ``data`` property of the form instance.
		
		Calling bind() before running validate() will result in a RuntimeError
		"""
		
		if not self.is_validated:
			raise RuntimeError, \
					"Form has not been validated. Call validate() first"
					
		if self.errors:
			raise RuntimeError, "Cannot bind to object if form has errors"
			
		items = [
			(k, v) for k, v in self.data.items() 
			if not k.startswith("_")
		]
		for k, v in items:
			
			if include and k not in include:
				continue
				
			if exclude and k in exclude:
				continue
				
			setattr(obj, k, v)
			
		return obj
	


class Renderer(object):
	
	def __init__(self, data, errors, id_prefix=None):
		self.data = data
		self.errors = errors
		self.id_prefix = id_prefix
	
	def get_sequence(self, name, min_entries=0):
		
		data = self.value(name, [])
		errors = self.errors.get(name, {})
		
		return SequenceRenderer(name, data, errors, min_entries=min_entries)
	
	def get_mapping(self, name):
		
		data = self.value(name, {})
		errors = self.errors.get(name, {})
		
		return MappingRenderer(name, data, errors)
	
	def text(self, name, value=None, id=None, **attrs):
		"""
		Outputs text input.
		"""
		return tags.text(
			self._get_name(name), 
			self.value(name, value), 
			self._get_id(id, name), 
			**attrs
		)
	
	def file(self, name, value=None, id=None, **attrs):
		"""
		Outputs file input.
		"""
		return tags.file(
			self._get_name(name), 
			self.value(name, value), 
			self._get_id(id, name), 
			**attrs
		)
	
	def hidden(self, name, value=None, id=None, **attrs):
		"""
		Outputs hidden input.
		"""
		if value is None:
			value = self.value(name)
		
		return tags.hidden(
			self._get_name(name), 
			value, 
			self._get_id(id, name), 
			**attrs
		)
	
	def radio(self, name, value=None, checked=False, label=None, **attrs):
		"""
		Outputs radio input.
		"""
		checked = self.value(name) == value or checked
		return tags.radio(self._get_name(name), value, checked, label, **attrs)
	
	def submit(self, name, value=None, id=None, **attrs):
		"""
		Outputs submit button.
		"""
		return tags.submit(
			self._get_name(name), 
			self.value(name, value), 
			self._get_id(id, name), 
			**attrs
		)
	
	def select(self, name, options, selected_value=None, id=None, **attrs):
		"""
		Outputs <select> element.
		"""
		return tags.select(
			self._get_name(name), 
			self.value(name, selected_value), 
			options, 
			self._get_id(id, name), 
			**attrs
		)
	
	def checkbox(self, name, value="1", checked=False, label=None, id=None, **attrs):
		"""
		Outputs checkbox input.
		"""
		
		return tags.checkbox(
			self._get_name(name), 
			value, 
			self.value(name), 
			label, 
			self._get_id(id, name), 
			**attrs
		)
	
	def textarea(self, name, content="", id=None, **attrs):
		"""
		Outputs <textarea> element.
		"""
		
		return tags.textarea(
			self._get_name(name), 
			self.value(name, content), 
			self._get_id(id, name), 
			**attrs
		)
	
	def password(self, name, value=None, id=None, **attrs):
		"""
		Outputs a password input.
		"""
		return tags.password(
			self._get_name(name), self.value(name, value), 
			self._get_id(id, name), 
			**attrs
		)
	
	def is_error(self, name):
		"""
		Shortcut for **self.form.is_error(name)**
		"""
		return name in self.errors
	
	def errors_for(self, name):
		"""
		Shortcut for **self.form.errors_for(name)**
		"""
		return self.form.errors_for(name)
	
	def all_errors(self):
		"""
		Shortcut for **self.form.all_errors()**
		"""
		return self.errors.values()
	
	def errorlist(self, name=None, **attrs):
		"""
		Renders errors in a <ul> element. Unless specified in attrs, class
		will be "error".
		
		If no errors present returns an empty string.
		
		`name` : errors for name. If **None** all errors will be rendered.
		"""
		
		if name is None:
			errors = self.all_errors()
		else:
			errors = self.errors_for(name)
			
		if not errors:
			return ''
			
		content = "\n".join(HTML.tag("li", error) for error in errors)
		
		if 'class_' not in attrs:
			attrs['class_'] = "error"
			
		return HTML.tag("ul", tags.literal(content), **attrs)
	
	def label(self, name, label=None, **attrs):
		"""
		Outputs a <label> element. 
		
		`name`  : field name. Automatically added to "for" attribute.
		
		`label` : if **None**, uses the capitalized field name.
		"""
		if 'for_' not in attrs:
			for_ = name.lower() if not self.id_prefix \
				else self.id_prefix + name.lower()
			attrs['for_'] = for_
			
		label = label or name.capitalize()
		return HTML.tag("label", label, **attrs)
	
	def value(self, name, default=None):
		return self.data.get(name, default)
	
	def _get_id(self, id, name):
		if id is None:
			id = name if not self.id_prefix else (self.id_prefix + name)
		return id
	
	def _get_name(self, name):
		id = name if not self.id_prefix else '.'.join([self.id_prefix, name])
		return id
	

class FormRenderer(Renderer):
	"""
	A simple form helper. Uses WebHelpers to render individual
	form widgets: see the WebHelpers library for more information
	on individual widgets.
	"""
	
	def __init__(self, form, csrf_field='_csrf', id_prefix=None):
		self.form = form
		self.csrf_field = csrf_field
		
		super(FormRenderer, self).__init__(
			self.form.data, 
			self.form.errors, 
			id_prefix,
		)
	
	def begin(self, url=None, **attrs):
		"""
		Creates the opening <form> tags.
		
		By default URL will be current path.
		"""
		url = url or self.form.request.path
		multipart = attrs.pop('multipart', self.form.multipart)
		return tags.form(url, multipart=multipart, **attrs)
	
	def end(self):
		"""
		Closes the form, i.e. outputs </form>.
		"""
		return tags.end_form()
	
	def csrf(self, name=None):
		"""
		Returns the CSRF hidden input. Creates new CSRF token
		if none has been assigned yet.
		
		The name of the hidden field is **_csrf** by default.
		"""
		name = name or self.csrf_field
		
		token = self.form.request.session.get_csrf_token()
		if token is None: # pragma: no cover
			token = self.form.request.session.new_csrf_token()
			
		return self.hidden(name, value=token)
	
	def csrf_token(self, name=None):
		"""
		Convenience function. Returns CSRF hidden tag inside hidden DIV.
		"""
		return HTML.tag("div", self.csrf(name), style="display:none;")
	
	def hidden_tag(self, *names):
		"""
		Convenience for printing all hidden fields in a form inside a 
		hidden DIV. Will also render the CSRF hidden field.
		
		:versionadded: 0.4
		"""
		inputs = [self.hidden(name) for name in names]
		inputs.append(self.csrf())
		return HTML.tag("div", 
						tags.literal("".join(inputs)), 
						style="display:none;")
	

class SequenceRenderer(Renderer):
	def __init__(self, name, data, errors, id_prefix=None, min_entries=0):
		self.name = name
		
		num_entries = min_entries - len(data)
		if num_entries > 0:
			for i in xrange(num_entries):
				data.append({})
				
		super(SequenceRenderer, self).__init__(
			data,
			errors,
			id_prefix,
		)
	
	def __iter__(self):
		
		# what kind of data we dealing with ?
		for i, d in enumerate(self.data):
			
			if not isinstance(d, dict):
				d = {self.name : d}
				
			errors = [] # to be determined
			#id_prefix = "%d-" % i
			id_prefix = "%s-%d" % (self.name, i)
			
			yield CompoundRenderer(self.name, d, errors, id_prefix=id_prefix) 
	

class CompoundRenderer(Renderer):
	"This Renderer is for use in conjuction with SequenceRenderer"
	def __init__(self, name, data, errors, id_prefix=None):
		self.name = name
		super(CompoundRenderer, self).__init__(
			data,
			errors,
			id_prefix,
		)
	

class MappingRenderer(Renderer):
	def __init__(self, name, data, errors, id_prefix=None):
		self.name = name
		id_prefix = id_prefix or name
		super(MappingRenderer, self).__init__(
			data,
			errors,
			id_prefix,
		)
	


