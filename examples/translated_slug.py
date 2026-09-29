"""Language-aware URLs and slugs for a trilingual site.

Status: shipped (distilled). The live helpers read the language list from
Django settings; this copy takes it as a module constant.

Constraint: Russian is the default language and stays unprefixed. English and
Kazakh live under /en/ and /kk/. Every article has one slug column per
language, and editors fill them unevenly.

Failure it prevents: switching language on an article page used to rebuild
the URL wrongly and resolve the object by the active language's slug only, so
a reader who clicked "EN" on a Russian article got a 404.

Refuses to include: the site's URL patterns and model names. The path rewrite
and the slug backfill are plain Python; the lookup helpers import Django only
when they run, so test_examples.py works without Django installed.
"""
import re

LANGUAGES = ("ru", "en", "kk")
DEFAULT_LANGUAGE = "ru"

_PREFIXED = tuple(code for code in LANGUAGES if code != DEFAULT_LANGUAGE)
_PREFIX_RE = re.compile(r"^/(%s)(?=/|$)" % "|".join(_PREFIXED))


def localized_url_path(path, language_code):
    """Rewrite a path for the language switcher.

    The default language has no prefix; every other language gets /<code>/.
    An existing prefix is stripped first, so switching en -> kk never
    produces /kk/en/...
    """
    if not path:
        path = "/"
    if not path.startswith("/"):
        path = "/" + path

    stripped = _PREFIX_RE.sub("", path) or "/"
    if not stripped.startswith("/"):
        stripped = "/" + stripped

    if language_code == DEFAULT_LANGUAGE:
        return stripped
    if stripped == "/":
        return f"/{language_code}/"
    return f"/{language_code}{stripped}"


def sync_empty_translated_slugs(instance, languages=LANGUAGES, default=DEFAULT_LANGUAGE):
    """Copy the default-language slug into empty per-language slug columns."""
    source = getattr(instance, f"slug_{default}", None) or getattr(instance, "slug", None)
    if not source:
        return
    for code in languages:
        attr = f"slug_{code}"
        if hasattr(instance, attr) and not getattr(instance, attr):
            setattr(instance, attr, source)


def slug_lookup_q(slug, languages=LANGUAGES):
    """Match a URL slug against every language's slug column, not only the active one."""
    from django.db.models import Q

    query = Q(slug=slug)
    for code in languages:
        query |= Q(**{f"slug_{code}": slug})
    return query


class TranslatedSlugLookupMixin:
    """DetailView mixin: resolve the object whichever language the slug came from."""

    def get_object(self, queryset=None):
        from django.shortcuts import get_object_or_404

        slug = self.kwargs.get(self.slug_url_kwarg)
        if slug is None:
            return super().get_object(queryset=queryset)
        queryset = self.model._default_manager.all()
        if hasattr(self.model, "status"):
            queryset = queryset.filter(status=True)
        return get_object_or_404(queryset, slug_lookup_q(slug))
