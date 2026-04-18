# version:: 1.0.2
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(override=True)
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY")

# Set True for detailed error messages
DEBUG = True if os.getenv("DEBUG").lower() == "true" else False
# Set to True in a dev. environment
ENV = os.getenv("ENV", "dev")
# NOTE:: Block writes (PUT, POST, PATCH and DELETE) on the database.
# This is very useful during maintenance cause it helps preventing data inconsistancy and
# changes of data during maintenace, in case of rollback.
READ_ONLY = True if os.getenv("READ_ONLY").lower() == "true" else False
assert isinstance(READ_ONLY, bool), "READ_ONLY value can only be True/False"
# This will force to redirect to https, can cause server not reachable True
# SECURE_SSL_REDIRECT = False  if DEBUG else False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").strip().replace(" ", "").split(",")

# 3. Explicitly allow your SvelteKit dev server
# TODO:: Fixe, Does not work with the preview url from coudflare pages.

# TEMPORARY - For development only!
CORS_ALLOWED_ORIGIN_REGEXES = [
    r".*",  # Matches every origin
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Cloudflare Pages URL
    "https://apps-sveltekit-customer.pages.dev",
    # custom domain for staging and production
    "https://app.jigoot.com",

]

# 4. If you're sending Cookies or Authorization headers
CORS_ALLOW_CREDENTIALS = True

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.staticfiles",
    "django.contrib.sessions",
    # thrid party
    "rest_framework_simplejwt.token_blacklist",
    "channels",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_crontab",
    "django_hosts",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "storages",  # from django-storages
    # INFO:: Admin pannel plugin
    "djangoql",
    "import_export",
    # 'mptt',
    # --- custom apps ---
    # "qcluster",
    "common",
    "user",
    "affiche",
    "merchant",
    "customer",
    "courier",
    "branch",
    # "store.apps.StoreConfig",
    "order",
    "parcel",
    "event",
    "wallet",
]


CUSTOMER_API_KEY = os.getenv("CUSTOMER_API_KEY")
BRANCH_API_KEY = os.getenv("BRANCH_API_KEY")
COURIER_API_KEY = os.getenv("COURIER_API_KEY")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

# settings.py
Q_CLUSTER = {
    "queue": "tasks",  # to remove
    "host": os.getenv("AMQP_URL"),
    "backend": {
        "broker": "rabbitmq",
        "url": os.getenv("AMQP_URL"),
        # 'host': '127.0.0.1',
        #     'port': 6379,
        #     'db': 0,
    },
    "workers": 2,
    "retry": 5,  # seconds
    "max_attempts": 5,
}



CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("UPSTASH_REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SSL": True,
        },
    }
}


# INFO: Firebase Cloud Messaging
FCM_DJANGO_SETTINGS = {
    "FCM_SERVER_KEY": "AAAAm1rGoPU:APA91bE3t-o4RF0XBrriMfGdbmyr1_4j2vdIgDwbbYF5A47cEDI1B5eLG5OqCTFXdcvF3VGBGYUo2aKiUDnOijfqvLmuLxBdvykD8_GLMjOdsRSqxm1rG9QgvIeLtd7ZtxTv4cvVTqOo",
    # true if you want to have only one active device per registered user at a time
    # default: False
    "ONE_DEVICE_PER_USER": True,
    # devices to which notifications cannot be sent,
    # are deleted upon receiving error response from FCM
    # default: False
    "DELETE_INACTIVE_DEVICES": True,
}


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # MUST be at the very top
    "django_hosts.middleware.HostsRequestMiddleware",  # django-hosts
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",  # ← Required for CSRF
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",  # ← Must be present
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Other middleware
    "core.middleware.ReadOnlyMiddleware",  # INFO:: read only
    "django_hosts.middleware.HostsResponseMiddleware",  # django-hosts
]


# NOTE:: Django-Hosts config
ROOT_HOSTCONF = "core.hosts"
DEFAULT_HOST = "www"
PARENT_HOST = "jigoot.com" if ENV == "prod" else "jigoot.local:8080"

# In settings.py | For cross-subdomain sessions (if needed)
SESSION_COOKIE_DOMAIN = ".jigoot.com" if ENV == "prod" else ".jigoot.local"
CSRF_COOKIE_DOMAIN = ".jigoot.com" if ENV == "prod" else ".jigoot.local"
if ENV == "prod":
    CSRF_TRUSTED_ORIGINS = [
        "https://jigoot.com",
        "https://www.jigoot.com",
        "https://admin.jigoot.com",
        "https://merchant.jigoot.com",
    ]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# NOTE:: ---- Silk  for debuging ----
# if DEV:
#     INSTALLED_APPS += ['silk', ]
#     MIDDLEWARE += ['silk.middleware.SilkyMiddleware',]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 15,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10/minute",  # 7 requests per minute for anonymous users
        "user": "15/minute",  # 15 requests per minute for authenticated users
        "anon_day": "100/hour",  # 100 requests per day for anonymous users
        "user_day": "200/hour",  # 200 requests per day for authenticated users
        "otp_request": "2/day",  # 3 OTP requests per day
    },
}

ROOT_URLCONF = "core.urls"
AUTH_USER_MODEL = "user.User"  # Custom User model
AUTHENTICATION_BACKENDS = [
    "user.backends.EmailOrPhoneBackend",
    "django.contrib.auth.backends.ModelBackend",  # fallback (optional)
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


LANGUAGES = (("en", "English"), ("fr", "French"))

WSGI_APPLICATION = "core.wsgi.application"
# TODO
ASGI_APPLICATION = "core.asgi.application"  # ***
# TODO use redis as backend for chnnels layer
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}


CRONJOBS = [
    # ('minute hour day_of_month day_of_week', 'command')
    ("0 3 * * *", "core.cron.cleanup_admin_log"),  # Runs daily at 3 AM
]

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND")
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL")  # For error messages

# In seconds
PASSWORD_RESET_TIMEOUT = timedelta(days=1).total_seconds()  # 1 days
# ----------------------------------
# ----------- DATABASE -------------
# ----------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        #  'ENGINE': 'django.contrib.gis.db.backends.postgis', # Use the PostGIS engine
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USERNAME"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST_ENDPOINT"),
        "PORT": os.environ.get("DB_PORT"),
        "OPTIONS": {
            "sslmode": "require",  # NOTE:: Important for Supabase
        },
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# CRISPY  FORM
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# STATIC  AND  MEDIA  FILE

STATIC_URL = "static/"  # Also required
STATIC_ROOT = "staticfiles"
# if ENV == "prod":
AWS_ACCESS_KEY_ID = os.getenv("IAM_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("IAM_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_QUERYSTRING_AUTH = False  # cleaner public URLs
AWS_S3_FILE_OVERWRITE = True
STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"

# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "location": "media",
        },
    },
    # Store collectstatic files on AWS S3
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "location": "static",
        },
    },
}
# else:
#     STATICFILES_DIRS = [
#         BASE_DIR / "static",
#     ]


# LOGGING
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["file"]},
    "handlers": {
        # TODO filter log and save online log that i created on purpose and some reload logs.
        # how can i exclude some file to be save in log file
        "file": {
            "level": "INFO",
            # "class": "logging.FileHandler",
            "class": "logging.handlers.RotatingFileHandler",
            # "/var/log/django.log",
            "filename": os.path.join(BASE_DIR, ".etc/server.log"),
            # INFO: maxBytes is an attribute of the RotatingFileHandler not the FileHandler. You will need to modify your logging config to:
            # 0.2 MB | which is at least 3500 lines for the log file
            "maxBytes": 1024 * 1024 * 0.2,
            # when maxBytes is reached the it will start a new log file and keep the old one as backup. and this will keep rotating
            "backupCount": 3,  # will keep the last two log files as backup
            "encoding": None,
            "formatter": "app",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "brief",
            "level": "INFO",
            # "filters": [allow_foo]
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "django": {"handlers": ["file"], "level": "WARNING", "propagate": False},
    },
    "formatters": {
        "app": {
            "format": ("%(asctime)s [%(levelname)-5s] |%(name)-40s|%(funcName)-3s| %(message)s"),
            "datefmt": "%d-%Y-%m %H:%M:%S",
        },
        "brief": {
            "format": ("[%(levelname)-8s] " "(%(module)s.%(funcName)s) %(message)s"),
            "datefmt": "%d-%Y-%m %H:%M:%S",
        },
    },
}

VERSION = "2026.03.05+3"
