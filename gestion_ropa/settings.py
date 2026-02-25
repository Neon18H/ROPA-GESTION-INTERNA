from pathlib import Path
import importlib.util
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
    ]},
}]

WSGI_APPLICATION = 'gestion_ropa.wsgi.application'
SETTINGS_DB_ENGINE = 'django.db.backends.mysql'
if not importlib.util.find_spec('MySQLdb') and os.getenv('MYSQL_FALLBACK_TO_SQLITE', 'True') == 'True':
    SETTINGS_DB_ENGINE = 'django.db.backends.sqlite3'

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/ropa')),
    'settings_db': {
        'ENGINE': SETTINGS_DB_ENGINE,
        'NAME': os.getenv('MYSQL_DB', str(BASE_DIR / 'settings_db.sqlite3')),
        'USER': os.getenv('MYSQL_USER', 'root'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', ''),
        'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
WHITENOISE_USE_FINDERS = os.getenv("WHITENOISE_USE_FINDERS", "False") == "True"

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
