"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 2.2.13.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import sys
try:
	import django_heroku   # HA
except:
	pass  # ignore locally

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '_3x$0i100i2=x!k@=znrw^=@lc(5d*4u9=*-cv!2@o%t&&n^)h'

# SECURITY WARNING: don't run with debug turned on in production!

# decide if running in development or in production based on my user :)
if 'USER' in os.environ and os.environ['USER'] == 'hadi':
    print("Development environment → DEBUG on")
    DEBUG = True
    SECURE_SSL_REDIRECT = False
else:
    DEBUG =  False
    SECURE_SSL_REDIRECT = True


if DEBUG:
	ALLOWED_HOSTS = ["127.0.0.1", "192.168.2.101"]
else:
	ALLOWED_HOSTS = []


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'earth'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if 'django_heroku' in sys.modules:
	MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')  # HA added for heroku


ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'


# HA Static files (CSS, JavaScript, Images)
# set where to store ()& collect) them; served with whitenoise.
#PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
#STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, '../staticfiles/'))
# Extra places for collectstatic to find static files.
#STATICFILES_DIRS = (
#    os.path.join(PROJECT_ROOT, '../static-assets'),
#)

# Heroku Simplified static file serving.
if 'django_heroku' in sys.modules:
	STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# HA Media files
MEDIA_ROOT = '/tmp'  # for now files are uploaded manually!
# MEDIA_URL = ''


# HA cookie-based sessions
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
# SESSION_COOKIE_HTTPONLY: default is True I think


# HA for Heroku.
# loads actual DB settings, etc. no need to remark on local
if 'django_heroku' in sys.modules:
	DEBUG_PROPAGATE_EXCEPTIONS = True
	django_heroku.settings(locals())
	 # ignore locally if module is not installed (hence not imported)


# HA Setup MemCache for Heroku
# ref: https://devcenter.heroku.com/articles/django-memcache#create-a-django-application-for-heroku
def get_cache():
  import os
  try:
    servers = os.environ['MEMCACHIER_SERVERS']
    username = os.environ['MEMCACHIER_USERNAME']
    password = os.environ['MEMCACHIER_PASSWORD']
    return {
      'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        # TIMEOUT is not the connection timeout! It's the default expiration
        # timeout that should be applied to keys! Setting it to `None` disables expiration.
        'TIMEOUT': None,
        'LOCATION': servers,
        'OPTIONS': {
          'binary': True,
          'username': username,
          'password': password,
          'behaviors': {
            # Enable faster IO
            'no_block': True,
            'tcp_nodelay': True,
            # Keep connection alive
            'tcp_keepalive': True,
            # Timeout settings
            'connect_timeout': 2000, # ms
            'send_timeout': 750 * 1000, # us
            'receive_timeout': 750 * 1000, # us
            '_poll_timeout': 2000, # ms
            # Better failover
            'ketama': True,
            'remove_failed': 1,
            'retry_timeout': 2,
            'dead_timeout': 30,
          }
        }
      }
    }
  except:
    return {
	  # for development mode where `memcachier` doesn't exist
      'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
      }
    }

CACHES = get_cache()
