# Examples

Small annotated modules picked for this case study. None of them is imported from the client project. Each module docstring states the constraint, the failure it prevents, and a `Status:` line.

- **Shipped** means the pattern went live on the site, distilled and renamed here.
- **Recommended** means the contract did not build it. It is the next cut.

The Django-facing modules are written against Django 4.2 LTS and Python 3.12. The pure-Python checks need neither:

```
python3 examples/test_examples.py
```

## settings_env.py

- Teaches: secrets and `DEBUG` from the environment, a local `.env` that never overrides the service's variables, and an admin prefix validated as one URL segment.
- Status: shipped.
- Prevents: a repository clone carrying the keys, and a production process that starts in debug mode.
- Refuses to include: real values, hostnames, or a fallback secret. The `.env.example` in the docstring holds placeholders.
- Read with: [docs/security.md](../docs/security.md).

## cabinet_access.py

- Teaches: `LoginRequiredMixin` leftmost on every cabinet view, and a `LOGIN_URL` that names a view that exists.
- Status: shipped.
- Prevents: a 500 for anonymous visitors, and a redirect to Django's default `/accounts/login/` that the site never routed.
- Refuses to include: the real cabinet screens and the dossier fields they edit. Authentication only; no groups.
- Read with: [docs/security.md](../docs/security.md), [docs/design.md](../docs/design.md).

## admin_scope.py

- Teaches: stripping `is_superuser` and the other privilege fields from the admin form for non-superusers, scoping querysets to owned rows, and an editor group with no delete and no account administration.
- Status: recommended. The contract did not change the admin or build groups.
- Prevents: a staff account promoting itself or another account to superuser.
- Refuses to include: the site's app labels and dossier columns. Codenames use the fictional models from `schema_rules.py`. Imports nothing from Django.
- Read with: [docs/privileges.md](../docs/privileges.md), [docs/what-next.md](../docs/what-next.md).

## schema_rules.py

- Teaches: identity split from the organization's file, `PROTECT` on taxonomy and on the organization-to-article link, `SET_NULL` on author, a unique slug, and an index for the public list.
- Status: recommended. Fictional.
- Prevents: an account deletion wiping an archive, orphaned categories, and two articles on one URL.
- Refuses to include: the live schema. These models mirror nothing on the site.
- Read with: [docs/database.md](../docs/database.md).

## translated_slug.py

- Teaches: the language-prefix rewrite for the switcher, backfilling empty slug columns, and resolving a slug against every language's column.
- Status: shipped.
- Prevents: 404s when a reader switches language on an article page.
- Refuses to include: the site's URL patterns and models. Django is imported only inside the lookup helpers.
- Read with: [docs/translation.md](../docs/translation.md).

## translation_backends.py

- Teaches: a stub default, chunked LibreTranslate for Russian and English, Kazakh routed to a swappable provider, and the paid cloud API loaded only on demand.
- Status: shipped (the seam).
- Prevents: translation calls on page requests, a hard dependency on an unapproved paid SDK, and oversized payloads.
- Refuses to include: any unofficial scraping client, instance URLs, or keys.
- Read with: [docs/translation.md](../docs/translation.md).

## fill_empty.py

- Teaches: write machine translation only into empty fields; `None` from a backend writes nothing.
- Status: shipped (the policy).
- Prevents: a rerun overwriting a human translation, and placeholder copy reaching live columns.
- Refuses to include: the site's model and field list.
- Read with: [docs/translation.md](../docs/translation.md), [docs/database.md](../docs/database.md).

## test_examples.py

- Teaches: the claims above, as checks a reader can run: slug prefix rewrite, empty-field skip, the translation routing, and a non-superuser fieldset without `is_superuser`.
- Status: written for this case study.
- Needs: Python 3 only. No Django, no network.
- Refuses to include: anything that talks to a database or a translation service.
- Run: `python3 examples/test_examples.py`.
