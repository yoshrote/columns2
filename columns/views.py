# encoding: utf-8
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import exception_response
from pyramid.response import Response

import sqlahelper
from columns.models import Upload
from columns.models import Setting

#############################
## Other Views 
#############################
def admin_view(request):
	return render_to_response('columns:templates/admin.jinja', {})

def browse_images_view(request):
	ckedit_num = request.GET.get('CKEditorFuncNum',None)
	return render_to_response(
		'columns:templates/uploads/browse_uploads.jinja',
		{
			'ckedit_num': ckedit_num
		}
	)

def browse_images_ajax(request):
	prefix = request.registry.settings.get('static_directory','')
	offset = int(request.params.get('offset','0'))
	limit = int(request.params.get('limit','20'))
	Session = sqlahelper.get_session()
	uploads = Session.query(Upload).\
		order_by(Upload.updated.desc()).\
		offset(offset).\
		limit(limit).\
		all()
	return [
		{
			'filepath': request.static_url(
				'/'.join([prefix,item.filepath]).replace('//','/')
			),
			'date':item.updated.isoformat(),
			'alt':item.title or ''
		} for item in uploads
	]

def quick_image_upload(request):
	ckedit_num = request.GET.get('CKEditorFuncNum')
	upload_file = request.POST['upload']
	values = {
		'title': upload_file.filename,
		'content': '',
		'tags': set([]),
		'file': upload_file
	}
	upload = Upload()
	try:
		upload = upload.build_from_values(values, request=request)
	except OSError: # pragma: no cover
		return Response(""""<script type='text/javascript'>\
		window.parent.CKEDITOR.tools.callFunction(%(n)s, '%(u)s', '%(m)s')\
		</script>""" % {'n':ckedit_num,'m':message,'u':upload.filepath})
	else:
		return Response(""""<script type='text/javascript'>\
			window.parent.CKEDITOR.tools.callFunction(%(num)s, '%(url)s')\
		</script>""" % {'num':ckedit_num,'url':upload.filepath})


#############################
## Utility Functions
#############################
'''
def settings_module(mod='core'):
	Session = sqlahelper.get_session()
	module = Session.query(Setting).get(mod)
	setting_dict = getattr(module, 'values', {})
	return setting_dict

'''
