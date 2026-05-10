"""Recurring tooling verbs surfaced through the ``splunk_uc`` dispatcher.

The ``tools/`` subpackage hosts long-lived utility verbs that don't
fit any of the four functional buckets (``audits``, ``generators``,
``ingest``, ``feasibility``, ``migrations``). They are recurring --
i.e. invoked across releases as part of normal authoring or release
flow -- which is what distinguishes them from the one-shot
burndown / uplift scripts that intentionally stay under
``scripts/`` until they're deleted at the end of the relevant
content burndown.

Curation rule: a script is migration-eligible into this subpackage
only when (a) it is committed to git, and (b) it is invoked
recurringly -- typically by CI, a Make target, a pre-commit hook,
or the documented release flow. One-shot fixers, ``_underscore``
helpers, and tier-uplift scripts stay under ``scripts/`` because
they will be removed wholesale when their associated phase finishes.
"""
