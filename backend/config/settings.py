import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# A frozen build (see packaging/) sets WIKI_ROOT to the folder next to the .exe that holds
# courses/ and the built front end; WIKI_DB points at the SQLite file inside it.
REPO_ROOT = Path(os.getenv("WIKI_ROOT") or BASE_DIR.parent)
load_dotenv(REPO_ROOT / ".env")

# Fail loud rather than shipping a demo key if someone forgets to set one.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "catalog",
    "core",
    "aichat",
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
        "DIRS": [REPO_ROOT / "frontend" / "dist"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.getenv("WIKI_DB") or BASE_DIR / "db.sqlite3",
    }
}

CORS_ALLOWED_ORIGINS = [
    o for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# The cloned repo already carries every lecture PDF; serve them as-is.
MEDIA_URL = "/courses/"
MEDIA_ROOT = REPO_ROOT / "courses"

FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"

# Mirrored EsiHub documents (tools/esihub_fetch.py). Absent in the shared sample build,
# where the assistant simply has no corpus to search.
CORPUS_DIR = Path(os.getenv("WIKI_CORPUS") or REPO_ROOT / "corpus")

# One key per model provider. A key is only ever sent to the host that minted it: sharing one
# variable across providers is how a credential ends up in the wrong Authorization header. Leave any
# of these empty and that provider is simply skipped. The first three are free tiers; OpenAI is the
# odd one out and bills per token, which is why the assistant tries it last.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# What the /contact page publishes. The mailbox is meant to be public; the phone is not, so it
# only exists when the machine running the wiki supplies it — the repo and the shared sample
# therefore carry no personal number. `or` rather than a default argument because dotenv turns
# a blank line in .env into an empty string, which would otherwise blank the address too.
CONTACT_EMAIL = os.getenv("WIKI_CONTACT_EMAIL") or "mohamed-amine.chafik@esi.ac.ma"
CONTACT_PHONE = os.getenv("WIKI_CONTACT_PHONE", "").strip()

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 48,
    "UNAUTHENTICATED_USER": None,
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
