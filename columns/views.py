# encoding: utf-8
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import exception_response

import sqlahelper
from .models import Upload
from .models import Setting

#############################
## Other Views 
#############################
def admin_no_slash_view(request): # pragma: no cover
    raise exception_response(
        302,
        location=request.route_url('admin')
    )

def app_no_slash_view(request): # pragma: no cover
    raise exception_response(
        302,
        location=request.route_url('app')
    )

def settings_view(request):
    Session = sqlahelper.get_session()
    settings = Session.query(Setting).\
        order_by(Setting.module).\
        all()
    return render_to_response('columns:templates/settings/index.jinja', {'resources': settings})

def settings_edit_view(request):
    module = request.matchdict.get('module')
    Session = sqlahelper.get_session()
    setting = Session.query(Setting).get(module)
    return render_to_response('columns:templates/settings/edit.jinja', {'resource': setting})

def settings_save(request):
    module = request.matchdict.get('module')
    Session = sqlahelper.get_session()
    setting = Session.query(Setting).get(module)
    for k, v in request.POST.items():
        if k == 'save':
            continue
        setting.config[k] = v
    Session.merge(setting)
    Session.commit()
    raise exception_response(
        302,
        location=request.route_url('settings')
    )

def imageupload(request):
    upload_file = request.POST['file']
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
        raise exception_response(500)
    else:
        return {'filelink': '/'.join([request.registry.settings.get('upload_baseurl'), upload.filepath])}

