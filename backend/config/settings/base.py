from pathlib import Path
import os
from datetime import timedelta

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = [v.strip() for v in os.getenv("ALLOWED_HOSTS", "*").split(",") if v.strip()]

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "apps.core",
    "apps.users",
    "apps.customers",
    "apps.trainers",
    "apps.categories",
    "apps.videos",
    "apps.products",
    "apps.orders",
    "apps.entitlements",
    "apps.subscriptions",
    "apps.purchases",
    "apps.payments",
    "apps.payouts",
    "apps.favorites",
    "apps.challenges",
    "apps.analytics",
    "apps.notifications",
    "apps.moderation",
    "apps.platform_settings",
    "apps.audit",
    "apps.authn",
    "apps.accounts",
    "apps.tenancy",
    "apps.access_control",
    "apps.events",
    "apps.workflows",
    "apps.projections",
    "apps.observability",
    "apps.ops",
    "apps.trainer_cms",
    "apps.media_assets",
    "apps.content",
    "apps.public_catalog",
    "apps.trainer_profiles",
    "apps.reviews",
    "apps.progress",
    "apps.assignments",
    "apps.messaging",
    "apps.billing",
    "apps.onboarding",
    "apps.habits",
    "apps.referrals",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

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

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

CORS_ALLOWED_ORIGINS = [
    v.strip()
    for v in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if v.strip()
]

CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

VK_S3_ENDPOINT_URL = os.getenv("VK_S3_ENDPOINT_URL", "")
VK_S3_ACCESS_KEY_ID = os.getenv("VK_S3_ACCESS_KEY_ID", "")
VK_S3_SECRET_ACCESS_KEY = os.getenv("VK_S3_SECRET_ACCESS_KEY", "")
VK_PRIVATE_BUCKET = os.getenv("VK_PRIVATE_BUCKET", "trainerhub-private")
VK_PUBLIC_BUCKET = os.getenv("VK_PUBLIC_BUCKET", "trainerhub-public")
MEDIA_UPLOAD_TTL_SECONDS = int(os.getenv("MEDIA_UPLOAD_TTL_SECONDS", "900"))
MEDIA_READ_TTL_SECONDS = int(os.getenv("MEDIA_READ_TTL_SECONDS", "300"))
GLOBAL_COMMISSION_RATE = os.getenv("GLOBAL_COMMISSION_RATE", "20.00")
