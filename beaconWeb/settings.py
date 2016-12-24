import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ['*']

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'beacons',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
 }

RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        'PASSWORD': 'some-password',
    },
    'high': {
        'URL': os.getenv('REDISTOGO_URL', 'redis://localhost:6379'), # If you're on Heroku
        'DB': 0,
    },
    'low': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
    }
}

TEST_ACCOUNT_NUMBER = ''
TEST_ACCOUNT_ACTIVATION = ''

FOURSQUARE_CLIENT_ID = ''
FOURSQUARE_CLIENT_SECRET = ''

FOURSQUARE_CLIENT_ID2 = ""
FOURSQUARE_CLIENT_SECRET2 = ""

YELP_CONSUMER_KEY = ""
YELP_CONSUMER_SECRET = ""
YELP_TOKEN = ""
YELP_TOKEN_SECRET = ""


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

#changed to be more universal... this will always give the absolute
#path for settings.py and everything is relative to it -- Jeff
ABSOLUTE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
# MEDIA_ROOT = os.path.join(ABSOLUTE_PATH, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"

MEDIA_URL = '/static/images/'
STATIC_URL = '/static/'

# AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']

AWS_STORAGE_BUCKET_NAME = 'hotspot-static'

if not DEBUG:
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    S3_URL = 'http://%s.s3-website-us-west-2.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
    STATIC_URL = S3_URL

STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__),'static').replace('\\','/'),
)


# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'beaconWeb.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'beaconWeb.wsgi.application'

TEMPLATE_DIRS = (
    ABSOLUTE_PATH
)

TEMPLATE_CONTEXT_PROCESSORS = (
	'django.contrib.auth.context_processors.auth',
	'django.core.context_processors.debug',
	'django.core.context_processors.i18n',
	'django.core.context_processors.request',
	'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.static'
)

INSTALLED_APPS = (
    'suit',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django_rq',
    'beaconWeb.apps.beacon',
    'beaconWeb.apps.happy_hours',
    'rest_framework',
    'rest_framework.authtoken',
    'south',
    'ios_notifications',
    'beaconWeb.apps.push_notifications',
    'beaconWeb.apps.twilio_sms',
    'gcm',
    'storages',
    'boto',
    'raven.contrib.django.raven_compat',
    'corsheaders',
    'django_extensions',
    'rest_framework_swagger',
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

AUTH_PROFILE_MODULE = "beacon.Profile"

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

SHELL_PLUS_POST_IMPORTS = (
    ('beaconWeb.shell.import_script', '*'),
    'beaconWeb.shell.import_script'
)

USE_TZ = False

CORS_ALLOW_HEADERS = (
        'x-requested-with',
        'content-type',
        'accept',
        'origin',
        'authorization',
        'x-csrftoken',
        'content-length',
        'X-HTTP-Method-Override',
    )

CORS_ORIGIN_ALLOW_ALL = True
TWILIO_ACCOUNT_SID = ""
TWILIO_AUTH_TOKEN = ""
TWILIO_PHONE = '' #default override by production environment

YELP_CONSUMER_KEY = ""
YELP_CONSUMER_SECRET = ""
YELP_TOKEN = ""
YELP_TOKEN_SECRET = ""

EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 587
EMAIL_USE_TLS = True

TWITTER_CONSUMER_KEY = ""
TWITTER_CONSUMER_SECRET = ""
TWITTER_ACCESS_TOKEN = ""
TWITTER_ACCESS_TOKEN_SECRET = ""

FACEBOOK_APP_ID = ""
FACEBOOK_APP_SECRET = ""

OMNIVORE_DEV_KEY = ""

BITLY_ACCESS_TOKEN = ""

URL = "http://localhost:8000"

SEND_TEXTS = False

IOS_NOTIFICATIONS_AUTHENTICATION = 'AuthNone'
APNS_HOSTNAME_DEVELOPMENT = 'gateway.sandbox.push.apple.com'
APNS_HOSTNAME_PRODUCTION = 'gateway.push.apple.com'
APNS_HOSTNAME = APNS_HOSTNAME_PRODUCTION
APNS_SERVICE_ID = 1

GCM_APIKEY = ""
GCM_DEVICE_MODEL = ''

DEFAULT_FILE_STORAGE = 'beaconWeb.static.s3utils.MediaRootS3BotoStorage'

AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
# AWS_STORAGE_BUCKET_NAME = 'hotspot-photos'

MOBILE_VIEW_TOKEN = ""

RQ_THREAD = 'low'

MIXPANEL_TOKEN = ""

VENMO_CLIENT_ID = ""
VENMO_SECRET_ID = ""

SWAGGER_SETTINGS = {
    "exclude_namespaces": [], # List URL namespaces to ignore
    "api_version": '0.1',  # Specify your API's version
    "api_path": "/",  # Specify the path to your API not a root level
    "enabled_methods": [  # Specify which methods to enable in Swagger UI
        'get',
        'post',
        'put',
        'patch',
        'delete'
    ],
    "api_key": '', # An API key
    "is_authenticated": False,  # Set to True to enforce user authentication,
    "is_superuser": False,  # Set to True to enforce admin only access
}

import braintree

ENVIRONMENT = os.environ.get('ENVIRONMENT')

if ENVIRONMENT and ENVIRONMENT == 'Production':
    # Parse database configuration from $DATABASE_URL
    import dj_database_url
    DATABASES['default'] = dj_database_url.config()

    URL = "http://mighty-reef-7102.herokuapp.com"
    #URL = "https://www.GetHotspotApp.com"
    #URL = "https://www.GetBeacons.com"

    RQ_THREAD = 'high'

    # Honor the 'X-Forwarded-Proto' header for request.is_secure()
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    SEND_TEXTS = os.environ.get('SEND_TEXTS')
    APNS_HOSTNAME = APNS_HOSTNAME_PRODUCTION
    APNS_SERVICE_ID = 2
    TWILIO_PHONE = "+16504259974"


if ENVIRONMENT and ENVIRONMENT == 'Staging':
    # Parse database configuration from $DATABASE_URL
    import dj_database_url
    DATABASES['default'] = dj_database_url.config()

    URL = "http://hotspotapp-staging.herokuapp.com"
    # URL = "https://www.GetHotspotApp.com"
    #URL = "https://www.GetBeacons.com"

    RQ_THREAD = 'high'

    SEND_TEXTS = os.environ.get('SEND_TEXTS')
    APNS_HOSTNAME = APNS_HOSTNAME_PRODUCTION
    APNS_SERVICE_ID = 2
    TWILIO_PHONE = '+16069074082'
    # TWILIO_PHONE = "+16504259974"

if ENVIRONMENT and ENVIRONMENT == 'LAN':
    SEND_TEXTS = os.environ.get('SEND_TEXTS')