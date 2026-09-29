# Dependencies

**Shipped.** Django moved from 4.2.2 to 4.2.30, the final release of the 4.2 LTS line. `django-modeltranslation` moved from 0.18.10 to 0.19.17, Pillow from 9.5.0 to 12.3.0, and the support libraries followed. Two packages that no code imported were removed. `requirements.txt` now describes the environment that was actually tested, and a version matrix records every before and after. The move to Django 5.2 was delivered as a written notice with reasons, and it was not attempted.

**Pattern.** Seamless upgrades on a live site mean: pin the LTS line, move to its last patch release, run the tests, write the matrix, and stop at the major boundary. Crossing a major version is a project with its own test environment and acceptance, never a side effect of "updating packages".

## What 4.2.2 to 4.2.30 buys

Between those two releases the 4.2 line had 27 patch releases. Django's security archive lists 22 advisories covering 43 CVEs fixed in that span: SQL injection through query arguments and column aliases, many denial-of-service cases in text and HTML utilities and in upload parsing, directory traversal when saving uploads and extracting archives, and permission errors in the admin. Some apply only to setups this site does not use (Oracle, PostGIS, Windows, ASGI). Many hit exactly what it does use: templates, uploads, the admin, and the ORM.

4.2.30 carries every fix the 4.2 line ever received. The line's extended support ended in April 2026, so from here the exposure grows slowly with each new advisory that 4.2 will not receive. That makes 5.2 the next planned project, and the timing can follow the client's calendar.

## Where the line stops

| Package | Before | After | Boundary |
|---|---|---|---|
| Django | 4.2.2 | 4.2.30 | 5.2 LTS is a major upgrade |
| django-modeltranslation | 0.18.10 | 0.19.17 | 0.19.19 requires Django 5.1 or later |
| Pillow | 9.5.0 | 12.3.0 | moves with image uploads |
| asgiref | 3.7.2 | 3.12.1 | Django support library |
| sqlparse | 0.4.4 | 0.6.0 | Django support library |
| gunicorn | 20.1.0 | 23.0.0 | production only, not in local tests |

`django-modeltranslation` is the tight coupling. Every translated column on the site exists because of it, and its next release refuses Django 4.2. The translation library and the framework therefore move together, on a copy of the live data, in one project.

gunicorn 22 and 23 tightened HTTP parsing and changed how proxy headers are trusted; 22.0 fixed a request smuggling CVE. Because gunicorn runs only on the server, the pin is not covered by local tests, and the deploy guide asks for the upgrade in a maintenance window with a check of the home page and the admin login afterward.

## Python

Django 4.2 is certified for Python 3.8 through 3.12. The development machine ran 3.14, and the Django test client failed there while copying template context. The tests were written with `RequestFactory` instead, and they pass. The fault was in test tooling and never affected pages served to visitors. The recommendation for production is Python 3.12, the newest version Django 4.2 supports. The Python choice for 5.2 belongs to the 5.2 project.

## Making the file honest

The inherited `requirements.txt` pinned older versions than the environment actually had, and listed two packages that appeared in no import, no `INSTALLED_APPS` entry, no template, no settings reference, and no migration. They had come in from an unrelated setup file that was committed by accident. Removing them cannot break a fresh deploy because no migration references them. The file now matches `pip freeze` of the tested environment, with the deploy-only server in its own section.

## Takeout (Shipped)

The shape of the pinned file. No example module here; [examples/README.md](../examples/README.md) lists the Django version each module was written against.

```text
# Status: shipped
# Resolved, installed and verified on 2026-08-29.
# Recommended runtime for the Django 4.2.x line: Python 3.12.

# --- Runtime ---
Django==4.2.30
django-modeltranslation==0.19.17
pillow==12.3.0

# Transitive dependencies, pinned so the environment is reproducible.
asgiref==3.12.1
sqlparse==0.6.0
typing_extensions==4.16.0

# --- Deploy only (not covered by local test runs) ---
gunicorn==23.0.0
```
