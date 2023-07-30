"""
Django settings for AdsDroid project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import sys
from distutils.util import strtobool
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", " ")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(strtobool(os.environ.get("DEBUG", "False")))

ALLOWED_HOSTS: list = os.environ.get("ALLOWED_HOSTS", ".localhost 127.0.0.1 [::1]").split(" ")
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(" ")

if DEBUG:
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

# LOGGING CONFIG
DEFAULT_LOG_FILE = "default.log"
DATA_EXCHANGE_LOG_FILE = "data_exchange.log"
ERRORS_LOG_FILE = "errors.log"
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_TO_CONSOLE = True  # or True, as per requirement, True will result in verbose logging to the console

if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

for log_file in [DEFAULT_LOG_FILE, DATA_EXCHANGE_LOG_FILE, ERRORS_LOG_FILE]:
    filepath = os.path.join(LOG_DIR, log_file)
    mode = "a" if os.path.exists(filepath) else "w"
    with open(filepath, mode) as f:
        pass


handlers = {
    "file": {
        "formatter": "verbose",
        "class": "logging.FileHandler",
        "filename": os.path.join(LOG_DIR, DEFAULT_LOG_FILE),
        "level": "INFO",
    },
    "file_data_exchange": {
        "formatter": "verbose",
        "class": "logging.FileHandler",
        "level": "INFO",
        "filename": os.path.join(LOG_DIR, DATA_EXCHANGE_LOG_FILE),
    },
    "file_errors": {
        "formatter": "verbose",
        "class": "logging.FileHandler",
        "level": "ERROR",
        "filename": os.path.join(LOG_DIR, ERRORS_LOG_FILE),
    },
}

loggers = {
    "": {
        "handlers": ["file_errors"],
        "level": "ERROR",
        "propagate": True,
    },
    "apps": {
        "handlers": ["file"],
        "level": "INFO",
        "propagate": True,
    },
    "apps.ads_api.data_exchange": {
        "handlers": ["file_data_exchange"],
        "level": "INFO",
        "propagate": True,
    },
    "celery.task": {
        "handlers": ["file_data_exchange"],
        "level": "INFO",
        "propagate": True,
    },
    "django.db.backends": {
        "level": "DEBUG",
        "handlers": [],
    },
}

if LOG_TO_CONSOLE:
    handlers["console"] = {
        "level": "DEBUG",
        "filters": ["require_debug_true"],
        "class": "logging.StreamHandler",
    }

    loggers["apps.ads_api.data_exchange"]["handlers"].append("console")
    loggers["celery.task"]["handlers"].append("console")
    loggers["django.db.backends"]["handlers"].append("console")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} | {asctime} | {filename}:{lineno} - {funcName} {message}",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        }
    },
    "handlers": handlers,
    "loggers": loggers,
}

# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.forms",
]

# Put your third-party apps here
THIRD_PARTY_APPS = [
    "allauth",  # allauth account/registration management
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "rest_framework",
    "rest_framework_api_key",
    "celery_progress",
    "hijack",  # "login as" functionality
    "hijack.contrib.admin",  # hijack buttons in the admin
    "django_extensions",
    "debug_toolbar",
]

PEGASUS_APPS = [
    "pegasus.apps.examples.apps.PegasusExamplesConfig",
    "pegasus.apps.employees.apps.PegasusEmployeesConfig",
]

# Put your project-specific apps here
PROJECT_APPS = [
    "apps.users.apps.UserConfig",
    "apps.ads_api.apps.AdsApiConfig",
    "apps.sp_api.apps.AdsApiConfig",
    "apps.openai_api.apps.OpenaiApiConfig",
    "apps.api.apps.APIConfig",
    "apps.web",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PEGASUS_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "adsdroid.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.web.context_processors.project_meta",
                # this line can be removed if not using Google Analytics
                "apps.web.context_processors.google_analytics_id",
            ],
        },
    },
]

WSGI_APPLICATION = "adsdroid.wsgi.application"

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("POSTGRES_DB", "adsdroid"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("DJANGO_DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DJANGO_DATABASE_PORT", "5432"),
    }
}

if "test" in sys.argv:
    DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": "test_database"}


# Auth / login stuff

# Django recommends overriding the user model even if you don't think you need to because it makes
# future changes much easier.
AUTH_USER_MODEL = "users.CustomUser"
LOGIN_REDIRECT_URL = "/"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Allauth setup

ACCOUNT_ADAPTER = "apps.users.adapter.EmailAsUsernameAdapter"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True


# User signup configuration: change to "mandatory" to require users to confirm email before signing in.
# or "optional" to send confirmation emails but not require them
ACCOUNT_EMAIL_VERIFICATION = "none"


AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)


# enable social login
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
}


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)

# uncomment to use manifest storage to bust cache when file change
# note: this may break some image references in sass files which is why it is not enabled by default
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

MEDIA_ROOT = BASE_DIR / "mediafiles"
MEDIA_URL = "/media/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

# future versions of Django will use BigAutoField as the default, but it can result in unwanted library
# migration files being generated, so we stick with AutoField for now.
# change this to BigAutoField if you're sure you want to use it and aren't worried about migrations.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Email setup

# use in development
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
# use in production
# see https://github.com/anymail/django-anymail for more details/examples
# EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'

# Django sites

SITE_ID = 1

# DRF config
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("apps.api.permissions.IsAuthenticatedOrHasUserAPIKey",),
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

# Redis setup
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Celery setup (using redis)
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_TASK_ALWAYS_EAGER = bool(strtobool(os.environ.get("CELERY_TASK_ALWAYS_EAGER", "False")))

# Pegasus config

# replace any values below with specifics for your project
PROJECT_METADATA = {
    "NAME": "AdsDroid",
    "URL": "http://localhost:8000",
    "DESCRIPTION": "Amazon Advertising Management for Publishers and Authors",
    "IMAGE": "https://upload.wikimedia.org/wikipedia/commons/2/20/PEO-pegasus_black.svg",
    "KEYWORDS": "SaaS, django",
    "CONTACT_EMAIL": "ivan@adsdroid.com",
}

# set this to True in production to have URLs generated with https instead of http
USE_HTTPS_IN_ABSOLUTE_URLS = os.environ.get("USE_HTTPS_IN_ABSOLUTE_URLS", False)

ADMINS = [("Ivan", "ivan@adsdroid.com")]

# Add your Google Analytics ID to the environment or default value to connect to Google Analytics
GOOGLE_ANALYTICS_ID = os.environ.get("GOOGLE_ANALYTICS_ID", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Django security checklist settings. Change to True in production.
# More details here: https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/
SECURE_SSL_REDIRECT = bool(strtobool(os.environ.get("SECURE_SSL_REDIRECT", "False")))
SESSION_COOKIE_SECURE = bool(strtobool(os.environ.get("SESSION_COOKIE_SECURE", "False")))
CSRF_COOKIE_SECURE = bool(strtobool(os.environ.get("CSRF_COOKIE_SECURE", "False")))

# fix ssl mixed content issues (in production).
SECURE_PROXY_SSL_HEADER = os.environ.get("SECURE_PROXY_SSL_HEADER", ())

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Books beam
BOOKS_BEAM_EMAIL = os.environ.get("BOOKS_BEAM_EMAIL")
BOOKS_BEAM_PASSWORD = os.environ.get("BOOKS_BEAM_PASSWORD")
BOOKS_BEAM_ACCESS_TOKEN_EXP_TIME = int(os.environ.get("BOOKS_BEAM_ACCESS_TOKEN_EXP_TIME", 79200))

# AMAZON ADS
ADS_API_CLIENT_ID = os.environ.get("ADS_API_CLIENT_ID")
ADS_API_CLIENT_SECRET = os.environ.get("ADS_API_CLIENT_SECRET")

# OPENAI API

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
