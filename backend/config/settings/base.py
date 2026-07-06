from pathlib import Path
import os
from datetime import timedelta

import dj_database_url
from dotenv import load_dotenv

from config.env import is_production_env, validate_production_environment

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _csv_env(name: str, default: str) -> list[str]:
    return [v.strip() for v in os.getenv(name, default).split(",") if v.strip()]


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


APP_ENV_NAME = os.getenv("APP_ENV", os.getenv("DJANGO_ENV", "local")).strip().lower()
IS_PRODUCTION = is_production_env(APP_ENV_NAME)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
DEBUG = os.getenv("DEBUG", "0") == "1"
ALLOWED_HOSTS = _csv_env("ALLOWED_HOSTS", "*")
CORS_ALLOWED_ORIGINS = _csv_env(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
CSRF_TRUSTED_ORIGINS = _csv_env(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
CORS_ALLOW_CREDENTIALS = True

validate_production_environment(
    env=APP_ENV_NAME,
    debug=DEBUG,
    secret_key=SECRET_KEY,
    allowed_hosts=ALLOWED_HOSTS,
    csrf_trusted_origins=CSRF_TRUSTED_ORIGINS,
    cors_allowed_origins=CORS_ALLOWED_ORIGINS,
    storage_access_key=os.getenv("VK_S3_ACCESS_KEY_ID") or os.getenv("VK_CLOUD_ACCESS_KEY"),
    storage_secret_key=os.getenv("VK_S3_SECRET_ACCESS_KEY") or os.getenv("VK_CLOUD_SECRET_KEY"),
)

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
    "apps.disputes",
    "apps.finance_documents",
    "apps.legal_compliance",
    "apps.live_sessions",
    "apps.cohorts",
    "apps.gamification",
    "apps.runtime",
    "apps.invoicing",
    "apps.finance_reporting",
    "apps.booking",
    "apps.affiliates",
    "apps.admin_panel",
    "apps.admin_marketplace",
    "apps.commerce",
    "apps.promotions",
    "apps.store",
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

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = _bool_env("SECURE_SSL_REDIRECT", IS_PRODUCTION)
SESSION_COOKIE_SECURE = _bool_env("SESSION_COOKIE_SECURE", IS_PRODUCTION)
CSRF_COOKIE_SECURE = _bool_env("CSRF_COOKIE_SECURE", IS_PRODUCTION)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if IS_PRODUCTION else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _bool_env("SECURE_HSTS_INCLUDE_SUBDOMAINS", IS_PRODUCTION)
SECURE_HSTS_PRELOAD = _bool_env("SECURE_HSTS_PRELOAD", IS_PRODUCTION)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

VK_S3_ENDPOINT_URL = os.getenv("VK_S3_ENDPOINT_URL", "")
VK_S3_ACCESS_KEY_ID = os.getenv("VK_S3_ACCESS_KEY_ID", "")
VK_S3_SECRET_ACCESS_KEY = os.getenv("VK_S3_SECRET_ACCESS_KEY", "")
VK_PRIVATE_BUCKET = os.getenv("VK_PRIVATE_BUCKET", "trainerhub-private")
VK_PUBLIC_BUCKET = os.getenv("VK_PUBLIC_BUCKET", "trainerhub-public")
MEDIA_UPLOAD_TTL_SECONDS = int(os.getenv("MEDIA_UPLOAD_TTL_SECONDS", "900"))
MEDIA_READ_TTL_SECONDS = int(os.getenv("MEDIA_READ_TTL_SECONDS", "300"))
GLOBAL_COMMISSION_RATE = os.getenv("GLOBAL_COMMISSION_RATE", "20.00")
