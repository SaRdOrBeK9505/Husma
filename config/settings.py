from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# .env ni aniq yo'l bilan yuklaymiz — WSGI boshqa katalogdan ishga tushsa ham
# (masalan PythonAnywhere'da) fayl topiladi.
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# if DEBUG:
#     CORS_ALLOW_ALL_ORIGINS = True
# else:
#     CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
#
# # Security — production da
# if not DEBUG:
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True
#     X_FRAME_OPTIONS = 'DENY'
#     SECURE_HSTS_SECONDS = 3600
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',

    # Local apps
    'apps.users',
    'apps.hudud',
    'apps.ariza',
    'apps.makler',
    'apps.review',
    'apps.kvartira',
    'apps.settings',
    'apps.obuna',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # eng yuqorida bo'lishi kerak
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DB_ENGINE = os.getenv('DB_ENGINE', 'postgresql')

if DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DATABASE_NAME'),
            'USER': os.getenv('DATABASE_USER'),
            'PASSWORD': os.getenv('DATABASE_PASSWORD'),
            'HOST': os.getenv('DATABASE_HOST', 'localhost'),
            'PORT': os.getenv('DATABASE_PORT', '5432'),
        }
    }

AUTH_USER_MODEL = 'users.CustomUser'

# DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Kvartira Qidiruv API',
    'DESCRIPTION': 'Telegram Mini App uchun REST API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,  # token kiritsa saqlab qoladi
    },
    'SECURITY': [{'BearerAuth': []}],
        'APPEND_COMPONENTS': {
            'securitySchemes': {
                'BearerAuth': {
                    'type': 'http',
                    'scheme': 'bearer',
                    'bearerFormat': 'JWT',
                }
            }
        },
    # Bir nechta modelda 'holat' maydoni borligi sababli enum nomlari to'qnashadi.
    # Har birini aniq nomlash bilan Swagger schema toza chiqadi.
    'ENUM_NAME_OVERRIDES': {
        'ArizaHolatEnum': 'apps.ariza.models.Ariza.Holat',
        'ObunaHolatEnum': 'apps.obuna.models.Obuna.Holat',
        'TolovHolatEnum': 'apps.obuna.models.Tolov.Holat',
        'TolovProvayderEnum': 'apps.obuna.models.Tolov.Provayder',
    },
}

AUTHENTICATION_BACKENDS = [
    'apps.users.backends.TelegramIDBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

# CORS — Telegram Mini App uchun
CORS_ALLOW_ALL_ORIGINS = True  # Productda o'zgartirish kerak

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# ===== PAYME MERCHANT API =====
# Payme Business kabinetdan olinadi (test: https://test.paycom.uz)
PAYME_MERCHANT_ID = os.getenv('PAYME_MERCHANT_ID', '')
# Webhook'ni autentifikatsiya qiluvchi maxfiy kalit (test va prod alohida)
PAYME_KEY = os.getenv('PAYME_KEY', '')
# Test rejimi: True bo'lsa test.paycom.uz, False bo'lsa checkout.paycom.uz
PAYME_TEST_MODE = os.getenv('PAYME_TEST_MODE', 'True') == 'True'
PAYME_CHECKOUT_URL = (
    'https://test.paycom.uz' if PAYME_TEST_MODE else 'https://checkout.paycom.uz'
)

# ===== CLICK (keyinchalik) =====
CLICK_SERVICE_ID = os.getenv('CLICK_SERVICE_ID', '')
CLICK_MERCHANT_ID = os.getenv('CLICK_MERCHANT_ID', '')
CLICK_SECRET_KEY = os.getenv('CLICK_SECRET_KEY', '')
CLICK_MERCHANT_USER_ID = os.getenv('CLICK_MERCHANT_USER_ID', '')

LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===== LOGGING =====
# telegram_auth logger — Telegram auth diagnostikasi.
# Loglar ham konsolga (runserver terminali), ham logs/telegram_auth.log fayliga yoziladi.
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'telegram_auth_file': {
            'class': 'logging.FileHandler',
            'filename': str(LOGS_DIR / 'telegram_auth.log'),
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'telegram_auth': {
            'handlers': ['console', 'telegram_auth_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}