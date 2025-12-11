import re
import os
import environ
from pathlib import Path
from celery.schedules import crontab
from corsheaders.defaults import default_headers

BASE_DIR = Path(__file__).resolve().parent.parent

# -------------------------
# ENV
# -------------------------

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
)

env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# -------------------------
# DATABASE
# -------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
    }
}

# -------------------------
# CELERY
# -------------------------

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER")

# -------------------------
# APPS
# -------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "simple_history",
    "corsheaders",
    "rest_framework",
    "viewflow",
    "django_json_widget",
    "django_celery_beat",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "main",
    "api",
]

# -------------------------
# MIDDLEWARE
# -------------------------

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
]

if not DEBUG:
    MIDDLEWARE.append("rollbar.contrib.django.middleware.RollbarNotifierMiddleware")

# -------------------------
# URL / WSGI
# -------------------------

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# -------------------------
# TEMPLATES
# -------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# -------------------------
# PASSWORD VALIDATION
# -------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -------------------------
# STATIC / MEDIA
# -------------------------

STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

if not DEBUG:
    STATIC_ROOT = BASE_DIR / "staticfiles"

# -------------------------
# CORS
# -------------------------

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}

CORS_ALLOW_CREDENTIALS = True

if DEBUG:
    CORS_ALLOWED_ORIGINS = [
        "http://front.local.molodcy:5173",
    ]

    CSRF_TRUSTED_ORIGINS = [
        "http://front.local.molodcy:5173",
    ]

    SESSION_COOKIE_DOMAIN = ".local.molodcy"
    CSRF_COOKIE_DOMAIN = ".local.molodcy"

    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SESSION_COOKIE_DOMAIN = ".большие-молодцы.рф"
    SESSION_COOKIE_SECURE = True
    # SESSION_COOKIE_SAMESITE = "None"

    CSRF_COOKIE_DOMAIN = ".большие-молодцы.рф"
    CSRF_COOKIE_SECURE = True
    # CSRF_COOKIE_SAMESITE = "None"

    CORS_ALLOW_HEADERS = list(default_headers) + ["Authorization"]
    CORS_ALLOWED_ORIGINS = [
        "https://большие-молодцы.рф",
        "https://xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://www.большие-молодцы.рф",
        "https://www.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://админ.большие-молодцы.рф",
        "https://xn--80aimpg.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://www.админ.большие-молодцы.рф",
        "https://www.xn--80aimpg.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://печать.большие-молодцы.рф",
        "https://xn--80aj3aox6a.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://www.печать.большие-молодцы.рф",
        "https://www.xn--80aj3aox6a.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
    ]
    CSRF_TRUSTED_ORIGINS = [
        "https://большие-молодцы.рф",
        "https://xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://www.большие-молодцы.рф",
        "https://www.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://админ.большие-молодцы.рф",
        "https://xn--80aimpg.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://www.админ.большие-молодцы.рф",
        "https://www.xn--80aimpg.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://печать.большие-молодцы.рф",
        "https://xn--80aj3aox6a.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
        "https://www.печать.большие-молодцы.рф",
        "https://www.xn--80aj3aox6a.xn----9sbkcordhnfb1hra5ce.xn--p1ai",
    ]

# -------------------------
# LOGGING
# -------------------------

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "verbose",
            "filename": LOG_DIR / "app.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "level": "INFO",
            "delay": True,
        },
    },

    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django": {
            "handlers": ["console", "file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "core": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

if not DEBUG:
    LOGGING["handlers"]["rollbar"] = {
        "class": "rollbar.logger.RollbarHandler",
        "level": "WARNING",
    }
    LOGGING["loggers"]["django"]["handlers"].append("rollbar")
    LOGGING["loggers"]["django.request"]["handlers"].append("rollbar")

    ROLLBAR = {
        "access_token": env("ROLLBAR_TOKEN"),
        "environment": "production",
        "code_version": "1.0",
        "root": BASE_DIR,
        "ignorable_404_urls": [
            re.compile(r'.*\.(json|env|php|asp|aspx|cgi|bak|old|sql|tar|gz)$'),
            re.compile(r'^/index\.php$'),
            re.compile(r'^/xmlrpc\.php$'),
            re.compile(r'^/wp-.*'),
            re.compile(r'^/vendor/.*'),
            re.compile(r'^/sites/.*'),
            re.compile(r'^/cms/.*'),
            re.compile(r'^/client/.*'),
            re.compile(r'^/library/.*'),
            re.compile(r'^/download/.*'),
            re.compile(r'^/sendgrid/.*'),
            re.compile(r'^/docs/.*'),
            re.compile(r'^/old/.*'),
            re.compile(r'^/new/.*'),
            re.compile(r'^/v\d+/.*'),
            re.compile(r'^/tr/.*'),
        ],
    }

# -------------------------
# I18N
# -------------------------

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Yekaterinburg"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
