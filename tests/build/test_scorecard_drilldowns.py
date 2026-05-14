"""Structural invariants for ``docs/scorecard.md`` per-category drill-downs.

Repo-overhaul plan §P14 second half (2026-05-13): the per-category
scorecard pairs each ``content/cat-NN-<slug>/`` directory with a
deep-linkable drill-down view inside ``docs/scorecard.md``. The plan
hinges on every CODEOWNERS row being able to land directly on its
category's composite, dimensions, depth tiers, and provenance mix via
a stable ``docs/scorecard.md#cat-NN-<slug>`` anchor.

The byte-equality contract in ``validate.yml`` already guarantees the
*content* matches the generator. This test pins the *shape*: every
content directory has a matching anchor, and every anchor maps back to
a real directory. If a category is added (or its slug changes) and the
scorecard is not regenerated, this test fails before the CODEOWNERS
link goes stale.

What we lock here
-----------------

* The scorecard exists at the canonical path.
* It carries a ``## Category drill-downs`` section so the deep-link
  index is always findable, not buried at the bottom.
* Every ``content/cat-NN-<slug>/`` directory has a matching
  ``<a id="cat-NN-<slug>"></a>`` anchor inside the drill-down section.
* The anchor set is exactly the set of content directories — no
  orphan anchors pointing at retired categories.
* Each drill-down block references its own content directory, so a
  copy-paste mistake (cat-01's block pointing at cat-02) is caught.

These invariants pair with ``tests/build/test_codeowners.py`` to keep
CODEOWNERS rows, content directories, and scorecard anchors in a
three-way alignment that cannot silently drift.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCORECARD_PATH = REPO_ROOT / "docs" / "scorecard.md"
CONTENT_DIR = REPO_ROOT / "content"

CAT_DIR_RE = re.compile(r"^cat-\d{2}-[a-z0-9-]+$")
ANCHOR_RE = re.compile(r'<a id="(cat-\d{2}-[a-z0-9-]+)"></a>')


def _category_directories() -> list[str]:
    return sorted(
        p.name for p in CONTENT_DIR.iterdir() if p.is_dir() and CAT_DIR_RE.match(p.name)
    )


def test_scorecard_doc_exists() -> None:
    assert SCORECARD_PATH.exists(), f"docs/scorecard.md must exist at {SCORECARD_PATH}"
    assert SCORECARD_PATH.stat().st_size > 0, "docs/scorecard.md is empty"


def test_scorecard_has_drilldown_section() -> None:
    """The drill-down index must be present as a level-2 heading.

    Without a stable section heading, the docs side-nav loses the
    "click into the scorecard" entry point and CODEOWNERS rows have
    nowhere obvious to deep-link into. A renamed section (e.g.
    "Category details" instead of "Category drill-downs") would
    silently break the readme/AGENTS.md cross-references that point
    here.
    """
    text = SCORECARD_PATH.read_text(encoding="utf-8")
    assert re.search(r"^##\s+Category drill-downs\s*$", text, flags=re.MULTILINE), (
        "docs/scorecard.md must contain a ``## Category drill-downs`` "
        "section. This is the deep-link index that CODEOWNERS rows and "
        "per-category routing depend on (§P14 second half, 2026-05-13)."
    )


def test_every_category_has_scorecard_anchor() -> None:
    """Every content/cat-NN-<slug>/ directory must have a matching anchor.

    The anchor format is ``<a id="cat-NN-<slug>"></a>`` and must
    appear inside the drill-down section. If a category is added
    (or its slug changes) and the scorecard is not regenerated,
    this test fails before any CODEOWNERS deep-link rots.
    """
    categories = _category_directories()
    assert categories, (
        "no cat-NN-<slug>/ directories found under content/ — sanity check failed"
    )

    text = SCORECARD_PATH.read_text(encoding="utf-8")
    anchors = set(ANCHOR_RE.findall(text))
    missing = [c for c in categories if c not in anchors]
    assert not missing, (
        "docs/scorecard.md is missing drill-down anchors for these "
        f"categories: {missing!r}. Regenerate via "
        "``python3 -m splunk_uc generate-scorecard`` and commit the "
        "result, or update the category slug in ``_category.json`` if "
        "the directory was renamed."
    )


def test_no_orphan_scorecard_anchors() -> None:
    """Every anchor in the drill-down section must map to a real directory.

    Prevents stale anchors lingering after a category is retired —
    those would create broken CODEOWNERS deep-links that look fine
    until somebody clicks them.
    """
    categories = set(_category_directories())
    text = SCORECARD_PATH.read_text(encoding="utf-8")
    anchors = set(ANCHOR_RE.findall(text))
    orphans = sorted(anchors - categories)
    assert not orphans, (
        "docs/scorecard.md contains drill-down anchors that do not "
        f"map to any content/cat-NN-<slug>/ directory: {orphans!r}. "
        "Regenerate the scorecard after retiring a category, or "
        "restore the matching directory."
    )


def test_drilldown_anchor_matches_content_link() -> None:
    """Each anchor's drill-down must link to its own content directory.

    Catches a category being copy-pasted in the source with the wrong
    cross-link (e.g. cat-01 drill-down pointing at cat-02 content).
    Looks for the canonical ``content/<slug>/`` reference inside the
    same drill-down block.
    """
    text = SCORECARD_PATH.read_text(encoding="utf-8")
    for category in _category_directories():
        start_pat = re.compile(rf'<a id="{re.escape(category)}"></a>')
        start_match = start_pat.search(text)
        assert start_match is not None, (
            f"no anchor block found for {category} — earlier test "
            "should have caught this"
        )
        rest = text[start_match.end():]
        end_match = re.search(
            r'(?:<a id="cat-\d{2}-[a-z0-9-]+"></a>|^## )',
            rest,
            flags=re.MULTILINE,
        )
        block = rest[: end_match.start()] if end_match else rest
        expected = f"`content/{category}/`"
        assert expected in block, (
            f"drill-down block for {category} must reference its own "
            f"content directory ({expected!r}). Found first 300 chars: "
            f"{block[:300]!r}"
        )
