"""Structural & build-contract invariants for ``templates/replication-starter/``.

Repo-overhaul plan §P11 (2026-05-09): the replication starter is the
canonical "minimum-viable-fork" reference for downstream catalogues.
``docs/replication-guide.md`` and ``AGENTS.md`` both promise that a
new contributor can clone the repo, run ``python3 build.py`` inside
``templates/replication-starter/``, and get a working static dashboard
in under five minutes. If that promise silently breaks (parser
regression, schema dialect drift, README link rot, committed
``catalog.json`` / ``data.js`` going stale), the only people who notice
are first-time forkers — exactly the audience we cannot afford to lose.

These tests pin the contract so drift surfaces in CI, not in a
forker's first hour.

What we lock here
-----------------

* All starter files exist (README, build.py, schema, sample JSON SSOT
  fixture, html).
* ``catalog.schema.json`` is valid JSON Schema 2020-12.
* ``build.py`` exits cleanly when invoked from any working directory
  (relies on ``SCRIPT_DIR`` resolution).
* ``build.py`` produces both ``catalog.json`` and ``data.js`` in the
  starter directory.
* The generated ``catalog.json`` validates against the bundled schema.
* The committed ``catalog.json`` and ``data.js`` are byte-identical to
  what a fresh ``build.py`` produces — i.e. the committed artefacts are
  never stale (forkers serving the dir over GitHub Pages get a working
  dashboard without running the build first).
* The parser produces the exact known fixture content for the bundled
  ``content/cat-01-example/`` (cat 1 / sub 1.1 / UCs 1.1.1 + 1.1.2 with
  the expected key abbreviations).
* ``data.js`` wraps ``catalog.json["data"]`` in a ``const DATA = …;``
  IIFE-friendly assignment that ``index.html`` consumes.
* The starter uses the same key abbreviations (``i``, ``n``, ``s``,
  ``u``) as the parent catalogue, so a fork can graduate to
  ``tools/build/`` without rewiring its frontend.
* ``index.html`` references ``data.js`` (not ``catalog.json``) so the
  static-host deployment promised by the README actually works.
* ``README.md`` cross-references ``docs/replication-guide.md`` and the
  guide cross-references the starter — drift in either direction
  catches both.
* ``build.py`` does not mutate its input JSON sidecars (idempotency).

These invariants are deliberately strict; intentional changes to any
of them require updating the test in the same PR, which is the right
review-burden trade-off for a public-facing template.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTER_DIR = REPO_ROOT / "templates" / "replication-starter"
BUILD_PY = STARTER_DIR / "build.py"
README = STARTER_DIR / "README.md"
SCHEMA = STARTER_DIR / "catalog.schema.json"
CONTENT_DIR = STARTER_DIR / "content"
CATEGORY_META = CONTENT_DIR / "cat-01-example" / "_category.json"
SAMPLE_UC1 = CONTENT_DIR / "cat-01-example" / "UC-1.1.1.json"
SAMPLE_UC2 = CONTENT_DIR / "cat-01-example" / "UC-1.1.2.json"
INDEX_HTML = STARTER_DIR / "index.html"
COMMITTED_CATALOG = STARTER_DIR / "catalog.json"
COMMITTED_DATA_JS = STARTER_DIR / "data.js"

REPLICATION_GUIDE = REPO_ROOT / "docs" / "replication-guide.md"
AGENTS_MD = REPO_ROOT / "AGENTS.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_starter_build(workdir: Path) -> subprocess.CompletedProcess[str]:
    """Run the starter ``build.py`` in *workdir* with the current Python.

    We invoke via ``sys.executable`` instead of ``python3`` so the test
    runs against the same interpreter that ships ``pytest``. This
    matters in CI where ``python3`` may resolve to a different minor
    than the one pytest is using.
    """
    return subprocess.run(
        [sys.executable, str(workdir / "build.py")],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


@pytest.fixture
def starter_copy(tmp_path: Path) -> Path:
    """Materialise an isolated, writable copy of the starter dir.

    The starter ships *committed* ``catalog.json`` / ``data.js`` so a
    forker who clones the repo gets a working dashboard immediately.
    But running ``build.py`` rewrites those files. To avoid mutating
    the real repo during the test (and to let parallel pytest workers
    coexist), every test gets its own ephemeral copy.
    """
    dst = tmp_path / "replication-starter"
    shutil.copytree(STARTER_DIR, dst)
    return dst


# ---------------------------------------------------------------------------
# 1. File-presence invariants
# ---------------------------------------------------------------------------


def test_starter_files_exist() -> None:
    """All starter files referenced by ``docs/replication-guide.md`` exist.

    If any of these go missing, the starter walkthrough in the
    replication guide is broken on the very first command.
    """
    expected = {
        "README.md": README,
        "build.py": BUILD_PY,
        "catalog.schema.json": SCHEMA,
        "content/cat-01-example/_category.json": CATEGORY_META,
        "content/cat-01-example/UC-1.1.1.json": SAMPLE_UC1,
        "content/cat-01-example/UC-1.1.2.json": SAMPLE_UC2,
        "index.html": INDEX_HTML,
    }
    missing = [name for name, path in expected.items() if not path.is_file()]
    assert not missing, (
        f"replication starter is missing required files: {missing}; "
        "docs/replication-guide.md §3 promises these paths exist"
    )


def test_committed_artefacts_present() -> None:
    """Generated ``catalog.json`` and ``data.js`` are committed.

    The starter is intended to be served over GitHub Pages with no
    build step (a forker's first instinct: "does this thing work
    out-of-the-box?"). Committing the generated artefacts means the
    static-host deployment path documented in §3 of the replication
    guide actually produces a working dashboard on first paint.
    """
    assert COMMITTED_CATALOG.is_file(), (
        "templates/replication-starter/catalog.json is missing — "
        "should be committed so static hosting works without a build step"
    )
    assert COMMITTED_DATA_JS.is_file(), (
        "templates/replication-starter/data.js is missing — "
        "should be committed so index.html renders without a build step"
    )


# ---------------------------------------------------------------------------
# 2. Schema sanity
# ---------------------------------------------------------------------------


def test_schema_is_valid_json_schema() -> None:
    """``catalog.schema.json`` is itself a valid JSON Schema document."""
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


# ---------------------------------------------------------------------------
# 3. Build behaviour
# ---------------------------------------------------------------------------


def test_build_invokable_from_any_cwd(starter_copy: Path, tmp_path: Path) -> None:
    """``build.py`` resolves its inputs from ``__file__``, not ``os.getcwd()``.

    Forkers commonly invoke the script from the parent repo root via
    ``python3 templates/replication-starter/build.py``. This guards
    that ``SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))``
    keeps working — i.e. the build doesn't accidentally start
    consuming the current directory's ``content/`` tree.
    """
    foreign_cwd = tmp_path / "foreign-cwd"
    foreign_cwd.mkdir()
    result = subprocess.run(
        [sys.executable, str(starter_copy / "build.py")],
        cwd=str(foreign_cwd),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"build.py failed when invoked from a foreign cwd; stderr=\n{result.stderr}"
    )
    # Outputs must land next to build.py, not in the foreign cwd.
    assert (starter_copy / "catalog.json").is_file()
    assert (starter_copy / "data.js").is_file()
    assert not (foreign_cwd / "catalog.json").exists()
    assert not (foreign_cwd / "data.js").exists()


def test_build_does_not_mutate_input(starter_copy: Path) -> None:
    """The parser is read-only: input JSON sidecars stay byte-identical.

    Locks the contract that re-running the build is safe (forkers
    iterate: edit JSON → run build → refresh browser → edit JSON →
    run build → ...). A bug that rewrote the sidecars in-place would
    silently destroy a forker's edits between iterations.
    """
    sample = starter_copy / "content" / "cat-01-example" / "UC-1.1.1.json"
    before = hashlib.sha256(sample.read_bytes()).hexdigest()
    _run_starter_build(starter_copy)
    after = hashlib.sha256(sample.read_bytes()).hexdigest()
    assert before == after, (
        "build.py mutated its input JSON sidecar — re-running the build is no longer idempotent"
    )


def test_build_is_byte_reproducible(starter_copy: Path) -> None:
    """Two consecutive builds produce byte-identical outputs.

    Required for the freshness gate (next test) to be tractable: if
    the parser emitted nondeterministic output (dict ordering, ISO
    timestamps, etc.) the committed bytes would always look stale.
    """
    _run_starter_build(starter_copy)
    first_catalog = (starter_copy / "catalog.json").read_bytes()
    first_data_js = (starter_copy / "data.js").read_bytes()
    _run_starter_build(starter_copy)
    second_catalog = (starter_copy / "catalog.json").read_bytes()
    second_data_js = (starter_copy / "data.js").read_bytes()
    assert first_catalog == second_catalog, "catalog.json is not byte-reproducible"
    assert first_data_js == second_data_js, "data.js is not byte-reproducible"


def test_committed_artefacts_are_fresh(starter_copy: Path) -> None:
    """Committed ``catalog.json`` / ``data.js`` match a fresh build.

    The starter ships these files committed (so static hosting works
    without a build step) — they MUST stay byte-identical to whatever
    ``build.py`` would produce today. If the parser changes or the
    bundled JSON sidecars change without rebuilding, this test catches
    the drift before the static dashboard goes silently stale.

    Maintainer fix when this fails:
    ::

        cd templates/replication-starter
        python3 build.py
        git add catalog.json data.js && git commit
    """
    _run_starter_build(starter_copy)
    fresh_catalog = (starter_copy / "catalog.json").read_bytes()
    fresh_data_js = (starter_copy / "data.js").read_bytes()
    committed_catalog = COMMITTED_CATALOG.read_bytes()
    committed_data_js = COMMITTED_DATA_JS.read_bytes()
    assert committed_catalog == fresh_catalog, (
        "templates/replication-starter/catalog.json is stale; rerun "
        "`cd templates/replication-starter && python3 build.py` and "
        "commit the result"
    )
    assert committed_data_js == fresh_data_js, (
        "templates/replication-starter/data.js is stale; rerun "
        "`cd templates/replication-starter && python3 build.py` and "
        "commit the result"
    )


# ---------------------------------------------------------------------------
# 4. Output shape & schema conformance
# ---------------------------------------------------------------------------


def test_committed_catalog_validates_against_schema() -> None:
    """The committed ``catalog.json`` validates against ``catalog.schema.json``.

    The bundled schema is the contract a forker writes their first
    custom audits against; if the build produces a doc that doesn't
    validate, every downstream tool is starting on a lie.
    """
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    catalog = json.loads(COMMITTED_CATALOG.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(catalog), key=lambda e: e.path)
    assert not errors, "committed catalog.json fails its own schema; first error: " + (
        f"{errors[0].message} at /{'/'.join(str(p) for p in errors[0].absolute_path)}"
        if errors
        else ""
    )


def test_committed_catalog_known_fixtures() -> None:
    """The committed catalog has the exact expected fixture content.

    The bundled SSOT declares one category, one subcategory, two UCs.
    Pinning the parsed values guards against parser-regression bugs
    that silently swallow fields (e.g. dropping ``criticality``
    because of a key-mapping tweak).
    """
    catalog = json.loads(COMMITTED_CATALOG.read_text(encoding="utf-8"))
    assert catalog["total_uc"] == 2, f"total_uc drifted; got {catalog['total_uc']}, expected 2"
    assert len(catalog["data"]) == 1, "expected exactly one category"
    cat = catalog["data"][0]
    assert cat["i"] == 1
    assert cat["n"] == "Example Category"
    assert len(cat["s"]) == 1
    sub = cat["s"][0]
    assert sub["i"] == "1.1"
    assert sub["n"] == "Example Subcategory"
    assert len(sub["u"]) == 2
    uc1, uc2 = sub["u"]
    assert uc1["i"] == "1.1.1"
    assert uc1["n"] == "Failed login spike"
    assert uc1["c"] == "High"
    assert uc1["f"] == "Beginner"
    assert uc2["i"] == "1.1.2"
    assert uc2["n"] == "Disk usage nearing capacity"
    assert uc2["c"] == "Medium"
    assert uc2["f"] == "Beginner"


def test_total_uc_matches_data() -> None:
    """``total_uc`` is the correct sum of every nested UC array.

    Trivial arithmetic, but the kind of off-by-one that gets
    silently wrong when a parser branch is added.
    """
    catalog = json.loads(COMMITTED_CATALOG.read_text(encoding="utf-8"))
    counted = sum(len(sub["u"]) for cat in catalog["data"] for sub in cat["s"])
    assert catalog["total_uc"] == counted, (
        f"total_uc={catalog['total_uc']} but counted {counted} UCs across the nested data tree"
    )


def test_field_keys_use_short_form() -> None:
    """SSOT JSON fields are mapped to the short-key wire shape.

    The parent catalogue's frontend iterates ``i`` / ``n`` / ``c`` / ``f``
    instead of the full names so its JSON payload is small. The starter
    must follow the same convention so a fork can graduate to
    ``tools/build/`` without rewiring its frontend.
    """
    catalog = json.loads(COMMITTED_CATALOG.read_text(encoding="utf-8"))
    uc = catalog["data"][0]["s"][0]["u"][0]
    expected_keys = {"i", "n", "c", "f"}
    assert set(uc.keys()) == expected_keys, (
        f"UC field keys drifted; got {set(uc.keys())}, expected {expected_keys}"
    )


def test_data_js_wraps_catalog_data() -> None:
    """``data.js`` is ``const DATA = <catalog.data JSON>;\\n``.

    The starter ``index.html`` does ``<script src="data.js">`` then
    iterates ``DATA``. Lock the wrapper format so the dashboard stays
    bootable from a static host (no module loaders, no fetch()).
    """
    text = COMMITTED_DATA_JS.read_text(encoding="utf-8")
    assert text.startswith("const DATA = "), (
        f"data.js prefix drifted; first 40 chars = {text[:40]!r}"
    )
    assert text.rstrip().endswith(";"), (
        "data.js must end with ';' so the assignment is statement-terminated"
    )
    payload = text[len("const DATA = ") :].rstrip().rstrip(";")
    parsed = json.loads(payload)
    catalog = json.loads(COMMITTED_CATALOG.read_text(encoding="utf-8"))
    assert parsed == catalog["data"], (
        "data.js payload drifted from catalog.json['data']; the two are "
        "supposed to be the same JSON, just one wrapped in 'const DATA ='"
    )


def test_starter_uses_parent_key_abbreviations() -> None:
    """Starter uses the same ``i``/``n``/``s``/``u`` keys as the parent catalogue.

    Documented in ``docs/catalog-schema.md``: the parent catalog uses
    ``i`` for ID, ``n`` for name, ``s`` for subcategories, ``u`` for
    use cases. The starter must match so a fork can graduate to
    ``tools/build/`` without rewiring its frontend (its ``index.html``
    iterates ``cat.s`` and ``sub.u`` — so does the parent).
    """
    catalog = json.loads(COMMITTED_CATALOG.read_text(encoding="utf-8"))
    cat = catalog["data"][0]
    assert "i" in cat and "n" in cat and "s" in cat
    sub = cat["s"][0]
    assert "i" in sub and "n" in sub and "u" in sub
    uc = sub["u"][0]
    assert "i" in uc and "n" in uc


# ---------------------------------------------------------------------------
# 5. HTML dependency contract
# ---------------------------------------------------------------------------


def test_index_html_loads_data_js() -> None:
    """``index.html`` <script-src>s ``data.js`` (not catalog.json).

    The committed ``data.js`` is the ``DATA`` global the inline
    script reads. If someone refactors the HTML to ``fetch()`` the
    catalog instead, the static-host promise breaks because GitHub
    Pages serves files but won't satisfy a same-origin fetch on
    ``file://`` previews.
    """
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert '<script src="data.js"></script>' in html, (
        'index.html must <script src="data.js"> so the static-host '
        "deployment works without a build step or fetch()"
    )
    assert "fetch(" not in html, (
        "index.html should not fetch() its data — keep it static-host "
        "friendly so file:// previews and GitHub Pages both work"
    )


def test_index_html_iterates_starter_shape() -> None:
    """``index.html`` reads the same key abbreviations the parser emits.

    Not a strict test (the regex is forgiving) but catches the
    obvious case where the HTML drifts from ``cat.s`` / ``sub.u``
    while the build still emits those keys.
    """
    html = INDEX_HTML.read_text(encoding="utf-8")
    assert re.search(r"\bcat\.s\b|\bof\s+\(?cat\.s\b", html), (
        "index.html doesn't iterate cat.s — drifted from parser output shape"
    )
    assert re.search(r"\bsub\.u\b|\bof\s+\(?sub\.u\b", html), (
        "index.html doesn't iterate sub.u — drifted from parser output shape"
    )


# ---------------------------------------------------------------------------
# 6. Documentation cross-references
# ---------------------------------------------------------------------------


def test_readme_links_replication_guide() -> None:
    """The starter README points back at ``docs/replication-guide.md``.

    The README is the entry point for someone who lands in the
    starter directly (e.g. via a GitHub search hit). Drifting away
    from the canonical replication guide turns the starter into an
    orphaned fork-of-a-fork.
    """
    readme = README.read_text(encoding="utf-8")
    assert "../../docs/replication-guide.md" in readme, (
        "templates/replication-starter/README.md must link to "
        "../../docs/replication-guide.md so forkers can find the full guide"
    )


def test_replication_guide_links_starter() -> None:
    """``docs/replication-guide.md`` references the starter directory.

    The guide promises in §3 ("Starter template walkthrough") that
    the starter lives at ``templates/replication-starter/``. The doc
    and the actual path must agree.
    """
    guide = REPLICATION_GUIDE.read_text(encoding="utf-8")
    assert "templates/replication-starter" in guide, (
        "docs/replication-guide.md doesn't reference templates/replication-starter — "
        "the §3 walkthrough is broken"
    )


def test_readme_lists_real_files() -> None:
    """Files mentioned in the README "Files" table must actually exist.

    Catches the common drift where a file is renamed/removed from
    the starter but the README's table still lists the old name.
    """
    readme = README.read_text(encoding="utf-8")
    referenced_files = {
        "build.py",
        "content/cat-01-example/_category.json",
        "content/cat-01-example/UC-1.1.1.json",
        "content/cat-01-example/UC-1.1.2.json",
        "index.html",
        "catalog.schema.json",
    }
    missing = []
    for filename in referenced_files:
        if filename not in readme:
            missing.append(f"{filename} (not mentioned in README)")
            continue
        if not (STARTER_DIR / filename).exists():
            missing.append(f"{filename} (mentioned but missing on disk)")
    assert not missing, f"README ↔ filesystem drift: {missing}"


def test_starter_referenced_in_agents_md() -> None:
    """``AGENTS.md`` advertises the starter under §"Further reading".

    Locks the discoverability contract: an AI agent reading
    ``AGENTS.md`` should be able to find the minimal-fork example
    without searching.
    """
    agents = AGENTS_MD.read_text(encoding="utf-8")
    assert "templates/replication-starter" in agents, (
        "AGENTS.md no longer references templates/replication-starter — "
        "the minimal-fork pointer for AI agents is broken"
    )


# ---------------------------------------------------------------------------
# 7. Version-bump policy
# ---------------------------------------------------------------------------


def test_starter_does_not_pin_repo_version() -> None:
    """The starter's docs do not pin a specific upstream ``VERSION``.

    Version-bump policy (P11): the starter is **version-agnostic**.
    It demonstrates the *pattern* (JSON SSOT → catalog.json via ~80 LOC),
    not a particular release of the upstream catalogue. Embedding a
    specific version in the README would force a same-PR update on
    every release, which we don't want — the starter shape rarely
    changes between releases.

    If a real semantic-version dependency is ever needed (e.g. the
    schema dialect bumps), encode it via the ``$schema`` URL inside
    ``catalog.schema.json``, not as a string in prose.
    """
    readme = README.read_text(encoding="utf-8")
    # Match a canonical SemVer like X.Y.Z (e.g. "8.1.0") but allow
    # "v8" / "v8.x" generic references to the major series.
    semver_re = re.compile(r"\bv?\d+\.\d+\.\d+\b")
    matches = semver_re.findall(readme)
    assert not matches, (
        f"README pins specific version(s) {matches}; replace with "
        "version-agnostic prose ('v8 series', 'current schema') so the "
        "starter doesn't need a same-PR update on every release"
    )
