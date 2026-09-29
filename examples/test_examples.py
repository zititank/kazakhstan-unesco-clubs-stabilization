"""Checks for the example modules that run without Django.

    python3 examples/test_examples.py

Covers the slug prefix rewrite, the empty-field-only fill policy, the
translation seam, and the recommended admin scoping: a non-superuser's
fieldsets never contain is_superuser.
"""
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin_scope import (  # noqa: E402
    ACCOUNT_FIELDSETS,
    EDITOR_PERMISSIONS,
    PRIVILEGE_FIELDS,
    ScopedAccountAdmin,
    editor_permission_problems,
    strip_privilege_fields,
)
from fill_empty import fill_empty_fields  # noqa: E402
from translated_slug import localized_url_path, sync_empty_translated_slugs  # noqa: E402
from translation_backends import (  # noqa: E402
    LibreTranslateBackend,
    RoutedBackend,
    StubBackend,
    TranslationBackendError,
    build_backend,
    chunk_text,
)


def flatten_fields(fieldsets):
    names = []
    for _, options in fieldsets:
        for entry in options.get("fields", ()):
            names.extend(entry if isinstance(entry, (tuple, list)) else (entry,))
    return names


class SlugPrefixRewriteTests(unittest.TestCase):
    def test_default_language_stays_unprefixed(self):
        self.assertEqual(localized_url_path("/en/news/item/", "ru"), "/news/item/")
        self.assertEqual(localized_url_path("/kk", "ru"), "/")

    def test_prefix_is_replaced_not_stacked(self):
        self.assertEqual(localized_url_path("/en/news/item/", "kk"), "/kk/news/item/")
        self.assertEqual(localized_url_path("/news/item/", "en"), "/en/news/item/")

    def test_root_and_empty_paths(self):
        self.assertEqual(localized_url_path("/", "en"), "/en/")
        self.assertEqual(localized_url_path("", "kk"), "/kk/")
        self.assertEqual(localized_url_path("news/", "en"), "/en/news/")

    def test_lookalike_segment_is_not_a_prefix(self):
        self.assertEqual(localized_url_path("/english-club/", "ru"), "/english-club/")
        self.assertEqual(localized_url_path("/english-club/", "kk"), "/kk/english-club/")

    def test_empty_slug_columns_are_backfilled_only(self):
        article = SimpleNamespace(slug="first", slug_ru="first", slug_en="", slug_kk="birinshi")
        sync_empty_translated_slugs(article)
        self.assertEqual(article.slug_en, "first")
        self.assertEqual(article.slug_kk, "birinshi")


class FillEmptyTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def translate(self, text, source, target):
        self.calls.append(target)
        return f"[{target}] {text}"

    def test_non_empty_target_is_skipped_and_never_translated(self):
        article = SimpleNamespace(title_ru="Новость", title_en="Written by an editor", title_kk="")
        filled, skipped = fill_empty_fields(article, ["title"], self.translate)
        self.assertEqual(article.title_en, "Written by an editor")
        self.assertEqual(article.title_kk, "[kk] Новость")
        self.assertEqual(filled, ["title_kk"])
        self.assertEqual(skipped, ["title_en"])
        self.assertEqual(self.calls, ["kk"])

    def test_whitespace_counts_as_empty(self):
        article = SimpleNamespace(title_ru="Новость", title_en="   ", title_kk=None)
        filled, _ = fill_empty_fields(article, ["title"], self.translate)
        self.assertEqual(filled, ["title_en", "title_kk"])

    def test_empty_source_writes_nothing(self):
        article = SimpleNamespace(title_ru="", title_en="", title_kk="")
        self.assertEqual(fill_empty_fields(article, ["title"], self.translate), ([], []))
        self.assertEqual(self.calls, [])

    def test_stub_backend_writes_nothing(self):
        article = SimpleNamespace(title_ru="Новость", title_en="", title_kk="")
        filled, _ = fill_empty_fields(article, ["title"], StubBackend().translate)
        self.assertEqual(filled, [])
        self.assertEqual((article.title_en, article.title_kk), ("", ""))

    def test_dry_run_reports_without_writing(self):
        article = SimpleNamespace(title_ru="Новость", title_en="", title_kk="")
        filled, _ = fill_empty_fields(article, ["title"], self.translate, dry_run=True)
        self.assertEqual(filled, ["title_en", "title_kk"])
        self.assertEqual(article.title_en, "")
        self.assertEqual(self.calls, [])


class TranslationSeamTests(unittest.TestCase):
    def test_chunks_respect_limit_and_rejoin_losslessly(self):
        text = ("Абзац первый, довольно длинный.\n" * 40) + ("word " * 300)
        chunks = chunk_text(text, 200)
        self.assertTrue(all(len(chunk) <= 200 for chunk in chunks))
        self.assertEqual("".join(chunks), text)

    def test_kazakh_goes_to_its_provider_and_english_to_libre(self):
        sent = []

        def fake_post(payload):
            sent.append((payload["source"], payload["target"]))
            return {"translatedText": "News"}

        class FakeKazakhProvider:
            def translate(self, text, source, target):
                return "Жаңалық"

        libre = LibreTranslateBackend("loopback-test", delay=0, post=fake_post)
        backend = RoutedBackend(libre, {"kk": FakeKazakhProvider()})
        self.assertEqual(backend.translate("Новость", "ru", "en"), "News")
        self.assertEqual(backend.translate("Новость", "ru", "kk"), "Жаңалық")
        self.assertEqual(sent, [("ru", "en")])

    def test_libre_refuses_pairs_it_has_no_model_for(self):
        libre = LibreTranslateBackend("loopback-test", delay=0, post=lambda payload: {})
        with self.assertRaises(TranslationBackendError):
            libre.translate("Новость", "ru", "kk")

    def test_default_backend_is_stub(self):
        self.assertIsInstance(build_backend(), StubBackend)


class NonSuperuserFieldsetTests(unittest.TestCase):
    def test_non_superuser_fieldset_does_not_contain_is_superuser(self):
        scoped = strip_privilege_fields(ACCOUNT_FIELDSETS, is_superuser=False)
        names = flatten_fields(scoped)
        self.assertNotIn("is_superuser", names)
        self.assertFalse(PRIVILEGE_FIELDS & set(names))
        self.assertIn("display_name", names)

    def test_superuser_keeps_the_checkbox(self):
        scoped = strip_privilege_fields(ACCOUNT_FIELDSETS, is_superuser=True)
        self.assertIn("is_superuser", flatten_fields(scoped))

    def test_mixin_applies_to_model_admin_fieldsets(self):
        class FakeModelAdmin:
            def get_fieldsets(self, request, obj=None):
                return ACCOUNT_FIELDSETS

        class AccountAdmin(ScopedAccountAdmin, FakeModelAdmin):
            pass

        staff = SimpleNamespace(user=SimpleNamespace(is_superuser=False, pk=7))
        self.assertNotIn("is_superuser", flatten_fields(AccountAdmin().get_fieldsets(staff)))

    def test_editor_group_cannot_delete_or_administer_accounts(self):
        self.assertEqual(editor_permission_problems(EDITOR_PERMISSIONS), [])
        self.assertEqual(
            editor_permission_problems(("directory.delete_organization", "auth.change_user")),
            ["directory.delete_organization", "auth.change_user"],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
