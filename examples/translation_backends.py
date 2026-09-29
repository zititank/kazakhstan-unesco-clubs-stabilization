"""Pluggable machine-translation backends for per-language model fields.

Status: shipped (seam). The live module has the same shape: a stub by
default, a self-hosted LibreTranslate backend for Russian and English, and
Kazakh sent to a separate provider behind the same interface.

Constraint: three languages, and no single free engine covers all pairs well.
LibreTranslate's open models handle Russian <-> English; they ship no Kazakh
model. Paid cloud translation costs the client money, so it is enabled only
after written approval.

Failure it prevents: the public process calling a translation service on a
page request, a hard dependency on a paid SDK nobody approved, and a long
article rejected because it exceeded the engine's payload limit.

Refuses to include: any unofficial scraping client for a commercial
translation site, and any instance URL or API key. The caller passes the
LibreTranslate base URL from configuration.
"""
import json
import time
import urllib.error
import urllib.request


class TranslationBackendError(Exception):
    pass


class StubBackend:
    """Default for local, CI, and the public process: returns None, so nothing is written."""

    name = "stub"

    def translate(self, text, source, target):
        return None


def chunk_text(text, max_chars):
    """Split on newlines, then spaces, so no chunk exceeds max_chars and joining restores the text."""
    if len(text) <= max_chars:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            split = text.rfind("\n", start, end)
            if split <= start:
                split = text.rfind(" ", start, end)
            if split > start:
                end = split + 1
        chunks.append(text[start:end])
        start = end
    return chunks


class LibreTranslateBackend:
    """Self-hosted LibreTranslate for ru <-> en, called in chunks."""

    name = "libre"
    pairs = frozenset({("ru", "en"), ("en", "ru")})

    def __init__(self, base_url, api_key="", delay=0.05, chunk_chars=3500, post=None):
        if not base_url:
            raise TranslationBackendError("Set LIBRETRANSLATE_URL to your LibreTranslate instance.")
        self.url = base_url.rstrip("/") + "/translate"
        self.api_key = api_key
        self.delay = delay
        # Payload limits vary by instance; 3500 characters stays under the common defaults.
        self.chunk_chars = chunk_chars
        self.post = post or self._http_post

    def translate(self, text, source, target):
        if not text or not str(text).strip():
            return None
        if (source, target) not in self.pairs:
            raise TranslationBackendError(f"LibreTranslate is not configured for {source}->{target}.")
        parts = []
        for chunk in chunk_text(str(text), self.chunk_chars):
            payload = {"q": chunk, "source": source, "target": target, "format": "text"}
            if self.api_key:
                payload["api_key"] = self.api_key
            translated = self.post(payload).get("translatedText")
            if translated is None:
                return None
            parts.append(translated)
            if self.delay:
                time.sleep(self.delay)
        return "".join(parts)

    def _http_post(self, payload, retries=3):
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt + 1 < retries:
                    time.sleep(2 ** attempt)
                    continue
                raise TranslationBackendError(f"LibreTranslate HTTP {exc.code}") from exc
            except urllib.error.URLError as exc:
                raise TranslationBackendError(f"LibreTranslate unreachable: {exc.reason}") from exc
        return {}


class UnconfiguredProvider:
    """Placeholder for a target language that has no approved provider yet."""

    name = "unconfigured"

    def translate(self, text, source, target):
        raise TranslationBackendError(
            f"No provider configured for {target!r}. Pass one to build_backend()."
        )


class CloudTranslationBackend:
    """Google Cloud Translation v2, the paid official API. Enable only after written cost approval."""

    name = "cloud"

    def translate(self, text, source, target):
        if not text or not str(text).strip():
            return None
        try:
            from google.cloud import translate_v2
        except ImportError as exc:
            raise TranslationBackendError(
                "google-cloud-translate is not installed; install it only after written approval."
            ) from exc
        result = translate_v2.Client().translate(
            text, source_language=source, target_language=target, format_="text"
        )
        return result.get("translatedText")


class RoutedBackend:
    """Send each target language to its own backend; everything else goes to the default."""

    name = "routed"

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
    if name == "cloud":
        return CloudTranslationBackend()
    raise TranslationBackendError(f"Unknown translation backend: {name!r}")
