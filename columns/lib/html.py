# encoding: utf-8
from BeautifulSoup import BeautifulSoup
from lxml import etree
from lxml import html
from lxml.html import clean
import re
import urlparse
import cgi
import urllib2
from pyramid.compat import json

re_nl = re.compile(ur'\n|\t|\r|&nbsp;')
re_script = re.compile(ur'<script.*?(?:/>|.*?</script>)')
re_caption = re.compile(ur'\[caption.*?\].*?\[/caption\]')

def get_embed_data(soup):
    attrs = None
    parsed = False
    #def parse_from_iframe(base):
    #   #parses ``base`` which is an iframe
    #   movie = dict.fromkeys(['movie', 'type', 'width', 'height'])
    #   movie['width'] = base.attrib.get('width', None)
    #   movie['height'] = base.attrib.get('height', None)
    #   movie['movie'] = base.attrib.get('src', None)
    #
    def parse_from_object(base):
        #parses ``base`` which is either object, object/object or object/embed
        embed = base.find("embed")
        movie = dict.fromkeys(['movie', 'type', 'width', 'height'])
        movie_url = dict.fromkeys(['base', 'args'])
        movie['width'] = base.get('width', embed.get('width', None) if embed is not None else None)
        movie['height'] = base.get('height', embed.get('height', None) if embed is not None else None)
        movie['type'] = base.get('type', embed.get('type', None) if embed is not None else None)
        #get param data, look for the flash url and params
        for param in base.findAll("param"):
            name = param['name'].lower()
            value = param['value']
            if name in ['src', 'movie'] and movie_url['base'] is None:
                movie_url['base'] = value
            elif name == 'flashvars' and movie_url['args'] is None:
                movie_url['args'] = value
            elif name in ['movie', 'type']:
                movie[name] = value
        
        #combine the base and args if there are any
        if movie_url['args'] is not None:
            if movie_url['base'].find('?') == -1:
                movie_url['base'] = ''.join([movie_url['base'], '?'])
            elif movie_url['base'][-1] not in ['?', '&']:
                movie_url['base'] = ''.join([movie_url['base'], '&'])
            if movie_url['args'].startswith('&'):
                movie_url['args'] = movie_url['args'][1:]
            movie['movie'] = ''.join([movie_url['base'], movie_url['args']])
        else:
            movie['movie'] = movie_url['base'] if movie['movie'] is None else movie['movie']
        
        return movie
    
    def parse_from_embed(base):
        #parses ``base`` which is an embed
        movie = dict.fromkeys(['movie', 'type', 'width', 'height'])
        movie['width'] = base.get('width', None)
        movie['height'] = base.get('height', None)
        movie['movie'] = base.get('src', None)
        movie['type'] = base.get('type', None)
        return movie
    
    if parsed is False:
        obj = soup.find('object')
        if obj is not None:
            attrs = parse_from_object(obj)
            parsed = True if attrs['movie'] is not None else False
    if parsed is False:
        obj = soup.find('embed')
        if obj is not None:
            attrs = parse_from_embed(obj)
            parsed = True if attrs['movie'] is not None else False
    #if parsed is False:
    #   obj = soup.find('iframe')
    #   if obj is not None:
    #       attrs = parse_from_iframe(obj)
    #       parsed = True if attrs['movie'] is not None else False
    return attrs if parsed is True else None

def stripobjects(content):
    if not isinstance(content, basestring):
        return u''
    parser = etree.XMLParser(recover=True, resolve_entities=False)
    tree = etree.fromstring("""<div>%s</div>"""%content, parser)
    changed = False
    for obj in tree.findall(".//iframe"):
        changed = True
        obj.getparent().remove(obj)
    for obj in tree.findall(".//object"):
        changed = True
        obj.getparent().remove(obj)
    for obj in tree.findall(".//embed"):
        changed = True
        obj.getparent().remove(obj)
    hr = tree.find(".//hr")
    if hr is not None:
        for i, x in enumerate(hr.itersiblings()):
            x.getparent().remove(x)
            changed = True
        hr.getparent().remove(hr)
    res = etree.tostring(tree)[5:-6]
    return res #, changed

def striphtml(content):
    """Returns ``content`` stripped of all HTML tags and of the contents of <style> and <script> tags.
    It will also remove any tabs, newline characters and non-breaking spaces.
    """
    if not isinstance(content, basestring):
        return u''
    content = re_script.sub(u'', content)
    doc = html.fragment_fromstring(content, create_parent=True)
    clean.clean_html(doc)
    return unicode(re_nl.sub(u'', doc.text_content()))

def get_post_thumbnail(video_src, default_img=None):
    if video_src.find('vimeo.com') != -1:
        clip_id = dict(cgi.parse_qsl(urlparse.urlparse(video_src).query)).get('clip_id')
        resp = json.load(urllib2.urlopen(urllib2.Request('http://vimeo.com/api/v2/video/%s.json'%clip_id, headers={'User-Agent':'ColumnsAgent'})))
        return unicode(resp[0]['thumbnail_small'])
    elif video_src.find('youtube.com') != -1:
        parsed_url = urlparse.urlparse(video_src)
        clip_id = dict(cgi.parse_qsl(parsed_url.query)).get('v', parsed_url.path.split('/')[-1].split('&')[0])
        return unicode("http://img.youtube.com/vi/%s/default.jpg" % clip_id)
    else:
        return default_img

def get_metamedia_data(content, default_img=None):
    metamedia = {'meta':{}, 'link':{}}
    if not isinstance(content, basestring):
        return metamedia
    cxml = BeautifulSoup(content)
    embed = get_embed_data(cxml)
    if embed is not None:
        #video content metadata
        metamedia['meta'][u'video_height'] = embed.get('height', None)
        metamedia['meta'][u'video_width'] = embed.get('width', None)
        metamedia['meta'][u'video_type'] = embed.get('type', None)
        metamedia['link'][u'video_src'] = embed.get('movie', None)
        metamedia['link'][u'image_src'] = get_post_thumbnail(embed['movie'], default_img)
        return metamedia
    img = cxml.find('img')
    if img is not None:
        metamedia['link'][u'image_src'] = img.get('src', default_img)
    return metamedia

