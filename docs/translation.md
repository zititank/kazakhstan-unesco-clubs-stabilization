# Languages and translation

**Shipped.** The language switcher keeps the reader on the same page. Article and project URLs resolve whichever language the slug came from, so switching language on a detail page no longer returns a 404. List pages stopped hiding rows whose translated title was still empty. A `translate_missing` management command fills empty English and Kazakh fields through a pluggable backend: a stub by default, self-hosted LibreTranslate for Russian and English, and a separate provider for Kazakh behind the same interface. Paid Google Cloud Translation is wired but stays off until the client approves the cost in writing. The interface catalogs received 140 English and 98 Kazakh machine-drafted entries, then were compiled.

**Pattern.** Choose engines per language pair. Keep machine translation out of the public process entirely. Let a batch job write only into empty fields, so it can never overwrite a human. Resolve URLs against every language's slug, never only the active one.

## Routing: three languages, prefix only where needed

Russian is the default language and stays unprefixed; English and Kazakh live under `/en/` and `/kk/`. The switcher used to lose the current path. It now passes the full request path as `next`, and a small function rewrites the prefix: strip any existing `/en` or `/kk`, then add the target's prefix unless the target is Russian. A lookahead in the pattern keeps a path like `/english-club/` from being mistaken for a prefix.

## Slugs in any language

Each article has `slug_ru`, `slug_en`, and `slug_kk`, filled unevenly by editors. The detail views used to look up the object by the active language's slug only. A reader on a Russian article who clicked "EN" arrived at `/en/<russian-slug>/`, and the English slug column did not match. The lookup now ORs every language's slug column. When a translated slug is empty, the command can copy the Russian slug into it, which keeps URLs stable without inventing new ones.

A related fix: list views filtered on `title_<lang>__contains=""`, which in SQL excludes NULL. Articles with no English title yet disappeared from the English list instead of falling back to Russian. The filter was removed, and a test pins it.

## Why hybrid

No single free engine covers all three languages well. LibreTranslate runs locally, costs nothing per call, and has solid open models for Russian and English. It ships no Kazakh model. Kazakh therefore routes to its own provider through the same `translate(text, source, target)` call, and the choice of that provider can change without touching the command. Paid Google Cloud Translation is the high-quality option for every pair; it costs the client money on every run, so it waits for a written yes.

Pair-specific routing also keeps failure local. If the Kazakh provider hits a quota, English still fills, and the Kazakh columns stay empty until the next run. Empty is the safe state: the site falls back to Russian, and an editor can see exactly what is missing.

## Rules the batch follows

- **Stub on the public process.** The server that renders pages runs with the stub backend. It returns nothing, so nothing is written, and no page request ever waits on a translation service.
- **Empty fields only.** A non-empty English or Kazakh field is skipped without calling the engine. A rerun is always safe. The policy is in [examples/fill_empty.py](../examples/fill_empty.py) and tested in [examples/test_examples.py](../examples/test_examples.py).
- **Chunked.** LibreTranslate instances cap payload size. Long articles split on newlines, then spaces, and rejoin losslessly.
- **On a copy, after a backup.** The job holds write locks for about an hour on the full archive. It runs on a copy in a maintenance window, and the copy is swapped in afterward. [database.md](database.md) explains why.

## What stays editorial

About forty Kazakh interface strings were still marked fuzzy at handover: board pages, the chronology, the FAQ. Machine output is a first draft; a Kazakh-speaking editor decides what ships. That is editorial work, and it is best done inside the editor workflow described in [what-next.md](what-next.md).

## Takeout (Shipped)

From [examples/translation_backends.py](../examples/translation_backends.py).

```python
# Status: shipped
class RoutedBackend:
    """Send each target language to its own backend; everything else goes to the default."""

    def __init__(self, default, by_target=None):
        self.default = default
        self.by_target = dict(by_target or {})

    def translate(self, text, source, target):
        return self.by_target.get(target, self.default).translate(text, source, target)


def build_backend(name="stub", *, libre_url="", libre_api_key="", kk_provider=None):
    name = (name or "stub").lower()
    if name == "stub":
        return StubBackend()
    if name == "libre":
        return RoutedBackend(
            LibreTranslateBackend(libre_url, api_key=libre_api_key),
            {"kk": kk_provider or UnconfiguredProvider()},
        )
```
