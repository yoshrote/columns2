import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'pyramid',
    'repoze.tm2>=1.0b1', # default_commit_veto
    'sqlalchemy',
    'zope.sqlalchemy',
    'WebError',
    'colander',
    'formencode',
    'webhelpers',
    'sqlahelper',
    'simplejson',
    'pyramid_beaker',
    'pyramid_jinja2',
    'pyramid_openid',
    'oauth2',
    'pytz',
    ]

tests_require = requires + ['webtest']

setup(name='columns',
      version='0.0',
      description='columns',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web pyramid pylons',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="columns",
      entry_points = """\
      [paste.app_factory]
      main = columns:main
      """,
      paster_plugins=['pyramid'],
      )

