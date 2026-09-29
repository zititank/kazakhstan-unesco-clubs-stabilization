# Security

**Shipped.** The signing key and mail credentials moved from the settings file into the environment, and startup fails loudly when they are missing. `DEBUG` reads from the environment and defaults to off. Branded 404 and 500 pages replaced Django's debug screens. The club cabinet now redirects anonymous visitors to the login page instead of crashing, and the login URL points at a view that exists. The admin path comes from the environment. Three CDN scripts gained Subresource Integrity hashes without a version change. Debug-era test views were removed. Uploads land in dated folders with sanitized names, and the form checks extension and size. `manage.py check --deploy` was run with debug off, and each of its five warnings was assigned to the layer that owns it.

**Pattern.** Decide which layer owns each security control before changing anything. The Django process owns secrets, debug mode, cookies, and who may reach a view. The TLS terminator owns HTTPS, the redirect to it, and HSTS. Run `check --deploy` with debug off and write the owner next to every warning.

## Debug off, real error pages

A site with `DEBUG = True` in production publishes its settings, its file paths, and fragments of its SQL to anyone who triggers an error. The fix is one line, and it only holds if the default is safe: the setting reads `DJANGO_DEBUG` and treats anything other than the exact string `True` as off. A forgotten variable produces a quiet production site, never a verbose one.

With debug off, Django needs `404.html` and `500.html` templates, or visitors see a bare text response. Both templates extend the site's base layout, so an error page still has the menu and the language switcher. Tests render both pages and check that the site menu is present.

## Secrets out of the repository

`SECRET_KEY`, the mail user, and the mail password come from the environment. A small loader reads a local `.env` for development and never overrides a variable the service manager already set. `.env` is ignored by git; `.env.example` carries placeholders only. A missing secret raises `ImproperlyConfigured` at startup with a message that says which variable to set. A weak fallback key would let a misconfigured server start and sign sessions with a value anyone can read in the source.

## The login wall on the cabinet

The club cabinet is a set of screens for a logged-in club. Anonymous requests to those URLs used to reach view code that assumed a club and answered with a 500. Adding `LoginRequiredMixin` fixed half of it. The other half was `LOGIN_URL`: Django's default is `/accounts/login/`, a route the site never had, so the redirect would have landed on a 404. The setting now names the site's own login view, and tests request every cabinet view anonymously and expect a 302 to the login page. [examples/cabinet_access.py](../examples/cabinet_access.py) shows the shape.

## The admin path

The admin prefix is a single URL segment read from the environment, validated so it cannot contain a slash or `..`. When it changes, the default path returns 404. This takes the admin off the list of URLs every scanner tries first, which cuts noise in the logs and slows opportunistic password guessing. The lock is still the password and the flags on the account behind it, which is the subject of [privileges.md](privileges.md).

## Subresource Integrity

Three scripts load from public CDNs. Each tag now carries an `integrity` hash and `crossorigin="anonymous"`, so a tampered file on the CDN fails to execute. The versions stayed the same; the hashes pin what the site already loaded. Upgrading those libraries is a separate change with its own testing.

## Uploads and static files

In production the TLS terminator serves `/static/` from the collected directory and `/media/` from the upload directory, with gzip and a request size limit. Django serves them only when told to. Uploaded images go to `image/YYYY/MM/` with a sanitized file name, and the form rejects unexpected extensions and oversized files.

## `check --deploy`, with owners

Synthetic transcript, run locally with debug off and a placeholder key. Messages are shortened; the owner column is the annotation.

```
$ DJANGO_DEBUG=False DJANGO_SECRET_KEY=replace-me python manage.py check --deploy
System check identified some issues:

WARNINGS:
?: (security.W004) SECURE_HSTS_SECONDS not set        owner: TLS terminator
?: (security.W008) SECURE_SSL_REDIRECT not True       owner: TLS terminator
?: (security.W009) SECRET_KEY too short or weak       owner: Django setting (environment)
?: (security.W012) SESSION_COOKIE_SECURE not True     owner: Django setting
?: (security.W016) CSRF_COOKIE_SECURE not True        owner: Django setting

System check identified 5 issues (0 silenced).
```

- **W004 and W008, TLS terminator.** The redirect to HTTPS and the HSTS header belong next to the certificate. Setting `SECURE_SSL_REDIRECT` in shared Django settings would break every developer's local HTTP server. HSTS is sticky in browsers, so the team that owns the certificate should own that decision.
- **W009, Django setting.** The key comes from the environment. Each environment generates its own value of at least fifty random characters. The local placeholder triggers the warning, which is the point of the placeholder.
- **W012 and W016, Django setting.** Secure-only cookies are correct once every request arrives over HTTPS. They switch on in the production environment together with TLS.

The warning set was identical before and after the dependency upgrade, so the upgrade introduced nothing new.

## Where this stops

Everything above configures the process: what it knows, what it prints, what it serves. None of it decides which person can create another administrator. That is a separate lock with separate failure modes, covered in [privileges.md](privileges.md).

## Takeout (Shipped)

From [examples/settings_env.py](../examples/settings_env.py).

```python
# Status: shipped
def require_env(name):
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(
            f"Missing required environment variable {name}. "
            "Copy .env.example to .env and set values for local development."
        )
    return value


SECRET_KEY = require_env("DJANGO_SECRET_KEY")
DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"
EMAIL_HOST_USER = require_env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = require_env("EMAIL_HOST_PASSWORD")
ADMIN_URL = admin_url_prefix()  # urls.py: path(f"{settings.ADMIN_URL}/", admin.site.urls)
```
