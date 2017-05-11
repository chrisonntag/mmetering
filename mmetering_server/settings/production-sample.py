from .defaults import *
import configparser

config = configparser.RawConfigParser()
config.read(os.path.join(BASE_DIR, 'my.cnf'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.get('variables', 'secretkey')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'domain.example.com',
]

ADMINS = (
    ('<yourName>', '<yourMail>'),
)
MANAGERS = ADMINS

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

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
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
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
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
            'formatter': 'standard',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/mmetering/mmetering.log',
            'formatter': 'standard',
        }
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'backend': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
        },
        'mmetering': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
        }
    }
}
