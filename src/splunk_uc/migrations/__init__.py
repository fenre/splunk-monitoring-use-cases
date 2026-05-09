"""One-shot data migrations.

Migrations are bulk transformations of the SSOT — typically a single
intentional change to UC sidecar shape, regulation taxonomy, or
schema fields. They run once per repo lifetime, then linger in the
codebase as documentation of the change.

Many ``scripts/migrate_*.py`` files have already executed and are
candidates for archiving rather than migrating. The triage rule:

- If a migration's invariants are now enforced by an audit, archive it.
- If a migration is still a useful tool for catalogue maintenance
  (e.g. renaming a category, bulk-promoting a field), migrate it here.
- If a migration was a fully-completed one-shot with no future use,
  ``git rm`` it in the same PR that documents the operation in
  ``CHANGELOG.md``.

Migration source: ``scripts/migrate_*.py`` (subject to triage).
"""

from __future__ import annotations

__all__: list[str] = []
