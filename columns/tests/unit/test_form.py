# encoding: utf-8
import unittest
import re
import colander
from pyramid import testing

class SimpleColanderSchema(colander.MappingSchema):
	name = colander.SchemaNode(
		colander.String(), 
		required=True, 
		validator=colander.Length(1, 100)
	)

class SimpleColanderSequence(colander.SequenceSchema):
	name = colander.SchemaNode(
		colander.String(), 
		required=True, 
		validator=colander.Length(1, 100)
	)

class ColanderSchemaWithSequence(colander.MappingSchema):
	name = SimpleColanderSequence()

class ColanderSchemaWithMapping(colander.MappingSchema):
	name = SimpleColanderSequence()

class SimpleObj(object):
	def __init__(self, name=None):
		self.name = name
	


class TestColanderForm(unittest.TestCase):
	
	def test_is_error(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(not(form.validate()))
		self.assert_(form.is_validated)
		self.assert_('name' in form.errors)
		self.assert_(form.is_error('name'))
	
	def test_all_errors_with_dict(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		form.errors = {"name" : u"Name is missing", }
		form.non_field_errors.append(u"Value is missing")
		self.assert_(form.all_errors() == [
			u"Value is missing",
			u"Name is missing"]
		)
	
	def test_errors_for(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(not(form.validate()))
		self.assert_(form.is_validated)
		self.assert_('name' in form.errors)
		
		self.assert_(form.errors_for('name') == ['Required'])
	
	def test_validate_twice(self):
		
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST = {'name' : 'ok'}
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(form.validate())
		self.assert_(form.is_validated)
		self.assert_(form.data['name'] == 'ok')
		
		request.POST = {'name' : 'ok again'}
		
		self.assert_(form.validate())
		self.assert_(form.is_validated)
		self.assert_(form.data['name'] == 'ok')
	
	def test_is_validated_on_post(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(not(form.validate()))
		self.assert_(form.is_validated)
	
	def test_is_validated_with_specified_params(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		form.validate(params={'name' : 'foo'})
		obj = form.bind(SimpleObj())
		self.assert_(obj.name == 'foo')
	
	def test_bind(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema())
		form.validate()
		obj = form.bind(SimpleObj())
		self.assert_(obj.name == 'test')
	
	def test_bind_ignore_underscores(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		request.POST['_ignoreme'] = 'test'
		
		class SimpleObjWithPrivate(SimpleObj):
			_ignoreme = None
		
		class SimpleSchemaWithPrivate(SimpleColanderSchema):
			_ignoreme = colander.SchemaNode(
				colander.String(), 
				required=True, 
				validator=colander.Length(1, 100)
			)
		
		form = Form(request, SimpleSchemaWithPrivate())
		form.validate()
		obj = form.bind(SimpleObjWithPrivate())
		self.assert_(obj.name == 'test')
		self.assert_(obj._ignoreme is None)
	
	def test_bind_not_validated_yet(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema())
		self.assertRaises(RuntimeError, form.bind, SimpleObj())
 	
	def test_bind_with_errors(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = ''
		
		form = Form(request, SimpleColanderSchema())
		self.assert_(not form.validate())
		self.assertRaises(RuntimeError, form.bind, SimpleObj())
	
	def test_bind_with_exclude(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema())
		form.validate()
		obj = form.bind(SimpleObj(), exclude=["name"])
		self.assert_(obj.name == None)
	
	def test_bind_with_include(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema())
		form.validate()
		obj = form.bind(SimpleObj(), include=['foo'])
		self.assert_(obj.name == None)
	
	def test_initialize_with_obj(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		
		form = Form(
			request, 
			SimpleColanderSchema(), 
			obj=SimpleObj(name='test')
		)
		
		self.assert_(form.data['name'] == 'test')
	
	def test_initialize_with_defaults(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		form = Form(
			request, 
			SimpleColanderSchema(), 
			defaults={'name' : 'test'}
		)
		
		self.assert_(form.data['name'] == 'test')
	
	def test_initialize_with_obj_and_defaults(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), 
					obj=SimpleObj(name='test1'),
					defaults={'name' : 'test2'})
					
		self.assert_(form.data['name'] == 'test1')
	
	def test_initialize_with_include(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		
		form = Form(
			request, 
			SimpleColanderSchema(), 
			include=['foo'],
			obj=SimpleObj(name='test')
		)
		self.assert_('name' not in form.data)
	
	def test_initialize_with_exclude(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		
		form = Form(
			request, 
			SimpleColanderSchema(), 
			exclude=['name'],
			obj=SimpleObj(name='test')
		)
		self.assert_('name' not in form.data)
	
	def test_validate_from_GET(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "GET"
		request.GET['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema(), method="GET")
		
		self.assert_(form.validate())
		self.assert_(form.is_validated)
	
	def test_validate_from_GET_if_on_POST(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.method = "GET"
		request.GET['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(not form.validate())
		self.assert_(not form.is_validated)
	
	
	def test_force_validate(self):
		from ...lib.form import Form
		
		request = testing.DummyRequest()
		request.GET['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(form.validate(force_validate=True))
		self.assert_(form.is_validated)
	

class TestColanderFormRenderer(unittest.TestCase):
	
	def test_begin_form(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(renderer.begin(url="/"),
					 '<form action="/" method="post">')
	
	def test_end_form(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(renderer.end() == "</form>")
	
	def test_csrf(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		self.assert_(re.match(
			r'<input id="_csrf" name="_csrf" type="hidden" value=".*" />',
			renderer.csrf()
		))
	
	def test_csrf_token(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(re.match(
			r'<div style="display:none;"><input id="_csrf" name="_csrf" '
			r'type="hidden" value=".*" /></div>', renderer.csrf_token()
		))
	
	def test_hidden_tag_with_csrf_and_other_names(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), defaults={'name':'foo'})
		renderer = FormRenderer(form)
		
		self.assert_(re.match(
			r'<div style="display:none;"><input id="name" name="name" '
			r'type="hidden" value="foo" /><input id="_csrf" name="_csrf" '
			r'type="hidden" value=".*" /></div>',
			renderer.hidden_tag('name')
		))
	
	def test_hidden_tag_with_just_csrf(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(re.match(
				r'<div style="display:none;"><input id="_csrf" name="_csrf" '
				r'type="hidden" value=".*" /></div>',
				renderer.hidden_tag()
		))
	
	
	def test_text(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), defaults={"name" : "Fred"})
		renderer = FormRenderer(form)
		
		self.assert_(renderer.text("name") == \
				'<input id="name" name="name" type="text" value="Fred" />')
	
	def test_textarea(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), defaults={"name" : "Fred"})
		renderer = FormRenderer(form)
		
		self.assert_(renderer.textarea("name") == \
				'<textarea id="name" name="name">Fred</textarea>')
	
	def test_hidden(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), defaults={"name" : "Fred"})
		renderer = FormRenderer(form)
		
		self.assert_(renderer.hidden("name") == \
				'<input id="name" name="name" type="hidden" value="Fred" />')
	
	def test_select(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), defaults={"name" : "Fred"})
		renderer = FormRenderer(form)
		
		options = [
			("Fred", "Fred"),
			("Barney", "Barney"),
			("Wilma", "Wilma"),
			("Betty", "Betty"),
		]	
		
		self.assert_(renderer.select("name", options) == \
			"""<select id="name" name="name">
<option selected="selected" value="Fred">Fred</option>
<option value="Barney">Barney</option>
<option value="Wilma">Wilma</option>
<option value="Betty">Betty</option>
</select>""")
	
	def test_file(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(renderer.file('file') == \
				   '<input id="file" name="file" type="file" />')
	
	def test_password(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(renderer.password('password') == \
				   '<input id="password" name="password" type="password" />')
	
	
	def test_radio(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), defaults={"name" : 'Fred'})
		renderer = FormRenderer(form)
		
		self.assert_(renderer.radio("name", value="Fred") == \
					 '<input checked="checked" id="name_fred" name="name" '
					 'type="radio" value="Fred" />')
		
		self.assert_(renderer.radio("name", value="Barney") == \
					 '<input id="name_barney" name="name" '
					 'type="radio" value="Barney" />')
	
	def test_submit(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(renderer.submit("submit", "Submit") == \
			'<input id="submit" name="submit" type="submit" value="Submit" />')
	
	def test_checkbox(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema(), defaults={"name" : True})
		renderer = FormRenderer(form)
		
		self.assert_(renderer.checkbox("name") == \
			'<input checked="checked" id="name" name="name" type="checkbox" '
			'value="1" />')
	
	def test_is_error(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(not(form.validate()))
		
		renderer = FormRenderer(form)
		self.assert_(renderer.is_error('name'))
	
	def test_errors_for(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		
		self.assert_(not(form.validate()))
		renderer = FormRenderer(form)
		
		self.assertEquals(renderer.errors_for('name'), ['Required'])
	
	def test_errorlist(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		form.validate()
		
		renderer = FormRenderer(form)
		
		self.assertEquals(renderer.errorlist(),
					 '<ul class="error"><li>Required</li></ul>')
	
	
	def test_errorlist_with_no_errors(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		request.method = "POST"
		request.POST['name'] = 'test'
		
		form = Form(request, SimpleColanderSchema())
		form.validate()
		
		renderer = FormRenderer(form)
		
		self.assert_(renderer.errorlist() == '')
	
	
	def test_errorlist_with_field(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		request.method = "POST"
		
		form = Form(request, SimpleColanderSchema())
		form.validate()
		
		renderer = FormRenderer(form)
		self.assert_(renderer.errorlist('name') == \
					 '<ul class="error"><li>Required</li></ul>')
	
	def test_label(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(renderer.label("name") == \
				   '<label for="name">Name</label>') 
	
	def test_label_using_field_name(self):
		
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, SimpleColanderSchema())
		renderer = FormRenderer(form)
		
		self.assert_(renderer.label("name", "Your name") == \
				   '<label for="name">Your name</label>') 
	

class TestColanderSequenceRenderer(unittest.TestCase):
	def test_min_entries(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		
		request = testing.DummyRequest()
		form = Form(request, ColanderSchemaWithSequence())
		renderer = FormRenderer(form)
		seq_renderer = renderer.get_sequence('name', min_entries=5)
		self.assert_(len(seq_renderer.data) >= 5)
	
	def test___iter__(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		from ...lib.form import CompoundRenderer
		request = testing.DummyRequest()
		form = Form(request, ColanderSchemaWithSequence())
		form.data = {'name':['bob', 'alice']}
		renderer = FormRenderer(form)
		seq_renderer = renderer.get_sequence('name')
		for seq in seq_renderer:
			self.assertEquals(seq.__class__, CompoundRenderer)
			self.assert_(seq.data.get('name') in ['bob', 'alice'])
	

class TestColanderMapperRenderer(unittest.TestCase):
	def test_min_entries(self):
		from ...lib.form import Form
		from ...lib.form import FormRenderer
		from ...lib.form import MappingRenderer
		
		request = testing.DummyRequest()
		form = Form(request, ColanderSchemaWithMapping())
		renderer = FormRenderer(form)
		map_renderer = renderer.get_mapping('name')
		self.assertEquals(map_renderer.__class__, MappingRenderer)
	


