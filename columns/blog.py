# encoding: utf-8
from pyramid.renderers import render_to_response
from pyramid.httpexceptions import exception_response

import sqlahelper
from sqlalchemy.exc import SQLAlchemyError
from .models import Article
from .models import Page
from .models import Tag
from .models import User

#############################
## Blog Views 
#############################
def page_view(request):
    Session = sqlahelper.get_session()
    try:
        page = Session.query(Page).\
            filter(Page.slug == request.matchdict.get('page')).\
            filter(Page.visible == True).\
            one()
    except SQLAlchemyError:
        Session.rollback()
        raise exception_response(404)
    else:
        return render_to_response(
            'columns:templates/blog/page.jinja', 
            {'page': page}
        )

def story_view(request):
    Session = sqlahelper.get_session()
    try:
        story = Session.query(Article).\
            filter(
                Article.permalink==request.matchdict.get('permalink')
            ).\
            filter(Article.published != None).\
            one()
    except SQLAlchemyError:
        Session.rollback()
        raise exception_response(404)
    else:
        return render_to_response(
            'columns:templates/blog/story.jinja', 
            {'story': story}
        )

def stream_view(request):
    tag = request.GET.get('tag')
    user = request.GET.get('user')
    page_number = request.GET.get('page')
    stories_per_page = 10
    try:
        page_number = max([int(page_number), 0])
    except (TypeError, ValueError):
        page_number = 0
    
    Session = sqlahelper.get_session()
    Session.rollback()
    query = Session.query(Article)
    if tag:
        query = query.filter(Article.tags.any(Tag.slug == tag))
    if user:
        query = query.filter(Article.author.has(User.name == user))
    
    stream = query.\
        filter(Article.published != None).\
        order_by(Article.published.desc()).\
        limit(stories_per_page).\
        offset(page_number * stories_per_page).\
        all()
    
    return render_to_response(
        'columns:templates/blog/stream.jinja', 
        {'stream': stream, 'request': request, 'page': page_number}
    )


#############################
## Blog Configuration
#############################
def includeme(config):
    config.add_route('blog_main', '/')
    config.add_view(
        'columns.blog.stream_view',
        route_name='blog_main',
    )
    
    config.add_route('blog_page', '/page/:page')
    config.add_view(
        'columns.blog.page_view',
        route_name='blog_page',
    )
    
    config.add_route('blog_story', '/story/:permalink')
    config.add_view(
        'columns.blog.story_view',
        route_name='blog_story',
    )

