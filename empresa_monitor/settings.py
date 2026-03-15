"""
Django settings for empresa_monitor project.
"""

import os
import dj_database_url
from pathlib import Path
from datetime import timedelta
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
try:
    SECRET_KEY = config('SECRET_KEY')
except Exception as e:
    print(f"⚠️ decouple falhou: {e}")
    # Fallback para os.environ
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Último recurso para desenvolvimento
        if os.environ.get('DEBUG', 'True') == 'True':
            SECRET_KEY = 'django-insecure-dev-key-temporary'
            print("⚠️ Usando chave temporária para desenvolvimento!")
        else:
            raise ValueError("SECRET_KEY não configurada!")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS configuration
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS if host.strip()]

# Add localhost always
ALLOWED_HOSTS.extend(['localhost', '127.0.0.1', '0.0.0.0'])

# Add Render host if in production
if 'RENDER' in os.environ:
    render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
    if render_host and render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(render_host)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',

    # Local apps
    'apps.accounts',
    'apps.devices',
    'apps.calls',
    'apps.sms_messages',
    'apps.whatsapp',
    'mobile_api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Whitenoise for static files
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'empresa_monitor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': True,
        },
    },
]

WSGI_APPLICATION = 'empresa_monitor.wsgi.application'

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Production with PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
    print(f"✅ Using PostgreSQL database")
else:
    # Development with SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("⚠️ Using SQLite (development mode)")

# Password validation
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
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Create static directory if it doesn't exist
os.makedirs(STATICFILES_DIRS[0], exist_ok=True)

# Whitenoise storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://monitor-whats-53jh.onrender.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF settings
CSRF_COOKIE_DOMAIN = '.onrender.com'  # Nota: começa com ponto
CSRF_TRUSTED_ORIGINS = [
    'https://monitor-whats-53jh.onrender.com',
    'http://monitor-whats-53jh.onrender.com',
    'http://localhost:8000',                     # Desenvolvimento local
    'http://127.0.0.1:8000',                     # Desenvolvimento local
    'http://10.0.2.2:8000',                      # Emulador Android
    'http://localhost',                           # Acessos diretos
]

# CSRF e Cookie settings
CSRF_COOKIE_SECURE = not DEBUG  # True em produção, False em desenvolvimento
CSRF_COOKIE_HTTPONLY = False  # Necessário para JavaScript ler o cookie
CSRF_COOKIE_SAMESITE = 'Lax'  # Ou 'Strict' para mais segurança
CSRF_USE_SESSIONS = False  # Usar cookies em vez de sessões

# Session settings
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'

# CORS settings (se estiver usando CORS)
CORS_ALLOWED_ORIGINS = [
    'https://monitor-whats-53jh.onrender.com',
]
CORS_ALLOW_CREDENTIALS = True

# Se você tiver outros domínios, adicione também
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ])