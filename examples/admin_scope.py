"""Admin scoping for a model that is both a login and an organization's file.

Status: recommended (not shipped). The stabilization contract did not change
the admin, build groups, or remove any checkbox. This is the next cut.

Constraint: on the site this case study describes, one row holds the club's
login and the club's dossier. Whoever can edit the dossier in the admin sees
the privilege checkboxes on the same form.

Failure it prevents: a staff account that edits clubs ticking is_superuser on
itself or on another account. With the fields stripped and the queryset
scoped, a stolen editor password costs articles, not the user table.

Refuses to include: the dossier's real field names and the site's app labels.
The permission codenames below use the fictional models from schema_rules.py.

The module imports nothing from Django, so test_examples.py runs it as plain
Python. Mix ScopedAccountAdmin into a django.contrib.admin.ModelAdmin:

    class AccountAdmin(ScopedAccountAdmin, admin.ModelAdmin):
        fieldsets = ACCOUNT_FIELDSETS
"""

PRIVILEGE_FIELDS = frozenset({"is_superuser", "is_staff", "groups", "user_permissions"})


def _without_privileges(fields):
    kept = []
    for entry in fields:
        if isinstance(entry, (tuple, list)):
            row = tuple(name for name in entry if name not in PRIVILEGE_FIELDS)
            if row:
                kept.append(row)
        elif entry not in PRIVILEGE_FIELDS:
            kept.append(entry)
    return tuple(kept)


def strip_privilege_fields(fieldsets, *, is_superuser):
    """Return the fieldsets without privilege fields unless the viewer is a superuser."""
    if is_superuser:
        return tuple(fieldsets)
    scoped = []
    for title, options in fieldsets:
        fields = _without_privileges(options.get("fields", ()))
        if fields:
            scoped.append((title, {**options, "fields": fields}))
    return tuple(scoped)


class ScopedAccountAdmin:
    """ModelAdmin mixin: privilege flags for superusers only, own rows for everyone else."""

    owner_field = None  # None: the model is the account itself. Otherwise e.g. "author".

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        return strip_privilege_fields(fieldsets, is_superuser=request.user.is_superuser)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if self.sees_everything(request):
            return queryset
        if self.owner_field is None:
            return queryset.filter(pk=request.user.pk)
        return queryset.filter(**{self.owner_field: request.user})

    def sees_everything(self, request):
        return request.user.is_superuser


ACCOUNT_FIELDSETS = (
    (None, {"fields": ("username", "password")}),
    ("Organization", {"fields": ("display_name", "profile_text")}),
    ("Access", {"fields": (("is_active", "is_staff"), "is_superuser", "groups")}),
)

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


def ensure_editor_group(Group, Permission):
    """Create the editor group with exactly EDITOR_PERMISSIONS.

    Django creates Permission rows after `migrate`, so call this from a
    management command, not from the first migration of a fresh database.
    """
    group, _ = Group.objects.get_or_create(name=EDITOR_GROUP)
    wanted = []
    for dotted in EDITOR_PERMISSIONS:
        app_label, codename = dotted.split(".", 1)
        wanted.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
    group.permissions.set(wanted)
    return group
