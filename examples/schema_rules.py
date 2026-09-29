"""A fictional schema that shows the integrity rules from docs/database.md.

Status: recommended (not shipped). Fictional: these models do not mirror the
live schema, and the live site was not migrated to them.

Constraint: the site holds years of articles from many organizations. Logins
come and go; the archive must stay. Taxonomy rows are shared by hundreds of
articles.

Failure it prevents:
  - deleting an account and losing that organization's articles (CASCADE);
  - deleting a category while articles still point at it;
  - two articles answering on the same URL because the slug was only indexed;
  - one admin form that edits both a password-bearing login and an
    organization's public profile.

Refuses to include: any column from the real club dossier. Organization
carries two placeholder fields.

On an existing project, swapping AUTH_USER_MODEL is its own migration
project. The practical first step is moving the dossier columns into an
Organization table and leaving the user model alone.
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Account(AbstractUser):
    """Identity only: credentials, privilege flags, last login."""


class Organization(models.Model):
    """The organization's file. Survives its login being disabled or deleted."""

    account = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organization",
    )
    display_name = models.CharField(max_length=200)
    profile_text = models.TextField(blank=True)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Article(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name="articles")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="articles")
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300)
    body = models.TextField()
    status = models.BooleanField(default=False)
    published = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # modeltranslation adds slug_ru, slug_en, slug_kk; each needs its own constraint.
            models.UniqueConstraint(fields=["slug"], name="article_slug_unique"),
        ]
        indexes = [
            models.Index(fields=["status", "-published"], name="article_public_list"),
        ]
