"""Unit-level coverage for ``templates/replication-starter/build.py``.

The starter is the canonical "minimum-viable-fork" reference for
downstream catalogues (see ``docs/replication-guide.md`` and §P11 in
``AGENTS.md``). A neighbouring file
``tests/build/test_replication_starter.py`` already pins the
end-to-end build contract by running the script as a subprocess.
That provides excellent integration confidence but cannot exercise
coverage instrumentation — the subprocess loads its own interpreter
without coverage.

This file complements the subprocess suite by importing
``build.py`` directly via ``importlib.util`` (the same pattern the
script-coverage tests use for ``scripts/augment_regulation_api.py``)
and driving every branch of ``parse_category`` and ``main``
hermetically. Each test gets its own ``tmp_path`` rooted ``content/``
tree; the module's ``SCRIPT_DIR`` and ``CONTENT_DIR`` constants are
``monkeypatch.setattr``'d per test so we never touch the real
replication-starter directory shipped with the repo.

What this suite locks
---------------------

* ``parse_category`` returns ``None`` for every missing-metadata path
  (no ``_category.json``, ``id`` absent, ``id`` non-numeric).
* ``parse_category`` skips invalid subcategory shells (no ``id``).
* ``parse_category`` skips UC sidecars that are unreadable, malformed,
  or missing the ``id`` field.
* ``parse_category`` creates a *stub* subcategory bucket when a UC's
  ``id`` prefix doesn't match any declared shell — this is the
  "never silently drop a UC" promise from the docstring.
* ``main`` glob-sorts categories, skips non-directories matching the
  ``cat-*`` glob, writes ``catalog.json`` (with the ``total_uc``
  rollup) and ``data.js`` (the ``const DATA = ...;`` wrapper), and
  prints the final summary line.
* Every branch (missing meta / bad id / null id / null subcat id /
  bad UC file / missing UC id / fallback bucket / no UCs in category)
  is hit at least once.

Run
---

``pytest tests/build/test_replication_starter_unit.py``

Coverage check
--------------

``pytest tests/build/test_replication_starter_unit.py \
   --cov=replication_starter_build --cov-branch``

(the module is registered in ``sys.modules`` under the canonical
``replication_starter_build`` name; coverage tracks it there.)
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Module import
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "templates" / "replication-starter" / "build.py"

_spec = importlib.util.spec_from_file_location(
    "replication_starter_build", _SCRIPT_PATH
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("replication_starter_build", _mod)
_spec.loader.exec_module(_mod)


@pytest.fixture(scope="module")
def starter() -> Any:
    return _mod


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_category_dir(
    root: Path,
    *,
    folder: str,
    meta: dict[str, Any] | None,
    ucs: list[dict[str, Any]] | None = None,
    extra_files: list[tuple[str, str]] | None = None,
) -> Path:
    """Create one ``cat-XX/`` directory under ``root``.

    ``meta`` is the JSON payload for ``_category.json``; pass ``None`` to
    skip writing the file. ``ucs`` is a list of payloads written to
    ``UC-<id>.json`` (slugged by index). ``extra_files`` lets a test
    drop arbitrary additional files (e.g. an unreadable ``UC-bad.json``).
    """
    cat_dir = root / folder
    cat_dir.mkdir(parents=True)
    if meta is not None:
        (cat_dir / "_category.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
    for uc in ucs or []:
        uid = uc.get("id", "X.X.X")
        (cat_dir / f"UC-{uid}.json").write_text(
            json.dumps(uc), encoding="utf-8"
        )
    for name, body in extra_files or []:
        (cat_dir / name).write_text(body, encoding="utf-8")
    return cat_dir


# ---------------------------------------------------------------------------
# parse_category — happy path + every short-circuit branch
# ---------------------------------------------------------------------------


class TestParseCategoryShortCircuits:
    def test_missing_meta_returns_none(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = tmp_path / "cat-01-empty"
        cat_dir.mkdir()
        # No ``_category.json`` at all.
        assert starter.parse_category(str(cat_dir)) is None

    def test_meta_without_id_returns_none(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-no-id",
            meta={"name": "Has no id"},
        )
        assert starter.parse_category(str(cat_dir)) is None

    def test_meta_with_null_id_returns_none(
        self, starter: Any, tmp_path: Path
    ) -> None:
        """A literal ``"id": null`` is treated the same as missing
        (covers the ``cid is None`` short-circuit, not the
        non-numeric branch)."""
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-null-id",
            meta={"id": None, "name": "Null id"},
        )
        assert starter.parse_category(str(cat_dir)) is None

    def test_meta_with_non_numeric_id_returns_none(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-bad-id",
            meta={"id": "not-a-number", "name": "Bad id"},
        )
        assert starter.parse_category(str(cat_dir)) is None

    def test_meta_with_list_id_returns_none(
        self, starter: Any, tmp_path: Path
    ) -> None:
        """A non-coercible type (list) triggers the ``TypeError`` arm
        of the ``int(cid)`` conversion."""
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-list-id",
            meta={"id": [1, 2], "name": "List id"},
        )
        assert starter.parse_category(str(cat_dir)) is None


class TestParseCategoryHappyPath:
    def test_minimal_category_no_ucs(self, starter: Any, tmp_path: Path) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-empty",
            meta={"id": 1, "name": "Empty", "subcategories": []},
        )
        out = starter.parse_category(str(cat_dir))
        assert out == {"i": 1, "n": "Empty", "s": []}

    def test_category_with_declared_subcategories_and_no_ucs(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-shells",
            meta={
                "id": "1",  # string-but-numeric — exercises int(cid) success
                "name": "Shells only",
                "subcategories": [
                    {"id": "1.1", "name": "Sub one"},
                    {"id": "1.2", "name": "Sub two"},
                ],
            },
        )
        out = starter.parse_category(str(cat_dir))
        assert out is not None
        assert out["i"] == 1
        assert [s["i"] for s in out["s"]] == ["1.1", "1.2"]
        # No UCs assigned.
        assert all(s["u"] == [] for s in out["s"])

    def test_subcategories_missing_id_are_skipped(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-skip-bad-sub",
            meta={
                "id": 1,
                "name": "Skip bad",
                "subcategories": [
                    {"id": "1.1", "name": "Good"},
                    {"name": "No id"},  # falsy id → skipped
                    {"id": "", "name": "Empty id"},  # falsy id → skipped
                ],
            },
        )
        out = starter.parse_category(str(cat_dir))
        assert out is not None
        # Only the one good shell survives.
        assert [s["i"] for s in out["s"]] == ["1.1"]

    def test_uc_routed_to_declared_subcategory(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-uc-routed",
            meta={
                "id": 1,
                "name": "Routed",
                "subcategories": [{"id": "1.1", "name": "Sub one"}],
            },
            ucs=[
                {
                    "id": "1.1.1",
                    "title": "First UC",
                    "criticality": "High",
                    "difficulty": "Easy",
                },
                {
                    "id": "1.1.2",
                    "title": "Second UC",
                    "criticality": "Medium",
                    "difficulty": "Medium",
                },
            ],
        )
        out = starter.parse_category(str(cat_dir))
        assert out is not None
        assert len(out["s"]) == 1
        sub = out["s"][0]
        assert sub["i"] == "1.1"
        assert sub["u"] == [
            {"i": "1.1.1", "n": "First UC", "c": "High", "f": "Easy"},
            {"i": "1.1.2", "n": "Second UC", "c": "Medium", "f": "Medium"},
        ]

    def test_uc_with_unknown_subcategory_creates_stub_bucket(
        self, starter: Any, tmp_path: Path
    ) -> None:
        """The 'never silently drop a UC' promise — UCs whose prefix
        doesn't match a declared shell get a fresh stub bucket."""
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-orphan-uc",
            meta={
                "id": 1,
                "name": "Orphans",
                "subcategories": [{"id": "1.1", "name": "Declared"}],
            },
            ucs=[
                {"id": "1.1.1", "title": "Declared route"},
                {"id": "1.9.1", "title": "Orphan route"},
            ],
        )
        out = starter.parse_category(str(cat_dir))
        assert out is not None
        ids = [s["i"] for s in out["s"]]
        assert "1.1" in ids
        assert "1.9" in ids
        # The orphan bucket has empty name (stub) and one UC.
        orphan = next(s for s in out["s"] if s["i"] == "1.9")
        assert orphan["n"] == ""
        assert orphan["u"][0]["i"] == "1.9.1"

    def test_uc_with_missing_id_is_skipped(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-no-uc-id",
            meta={
                "id": 1,
                "name": "Skip no-id UC",
                "subcategories": [{"id": "1.1", "name": "Sub"}],
            },
            extra_files=[
                ("UC-noid.json", json.dumps({"title": "No id field"})),
                (
                    "UC-emptyid.json",
                    json.dumps({"id": "", "title": "Empty id"}),
                ),
            ],
        )
        out = starter.parse_category(str(cat_dir))
        assert out is not None
        # No UC was added to any subcategory.
        assert all(s["u"] == [] for s in out["s"])

    def test_uc_with_malformed_json_is_skipped_silently(
        self, starter: Any, tmp_path: Path
    ) -> None:
        """The ``except (OSError, json.JSONDecodeError): continue``
        path. We drop a corrupt UC-*.json file and verify the parser
        keeps the good one."""
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-bad-uc",
            meta={
                "id": 1,
                "name": "Bad UC tolerated",
                "subcategories": [{"id": "1.1", "name": "Sub"}],
            },
            ucs=[{"id": "1.1.1", "title": "Good"}],
            extra_files=[("UC-bad.json", "{ this is not valid json")],
        )
        out = starter.parse_category(str(cat_dir))
        assert out is not None
        sub = out["s"][0]
        assert [uc["i"] for uc in sub["u"]] == ["1.1.1"]

    def test_meta_with_subcategories_null_uses_empty_default(
        self, starter: Any, tmp_path: Path
    ) -> None:
        """``meta.get("subcategories", []) or []`` short-circuits to
        the empty list when ``subcategories`` is literally ``null`` —
        covers the ``or []`` defensive branch."""
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-null-subs",
            meta={"id": 1, "name": "Null subs", "subcategories": None},
        )
        out = starter.parse_category(str(cat_dir))
        assert out == {"i": 1, "n": "Null subs", "s": []}

    def test_meta_name_missing_defaults_to_empty_string(
        self, starter: Any, tmp_path: Path
    ) -> None:
        cat_dir = _make_category_dir(
            tmp_path,
            folder="cat-01-no-name",
            meta={"id": 1, "subcategories": []},
        )
        out = starter.parse_category(str(cat_dir))
        assert out is not None
        assert out["n"] == ""


# ---------------------------------------------------------------------------
# main — orchestration, IO, and CLI summary line
# ---------------------------------------------------------------------------


class TestMain:
    def _wire_content(
        self,
        starter: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        *,
        categories: list[tuple[str, dict[str, Any], list[dict[str, Any]]]],
        extras: list[Path] | None = None,
    ) -> Path:
        """Point the module's SCRIPT_DIR + CONTENT_DIR at tmp_path and
        materialise the requested categories.

        ``categories`` is a list of ``(folder, meta, ucs)`` triples.
        ``extras`` (optional) is a list of extra directories or files
        to drop under ``content/`` (used to verify the non-dir
        ``cat-*`` filter).
        """
        content = tmp_path / "content"
        content.mkdir(parents=True)
        for folder, meta, ucs in categories:
            _make_category_dir(content, folder=folder, meta=meta, ucs=ucs)
        for extra in extras or []:
            extra.touch() if not extra.is_dir() else None
        monkeypatch.setattr(starter, "SCRIPT_DIR", str(tmp_path))
        monkeypatch.setattr(starter, "CONTENT_DIR", str(content))
        return content

    def test_main_writes_catalog_json_and_data_js(
        self,
        starter: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._wire_content(
            starter,
            tmp_path,
            monkeypatch,
            categories=[
                (
                    "cat-01-foo",
                    {
                        "id": 1,
                        "name": "Foo",
                        "subcategories": [{"id": "1.1", "name": "Sub"}],
                    },
                    [
                        {
                            "id": "1.1.1",
                            "title": "UC A",
                            "criticality": "High",
                            "difficulty": "Easy",
                        },
                        {
                            "id": "1.1.2",
                            "title": "UC B",
                            "criticality": "Low",
                            "difficulty": "Hard",
                        },
                    ],
                ),
                (
                    "cat-02-bar",
                    {
                        "id": 2,
                        "name": "Bar",
                        "subcategories": [{"id": "2.1", "name": "Sub"}],
                    },
                    [
                        {
                            "id": "2.1.1",
                            "title": "UC C",
                            "criticality": "Medium",
                            "difficulty": "Medium",
                        },
                    ],
                ),
            ],
        )
        starter.main()
        cat_json = json.loads(
            (tmp_path / "catalog.json").read_text(encoding="utf-8")
        )
        assert cat_json["total_uc"] == 3
        assert [c["i"] for c in cat_json["data"]] == [1, 2]
        data_js = (tmp_path / "data.js").read_text(encoding="utf-8")
        assert data_js.startswith("const DATA = ")
        assert data_js.rstrip().endswith(";")
        # The JSON payload inside the wrapper is the same ``data`` list.
        body = data_js[len("const DATA = ") : data_js.rstrip().rfind(";")]
        assert json.loads(body) == cat_json["data"]
        out = capsys.readouterr().out.strip()
        assert "Built 2 categories, 3 use cases." == out

    def test_main_skips_non_directory_entries_matching_cat_glob(
        self,
        starter: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A stray ``cat-99-foo`` *file* (not a directory) under
        ``content/`` must be filtered by the ``os.path.isdir`` guard
        in ``main``."""
        content = self._wire_content(
            starter,
            tmp_path,
            monkeypatch,
            categories=[
                (
                    "cat-01-foo",
                    {"id": 1, "name": "Foo", "subcategories": []},
                    [],
                ),
            ],
        )
        # File matching the glob but not a directory.
        (content / "cat-99-stray-file").write_text("ignored", encoding="utf-8")
        starter.main()
        cat_json = json.loads(
            (tmp_path / "catalog.json").read_text(encoding="utf-8")
        )
        # Only the real cat-01 made it through.
        assert [c["i"] for c in cat_json["data"]] == [1]

    def test_main_drops_categories_that_parse_to_none(
        self,
        starter: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``parse_category`` returns ``None`` when meta is missing or
        ``id`` is bad. ``main`` must filter those out — covers the
        ``if cat is not None`` branch."""
        self._wire_content(
            starter,
            tmp_path,
            monkeypatch,
            categories=[
                (
                    "cat-01-good",
                    {"id": 1, "name": "Good", "subcategories": []},
                    [],
                ),
                # Missing meta — parse_category returns None.
                ("cat-02-bare", None, []),
                # Bad id — parse_category returns None.
                (
                    "cat-03-bad",
                    {"id": "not-a-number", "name": "Bad"},
                    [],
                ),
            ],
        )
        starter.main()
        cat_json = json.loads(
            (tmp_path / "catalog.json").read_text(encoding="utf-8")
        )
        assert [c["i"] for c in cat_json["data"]] == [1]

    def test_main_emits_zero_summary_when_no_categories(
        self,
        starter: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        self._wire_content(starter, tmp_path, monkeypatch, categories=[])
        starter.main()
        assert "Built 0 categories, 0 use cases." in capsys.readouterr().out

    def test_main_total_uc_counts_orphan_buckets(
        self,
        starter: Any,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The ``total`` sum walks every subcategory's ``u`` list,
        so UCs that landed in stub buckets must still be counted."""
        self._wire_content(
            starter,
            tmp_path,
            monkeypatch,
            categories=[
                (
                    "cat-01-mix",
                    {
                        "id": 1,
                        "name": "Mixed",
                        "subcategories": [{"id": "1.1", "name": "Sub"}],
                    },
                    [
                        {"id": "1.1.1", "title": "Declared"},
                        {"id": "1.9.1", "title": "Orphan"},
                    ],
                ),
            ],
        )
        starter.main()
        out = capsys.readouterr().out.strip()
        assert out == "Built 1 categories, 2 use cases."
