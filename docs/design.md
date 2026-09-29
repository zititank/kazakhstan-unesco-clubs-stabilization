# Design

**Shipped.** A minimum pass on what was broken: a calendar stylesheet that conflicted with the calendar script was removed, public pages were fixed at phone widths down to 375 pixels, the mobile menu closes when a link is tapped and on Escape, dead links became real URL reversals, cards crop images consistently, and the Sass build is pinned so the CSS can be rebuilt. The pages were not restyled into a new product. The club cabinet was closed to anonymous visitors so it stopped crashing.

**Pattern.** One visual system or none. A half-restyle is the liability: two sets of components, two spacing scales, and every future page has to pick one. Fix what is broken inside the existing system, and fund a redesign as its own project with its own acceptance.

## Why the look stayed

A redesign was out of scope in writing. Restyling a few pages "while in there" would have left the site with a new header on some pages and the old one on others, and the next developer maintaining both. The stabilization kept a single system, however dated, and made it work on phones.

## The cabinet

The club cabinet is a set of screens for logged-in clubs. The stabilization made it safe: anonymous visitors get a redirect to login instead of a 500. It did not make it a product. Someone still has to choose one of three paths: hide it, keep it for staff-provisioned accounts only, or fund it as a real product with its own design and tests. Each choice changes what the privilege model in [privileges.md](privileges.md) has to protect.

## Takeout (Shipped)

From [examples/cabinet_access.py](../examples/cabinet_access.py).

```python
# Status: shipped
# settings.py
# LOGIN_URL = "main:login"


# LoginRequiredMixin must stay leftmost: its dispatch() has to run before any
# mixin that touches request.user as if it were a club.
class CabinetHome(LoginRequiredMixin, CabinetContextMixin, ListView):
    template_name = "cabinet/home.html"

    def get_queryset(self):
        return self.request.user.articles.order_by("-created")


class CabinetProfile(LoginRequiredMixin, CabinetContextMixin, UpdateView):
    template_name = "cabinet/profile.html"
    fields = ("display_name", "profile_text")
```
