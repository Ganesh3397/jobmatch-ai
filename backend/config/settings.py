"""
Django settings for AI Resume Analyzer & Real-Time Job Recommendation System.
All secrets / environment specific values come from the .env file.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env(key, default=None):
    return os.getenv(key, default)


def env_bool(key, default=False):
    return str(env(key, default)).lower() in ("1", "true", "yes", "on")


SECRET_KEY = env("SECRET_KEY", "change-me-in-production-please")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in env("ALLOWED_HOSTS", "*").split(",")]
# Render gives the public URL in this variable automatically
RENDER_HOST = env("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]
if RENDER_HOST:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_HOST}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    # local apps
    "accounts",
    "resumes",
    "jobs",
    "analytics",
    "ai",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------- Database
# 1) DATABASE_URL (cloud: Neon / Render)  2) DB_* values (local PostgreSQL)  3) sqlite
if env("DATABASE_URL"):
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(env("DATABASE_URL"), conn_max_age=600)}
elif env("DB_ENGINE", "postgres") == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "resume_ai"),
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", "postgres"),
            "HOST": env("DB_HOST", "localhost"),
            "PORT": env("DB_PORT", "5432"),
        }
    }

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 6}},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
# Built React app (npm run build) served by Django in production -> one URL for everything
FRONTEND_BUILD_DIR = BASE_DIR / "frontend_build"
WHITENOISE_ROOT = FRONTEND_BUILD_DIR if FRONTEND_BUILD_DIR.exists() else None
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------- REST / JWT
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=6),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "UPDATE_LAST_LOGIN": True,  # admin can see when each user last logged in
}

CORS_ALLOWED_ORIGINS = [
    o.strip() for o in env("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
]

# ---------------------------------------------------------------- Redis cache
REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")
if env_bool("USE_REDIS", True):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # if Redis is down, the site keeps working (cache is skipped)
                "IGNORE_EXCEPTIONS": True,
            },
            "TIMEOUT": 60 * 60,
        }
    }
    DJANGO_REDIS_IGNORE_EXCEPTIONS = True
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# ---------------------------------------------------------------- Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TIMEZONE = TIME_ZONE
# If true, tasks run immediately in the same process (no worker needed)
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
# true  -> resume analysis runs in a Celery worker (needs Redis + worker)
# false -> resume analysis runs instantly inside the request (easy local setup)
ASYNC_PROCESSING = env_bool("ASYNC_PROCESSING", False)
CELERY_BEAT_SCHEDULE = {
    "refresh-live-jobs-every-6-hours": {
        "task": "jobs.tasks.refresh_live_jobs",
        "schedule": 60 * 60 * 6,
    },
    "send-job-alerts-daily": {
        "task": "jobs.tasks.send_job_alerts",
        "schedule": 60 * 60 * 24,
    },
}

# ---------------------------------------------------------------- Email
# Forgot-password codes and job alerts. The first configured provider is used:
#   1. Brevo HTTP API  (BREVO_API_KEY)  -> works on Render free plan (SMTP is blocked there)
#   2. Gmail SMTP      (EMAIL_HOST_USER + EMAIL_HOST_PASSWORD = 16-letter Gmail App Password) -> laptop
#   3. none            -> emails are printed in the terminal only
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(env("EMAIL_PORT", 587))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", EMAIL_PORT != 465)
EMAIL_USE_SSL = EMAIL_PORT == 465
EMAIL_TIMEOUT = 15
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "").replace(" ", "")  # Gmail shows app passwords with spaces
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD and "console" in EMAIL_BACKEND:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
BREVO_API_KEY = env("BREVO_API_KEY", "").strip()
EMAIL_FROM_ADDRESS = env("EMAIL_FROM_ADDRESS", "") or EMAIL_HOST_USER or "noreply@jobmatch.ai"
EMAIL_FROM_NAME = env("EMAIL_FROM_NAME", "JobMatch AI")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>")
PASSWORD_RESET_CODE_MINUTES = 10
# Public website URL used in emails (auto-detected from the request when empty)
FRONTEND_URL = env("FRONTEND_URL", "")

# ---------------------------------------------------------------- Job APIs
ADZUNA_APP_ID = env("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = env("ADZUNA_APP_KEY", "")
ADZUNA_COUNTRY = env("ADZUNA_COUNTRY", "in")
JSEARCH_API_KEY = env("JSEARCH_API_KEY", "")  # RapidAPI key (optional)
# Free job APIs that need NO key: Remotive, Jobicy, Arbeitnow (remote / worldwide jobs)
FREE_JOB_APIS = env_bool("FREE_JOB_APIS", True)
# Company careers pages, e.g. CAREER_BOARDS=greenhouse:companyslug,lever:otherslug=Other Company
CAREER_BOARDS = [x.strip() for x in env("CAREER_BOARDS", "").split(",") if x.strip()]

# ---------------------------------------------------------------- Generative AI (optional)
# Free key: https://aistudio.google.com/apikey . Without a key the built-in rule engine is used.
GEMINI_API_KEY = env("GEMINI_API_KEY", "")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-3.8-flash")

# ---------------------------------------------------------------- AI / ML
# "auto" = use sentence-transformers if installed, else TF-IDF
MATCHER_BACKEND = env("MATCHER_BACKEND", "auto")
EMBEDDING_MODEL = env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
MAX_UPLOAD_MB = 5

# ---------------------------------------------------------------- Production security
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO" if not DEBUG else "WARNING"},
}
