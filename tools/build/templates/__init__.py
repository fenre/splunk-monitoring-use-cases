"""tools.build.templates — page templates for the SSG.

Each public page family has its own module:

* ``_helpers``   — escape, slug, sort_key, mini markdown→HTML, JSON-LD builders
* ``_css``       — shared inline stylesheet for SSG pages
* ``uc``         — per-use-case detail pages
* ``category``   — per-category landing pages
* ``landing``    — site root landing page
* ``regulation`` — per-regulation rollup pages (added by ssg-regulation-equipment todo)

Templates take a ``RenderContext`` (immutable per-build constants) plus
the relevant slice of the ``Catalog`` and return a ``str`` of HTML or a
``dict`` for JSON twins. They never write to disk — that's
``render_pages``' job.
"""

from . import _css, _helpers  # noqa: F401  (exposed for callers)
