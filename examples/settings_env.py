"""Django settings that take secrets and debug mode from the environment.

Status: shipped (distilled). The live settings follow this pattern; values,
hostnames, and unrelated settings are left out.

Constraint: the repository has to be safe to hand to another developer, and
the same settings file has to run on a laptop over plain HTTP and in
production behind a TLS terminator.

Failure it prevents: a clone of the repository carrying the signing key and
the mail password, and a production process that starts with DEBUG on
because someone forgot a flag. A missing secret stops startup with a clear
message; there is no weak fallback value.

Refuses to include: real values and hostnames. A matching .env.example
holds placeholders only:

    DJANGO_SECRET_KEY=replace-me
    DJANGO_DEBUG=False
    DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
    DJANGO_ADMIN_URL=admin
    EMAIL_HOST=localhost
    EMAIL_HOST_USER=replace-me
    EMAIL_HOST_PASSWORD=replace-me
    TRANSLATION_BACKEND=stub

This file only reads the environment. It does not decide which person may
do what; that is docs/privileges.md and admin_scope.py.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(path):
    """Read KEY=VALUE lines into os.environ. Variables already set by the service win."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f"Missing required environment variable {name}. "
            "Copy .env.example to .env and set values for local development."
        )
    return value


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


def admin_url_prefix():
    """One URL segment for the admin. Anything that looks like a path falls back to 'admin'."""
    raw = os.environ.get("DJANGO_ADMIN_URL", "admin").strip().strip("/")
    if not raw or "/" in raw or "\\" in raw or ".." in raw:
        return "admin"
    return raw


load_dotenv(BASE_DIR / ".env")

SECRET_KEY = require_env("DJANGO_SECRET_KEY")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

EMAIL_USE_TLS = True
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = require_env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = require_env("EMAIL_HOST_PASSWORD")

ADMIN_URL = admin_url_prefix()  # urls.py: path(f"{settings.ADMIN_URL}/", admin.site.urls)
LOGIN_URL = "main:login"
TRANSLATION_BACKEND = os.environ.get("TRANSLATION_BACKEND", "stub")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# SECURE_SSL_REDIRECT and SECURE_HSTS_SECONDS stay unset: the TLS terminator owns
# the redirect and the HSTS header, so local HTTP keeps working with these settings.
