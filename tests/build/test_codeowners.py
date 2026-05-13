"""Structural invariants for ``.github/CODEOWNERS``.

Repo-overhaul plan §P14 (2026-05-13): per-category content
stewardship requires that every category directory under
``content/cat-NN-<slug>/`` has an explicit CODEOWNERS row. The
plan envisions different domain owners per category (cat-22
compliance, cat-04 cloud, cat-14 OT, etc.); until co-maintainers
join, every row points at the lead maintainer — but the *shape*
is locked here so reviewer assignment cannot silently drift
back to a single catch-all rule.

What we lock here
-----------------

* The CODEOWNERS file exists at ``.github/CODEOWNERS``.
* Every ``content/cat-NN-<slug>/`` directory has a matching
  ``/content/cat-NN-<slug>/`` rule.
* Every per-category rule points at a real reviewer (not a
  placeholder like ``@TODO``) — at minimum ``@`` followed by one
  printable character.
* The default catch-all ``*`` rule still exists at the top so
  un-rule-d paths still have an owner.
* A header rule for ``/content/`` exists *before* the per-category
  block (CODEOWNERS uses last-match-wins, so the per-category
  rules need to come after the directory catch-all).

These invariants are deliberately strict; intentional changes to
any of them require updating the test in the same PR.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CODEOWNERS_PATH = REPO_ROOT / ".github" / "CODEOWNERS"
CONTENT_DIR = REPO_ROOT / "content"

CAT_DIR_RE = re.compile(r"^cat-\d{2}-[a-z0-9-]+$")


def _category_directories() -> list[str]:
    """Return the names of every ``cat-NN-<slug>/`` directory under content/.

    Sorted for deterministic test ordering. Pre-condition: at least
    one category exists (the catalogue has 23 today and a UC tree
    with zero categories would be a separate, larger failure).
    """
    return sorted(
        p.name for p in CONTENT_DIR.iterdir() if p.is_dir() and CAT_DIR_RE.match(p.name)
    )


def _codeowners_lines() -> list[str]:
    """Return the non-blank, non-comment lines of the CODEOWNERS file."""
    text = CODEOWNERS_PATH.read_text(encoding="utf-8")
    return [
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def test_codeowners_file_exists() -> None:
    """``.github/CODEOWNERS`` must exist and be non-empty."""
    assert CODEOWNERS_PATH.exists(), f"missing CODEOWNERS at {CODEOWNERS_PATH}"
    assert CODEOWNERS_PATH.stat().st_size > 0, "CODEOWNERS file is empty"


def test_codeowners_has_default_catch_all() -> None:
    """A ``*`` rule must exist so every path has at least one reviewer.

    Without a default catch-all, files outside any explicit rule —
    new top-level docs, ad-hoc tooling, fresh subtrees — would slip
    through with no reviewer assignment at all.
    """
    lines = _codeowners_lines()
    assert any(line.startswith("*") for line in lines), (
        "CODEOWNERS must contain a default catch-all rule "
        "(a line starting with ``*``). Without it, files not "
        "covered by any explicit rule have no reviewer."
    )


def test_codeowners_has_content_catch_all() -> None:
    """A ``/content/`` rule must exist (used as the fall-back per-category)."""
    lines = _codeowners_lines()
    assert any(
        line.startswith("/content/ ") or line.startswith("/content/\t")
        for line in lines
    ), (
        "CODEOWNERS must contain a ``/content/`` rule that "
        "covers every UC under the content tree by default. "
        "Per-category rules override it for specific cat-NN "
        "directories, but the fall-back must exist for any "
        "non-category files placed under content/."
    )


def test_every_category_has_codeowners_row() -> None:
    """Every cat-NN-<slug>/ directory must have its own CODEOWNERS row.

    This is the §P14 invariant: per-category routing for content
    stewardship. The plan envisions different domain owners per
    category; while there is only one maintainer the rows are
    redundant on paper, but locking the *shape* now means the
    swap-in of a co-maintainer is a one-line change rather than
    a structural refactor.
    """
    categories = _category_directories()
    assert categories, "no cat-NN-<slug>/ directories found under content/ — sanity check failed"

    text = CODEOWNERS_PATH.read_text(encoding="utf-8")
    missing: list[str] = []
    for category in categories:
        # Match `/content/<category>/` followed by whitespace, regardless
        # of how much whitespace separates the path from the owner.
        pattern = rf"^/content/{re.escape(category)}/\s+@"
        if not re.search(pattern, text, flags=re.MULTILINE):
            missing.append(category)
    assert not missing, (
        "CODEOWNERS is missing per-category rows for these "
        f"content directories: {missing!r}. Every "
        "content/cat-NN-<slug>/ directory must have a matching "
        "``/content/<cat-name>/  @owner`` row in .github/CODEOWNERS "
        "(§P14 content stewardship invariant)."
    )


def test_every_category_row_has_real_owner() -> None:
    """No CODEOWNERS row may use a placeholder like ``@TODO`` for an owner.

    The structural test would happily accept ``@TODO`` as a row, so
    this complementary check ensures the owner identifier is at
    least plausible: ``@`` followed by one printable character and
    not a known placeholder.
    """
    categories = _category_directories()
    text = CODEOWNERS_PATH.read_text(encoding="utf-8")
    placeholders = {"@TODO", "@TBD", "@FIXME", "@team", "@user"}
    bad_rows: list[str] = []
    for category in categories:
        pattern = rf"^/content/{re.escape(category)}/\s+(@\S+)"
        match = re.search(pattern, text, flags=re.MULTILINE)
        assert match is not None, f"no match for {category} — earlier test should have caught this"
        owner = match.group(1)
        if owner in placeholders or len(owner) < 2:
            bad_rows.append(f"{category}: {owner}")
    assert not bad_rows, (
        "CODEOWNERS contains placeholder owners in per-category rows: "
        f"{bad_rows!r}. Replace with a real GitHub username or team."
    )


def test_content_rule_precedes_per_category_rules() -> None:
    """The ``/content/`` rule must appear *before* any per-category rules.

    CODEOWNERS resolves to the *last* matching pattern, so per-category
    rules need to come after the directory-wide ``/content/`` catch-all.
    If the order is reversed, the per-category rules are silently
    overridden by the directory-wide one — exactly the §P14 failure
    mode we are trying to prevent.
    """
    text = CODEOWNERS_PATH.read_text(encoding="utf-8")
    content_idx = None
    first_cat_idx = None
    for i, line in enumerate(text.splitlines()):
        if line.startswith("/content/ ") or line.startswith("/content/\t"):
            if content_idx is None:
                content_idx = i
        if re.match(r"^/content/cat-\d{2}-", line) and first_cat_idx is None:
            first_cat_idx = i
    assert content_idx is not None, "no /content/ catch-all rule found"
    assert first_cat_idx is not None, "no /content/cat-NN-...  rule found"
    assert content_idx < first_cat_idx, (
        f"The /content/ catch-all rule at line {content_idx + 1} appears "
        f"after the first per-category rule at line {first_cat_idx + 1}. "
        "CODEOWNERS uses last-match-wins, so the catch-all must precede "
        "the per-category rules — otherwise the per-category routing is "
        "silently overridden."
    )
