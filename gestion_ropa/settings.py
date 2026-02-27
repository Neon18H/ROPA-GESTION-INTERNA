from pathlib import Path
import importlib.util
import logging
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '*').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [u.strip() for u in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if u.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'apps.common',
    'apps.accounts',
    'apps.audit',
    'apps.dashboard',
    'apps.inventory',
    'apps.sales',
    'apps.customers',
    'apps.purchases',
    'apps.finance',
    'apps.reports',
    'apps.promotions',
    'apps.returns_app',
    'apps.settings_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.common.middleware.OrganizationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_ropa.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'apps.settings_app.context_processors.store_settings',
    ]},
}]

WSGI_APPLICATION = 'gestion_ropa.wsgi.application'


def get_env(keys, default=None):
    """Return the first non-empty env var found in keys."""
    if isinstance(keys, str):
        keys = [keys]
    for key in keys:
        value = os.getenv(key)
        if value not in (None, ''):
            return value
    return default


def env_bool(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


IS_LOCAL_ENV = DEBUG or get_env('DJANGO_ENV', '').lower() == 'local'
SETTINGS_DB_ENGINE = 'django.db.backends.mysql'
if not importlib.util.find_spec('MySQLdb') and os.getenv('MYSQL_FALLBACK_TO_SQLITE', 'True') == 'True':
    SETTINGS_DB_ENGINE = 'django.db.backends.sqlite3'

mysql_url = get_env(['MYSQL_URL'])

if mysql_url:
    parsed_mysql_settings = dj_database_url.parse(mysql_url, engine=SETTINGS_DB_ENGINE)
    settings_db_name = parsed_mysql_settings.get('NAME') or (str(BASE_DIR / 'settings_db.sqlite3') if SETTINGS_DB_ENGINE.endswith('sqlite3') else '')
    settings_db_user = parsed_mysql_settings.get('USER', '')
    settings_db_password = parsed_mysql_settings.get('PASSWORD', '')
    settings_db_host = parsed_mysql_settings.get('HOST', '127.0.0.1' if IS_LOCAL_ENV else '')
    settings_db_port = str(parsed_mysql_settings.get('PORT', '3306' if IS_LOCAL_ENV else ''))
else:
    settings_db_name = get_env(['MYSQLDATABASE', 'MYSQL_DB'], str(BASE_DIR / 'settings_db.sqlite3') if SETTINGS_DB_ENGINE.endswith('sqlite3') else '')
    settings_db_user = get_env(['MYSQLUSER', 'MYSQL_USER'], 'root' if IS_LOCAL_ENV else '')
    settings_db_password = get_env(['MYSQLPASSWORD', 'MYSQL_PASSWORD'], '')
    settings_db_host = get_env(['MYSQLHOST', 'MYSQL_HOST'], '127.0.0.1' if IS_LOCAL_ENV else '')
    settings_db_port = get_env(['MYSQLPORT', 'MYSQL_PORT'], '3306' if IS_LOCAL_ENV else '')

if not settings_db_host and SETTINGS_DB_ENGINE.endswith('sqlite3'):
    settings_db_host = '127.0.0.1'
if not settings_db_port and SETTINGS_DB_ENGINE.endswith('sqlite3'):
    settings_db_port = '3306'

logging.getLogger(__name__).info(
    'settings_db config resolved: HOST=%s PORT=%s NAME=%s USER=*** PASSWORD=***',
    settings_db_host or '<empty>',
    settings_db_port or '<empty>',
    settings_db_name or '<empty>',
)

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ropa')),
    'settings_db': {
        'ENGINE': SETTINGS_DB_ENGINE,
        'NAME': settings_db_name,
        'USER': settings_db_user,
        'PASSWORD': settings_db_password,
        'HOST': settings_db_host,
        'PORT': settings_db_port,
        'OPTIONS': {} if SETTINGS_DB_ENGINE.endswith('sqlite3') else {'charset': 'utf8mb4'},
    },
}

DATABASE_ROUTERS = ['apps.common.db_router.SettingsRouter']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-co'
TIME_ZONE = get_env(['TIME_ZONE', 'TZ'], 'America/Bogota')
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
WHITENOISE_USE_FINDERS = os.getenv("WHITENOISE_USE_FINDERS", "False") == "True"

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_DEFAULT_ACL = None
MEDIA_PUBLIC_READ = env_bool('MEDIA_PUBLIC_READ', default=False)
AWS_QUERYSTRING_AUTH = not MEDIA_PUBLIC_READ
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

if AWS_S3_ENDPOINT_URL and AWS_STORAGE_BUCKET_NAME:
    MEDIA_URL = f"{AWS_S3_ENDPOINT_URL.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/media/"
else:
    MEDIA_URL = '/media/'
    logging.getLogger(__name__).warning(
        'S3 media storage env vars are incomplete; MEDIA_URL fallback to local /media/. '
        'Set AWS_S3_ENDPOINT_URL and AWS_STORAGE_BUCKET_NAME for production uploads.'
    )

STORAGES = {
    'default': {
        'BACKEND': (
            'apps.common.storage.PublicMediaStorage'
            if MEDIA_PUBLIC_READ
            else 'apps.common.storage.PrivateMediaStorage'
        )
    },
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
