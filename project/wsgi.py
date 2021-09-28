"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from ws4redis.uwsgi_runserver import uWSGIWebsocketServer  # from ws4redis
#from whitenoise.django import DjangoWhiteNoise  # HA: from heroku example, unclear if necessary 

# if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

_django_app = get_wsgi_application()
#_django_app = DjangoWhiteNoise(_django_app)
_websocket_app = uWSGIWebsocketServer()


def application(environ, start_response):
    if environ.get('PATH_INFO').startswith(settings.WEBSOCKET_URL):
        return _websocket_app(environ, start_response)
    return _django_app(environ, start_response)
