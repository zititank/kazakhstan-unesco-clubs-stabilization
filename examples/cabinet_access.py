"""Club cabinet views behind a login page that exists.

Status: shipped (distilled). Nine cabinet views on the live site received
this treatment; three stand in for them here.

Constraint: the cabinet is the club's own set of screens. Anonymous visitors
still reach those URLs through old links and search engines.

Failure it prevents: an anonymous request used to reach view code that
assumed request.user was a club, and the site answered with a 500. The mixin
alone would only have moved the failure: Django's default LOGIN_URL is
/accounts/login/, a route this site never had, so the redirect would have
landed on a 404. LOGIN_URL has to name the login view that exists.

The shipped tests request every cabinet view anonymously and assert a 302 to
the login page with ?next= set. They use RequestFactory, because the Django
test client failed on the development machine's Python 3.14 (see
docs/dependencies.md).

Refuses to include: the real cabinet screens, their forms, and the dossier
fields they edit. The login wall is authentication only; groups and
permissions were not part of the contract (see admin_scope.py).
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, UpdateView

# settings.py
# LOGIN_URL = "main:login"


class CabinetContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organization"] = self.request.user
        return context


# LoginRequiredMixin must stay leftmost: its dispatch() has to run before any
# mixin that touches request.user as if it were a club.
class CabinetHome(LoginRequiredMixin, CabinetContextMixin, ListView):
    template_name = "cabinet/home.html"

    def get_queryset(self):
        return self.request.user.articles.order_by("-created")


class CabinetProfile(LoginRequiredMixin, CabinetContextMixin, UpdateView):
    template_name = "cabinet/profile.html"
    fields = ("display_name", "profile_text")

    def get_object(self, queryset=None):
        return self.request.user


class CabinetPost(LoginRequiredMixin, CabinetContextMixin, CreateView):
    template_name = "cabinet/post.html"
    fields = ("title", "body")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
