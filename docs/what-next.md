# What comes next

**Shipped.** The stabilization left a site that runs with debug off, keeps its secrets in the environment, serves three languages without 404s on the switcher, and sits on the final Django 4.2 release. It also left written notes on everything it deliberately did not do: the Django 5.2 upgrade, the Postgres move, a redesign, and a decision on the club cabinet.

**Pattern.** Fund work in the order that makes the next step cheaper and safer. A proven restore makes every later change reversible. A privilege cut shrinks the worst case. Only then do larger projects, each rehearsed on a copy of the data.

## The order

1. **Proven backup and restore.** A snapshot through SQLite's backup API plus the media directory, restored onto an empty folder, followed by `migrate` and a manual check. Everything below assumes this exists.
2. **The privilege cut.** One break-glass superuser created from the server shell. An editor group that can add and change news and projects, with no user administration and no delete on clubs. The superuser checkbox off the everyday admin form. See [privileges.md](privileges.md).
3. **Translation inside the editor.** The batch job fills gaps after the fact. The lasting fix is a "draft translation" action in the admin that applies the same empty-fields-only rule on save, so English and Kazakh stop falling behind Russian. The remaining fuzzy Kazakh interface strings (about forty at handover) are editorial work for a Kazakh-speaking editor, done in the same workflow.
4. **One visual system.** A redesign as its own project, covering every page, with its own acceptance. See [design.md](design.md).
5. **A product decision on the cabinet.** Hide it, keep it for staff-provisioned accounts, or fund it as a product.
6. **HTML filtering for stored articles.** Article bodies are stored as HTML from the editor. An allowlist sanitizer on save keeps a compromised editor account from planting script in the archive.
7. **A map that does not run third-party script on every page.** Load the map only on the page that shows it, or render a static image with a link.
8. **PostgreSQL and Django 5.2, on a copy.** Restore rehearsal first, then the integrity rules from [database.md](database.md) as constraints, then the framework and `django-modeltranslation` together, then Python per 5.2's requirements. Full regression on the copy before the live cutover.

Steps 1 and 2 are small and protect everything after them. Step 8 is the largest and depends on all of the rules the earlier steps put in place.

## Takeout (Recommended)

From [examples/admin_scope.py](../examples/admin_scope.py). Not shipped; this is step 2.

```python
# Status: recommended
EDITOR_GROUP = "Editors"
EDITOR_PERMISSIONS = (
    "content.view_article",
    "content.add_article",
    "content.change_article",
    "content.view_project",
    "content.add_project",
    "content.change_project",
    "directory.view_organization",
)


def editor_permission_problems(codenames):
    """Codenames that would let the daily publishing role delete data or administer accounts."""
    return [
        dotted
        for dotted in codenames
        if dotted.split(".", 1)[1].startswith("delete_") or dotted.startswith("auth.")
    ]
```
