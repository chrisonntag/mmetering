from .defaults import *
import configparser

config = configparser.RawConfigParser()
config.read(os.path.join(BASE_DIR, 'my.cnf'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'pcawgi2s$v5k+%r4uzti&bqj%fe1g+o=7^0bwq-hdav-h+)5)6'

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'celery',
    'mmetering.apps.MmeteringConfig',
    'backend.apps.BackendConfig',
    'rest_framework',
]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["0.0.0.0", "localhost", "127.0.0.1"]

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

# TODO: Maybe put database settings in default settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': os.path.join(BASE_DIR, 'my.cnf'),
        },
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
# noinspection PyUnresolvedReferences
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
# STATIC_ROOT = '/static/'
STATIC_URL = '/static/'

# EMAIL SETTINGS
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config.get('mail', 'host')
EMAIL_HOST_USER = config.get('mail', 'user')
EMAIL_HOST_PASSWORD = config.get('mail', 'password')
EMAIL_USE_SSL = config.getboolean('mail', 'ssl')
EMAIL_USE_TLS = config.getboolean('mail', 'tls')
EMAIL_PORT = config.getint('mail', 'port')
DEFAULT_FROM_EMAIL = config.get('mail', 'from')
DEFAULT_TO_EMAIL = list(filter(lambda x: x is not "", config.get('mail', 'to').split("\n")))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(module)s[%(levelname)s]:%(asctime)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/mmetering/mmetering.log',
            'formatter': 'standard',
        }
    },
    'loggers': {
        'backend': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'mmetering': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'mmio': {
            'handlers': ['file'],
            'level': 'DEBUG'
        },
    }
}
