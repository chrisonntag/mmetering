from .defaults import *


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'pcawgi2s$v5k+%r4uzti&bqj%fe1g+o=7^0bwq-hdav-h+)5)6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

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
STATICFILES_DIRS = (
  os.path.join(BASE_DIR, "static"),
)
# STATIC_ROOT = '/static/'
STATIC_URL = '/static/'


#EMAIL SETTINGS
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
DEFAULT_FROM_EMAIL = 'info@chrisonntag.com'