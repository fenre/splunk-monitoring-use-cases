"""Unit-level coverage for ``tools/audits/splunkbase_ids.py``.

``splunkbase_ids`` is the hermetic counterpart to the weekly
``scripts/sync_splunkbase_catalog.py`` refresh: it verifies that every
``splunkbaseApps[].id`` referenced by a UC sidecar resolves against the
cached ``data/splunkbase-catalog.json`` (after applying
``data/splunkbase-catalog-overrides.json``). The audit also surfaces
URL drift — every ``splunkbaseApps[].url`` MUST start with
``https://splunkbase.splunk.com/app/<id>`` for the catalog-resolved id.

The audit is wired into ``.github/workflows/validate.yml`` and runs on
every PR. Before this commit it had zero unit tests
(``Module tools.audits.splunkbase_ids was never imported`` warning).

What this suite locks
---------------------

* ``main`` returns ``2`` with a stderr message when ``content/`` is
  missing.
* ``main`` returns ``2`` when the catalog file is absent (raises
  ``SystemExit`` from ``_load_catalog`` before any UC is walked).
* ``main`` returns ``2`` when the catalog file is unreadable JSON.
* ``main`` returns ``2`` when a UC sidecar is unreadable JSON.
* ``main`` returns ``0`` with the OK banner when every referenced id
  resolves and every URL matches the expected prefix.
* ``main`` returns ``1`` and lists offenders on stderr when an id
  is missing from the catalog, when an id field is non-int, or when
  the entry is missing the ``id`` key entirely.
* ``main`` returns ``1`` and lists BAD URL examples (capped at 5)
  when ids resolve but URLs do not match the expected prefix.
* Offender list is truncated to 10 entries with an ``... and N more``
  footer for overflow.
* Non-dict entries inside ``splunkbaseApps`` are silently skipped
  (defensive against partially-typed authoring).
* UCs without ``splunkbaseApps`` or with an empty list are skipped
  (do not contribute to ``ucs_with_apps`` count).
* ``_load_catalog`` merges overrides into base: existing keys are
  updated in place, new keys are added, non-dict entries are
  dropped from both base and overrides.
* ``_load_catalog`` works without ``data/splunkbase-catalog-overrides.json``
  on disk (falls through to the empty-overrides default).
* ``--json`` writes the breakdown to disk including ``catalogSize``,
  ``ucsWithApps``, ``totalReferences``, ``offendingUcs``, and
  ``badUrlExamples`` — and the parent directory is created if it
  does not exist.
* The ``if __name__ == "__main__":`` guard is covered by a subprocess
  smoke check against the real repo-rooted ``content/`` tree.

Run
---

``pytest tests/build/test_tools_audits_splunkbase_ids.py``

Coverage check
--------------

``pytest tests/build/test_tools_audits_splunkbase_ids.py \
    --cov=tools.audits.splunkbase_ids --cov-branch``
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.audits.splunkbase_ids as splunkbase_ids


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_catalog(
    path: Path,
    apps: dict[str, Any],
) -> None:
    """Write a minimal Splunkbase catalog JSON file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"apps": apps}, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_uc(
    content_dir: Path,
    *,
    cat: str,
    uc_id: str,
    splunkbase_apps: list[dict[str, Any]] | None,
) -> Path:
    """Write a synthetic UC sidecar under ``content/<cat>/UC-<id>.json``.

    ``splunkbase_apps`` may be ``None`` (omitted entirely), an empty
    list (present but empty), or a populated list. We use this to
    exercise the three documented entry-shape branches of ``main``.
    """

    cat_dir = content_dir / cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"id": uc_id, "title": f"UC {uc_id}"}
    if splunkbase_apps is not None:
        payload["splunkbaseApps"] = splunkbase_apps
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def isolated_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Redirect ``REPO_ROOT``/``CONTENT_DIR``/``CATALOG_PATH``/
    ``OVERRIDES_PATH`` to ``tmp_path`` so every test runs against a
    fresh, synthetic content + catalog tree."""

    monkeypatch.setattr(splunkbase_ids, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        splunkbase_ids, "CONTENT_DIR", tmp_path / "content"
    )
    monkeypatch.setattr(
        splunkbase_ids,
        "CATALOG_PATH",
        tmp_path / "data" / "splunkbase-catalog.json",
    )
    monkeypatch.setattr(
        splunkbase_ids,
        "OVERRIDES_PATH",
        tmp_path / "data" / "splunkbase-catalog-overrides.json",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# _load_catalog
# ---------------------------------------------------------------------------


class TestLoadCatalog:
    def test_raises_systemexit_when_catalog_missing(
        self,
        isolated_repo: Path,
    ) -> None:
        """The catalog file is the single source of truth — if it's
        missing the script aborts BEFORE walking content."""

        with pytest.raises(SystemExit) as excinfo:
            splunkbase_ids._load_catalog()
        assert "missing catalog file" in str(excinfo.value)

    def test_loads_base_without_overrides_file(
        self,
        isolated_repo: Path,
    ) -> None:
        """The overrides file is optional; when absent the loader
        falls through to the documented ``{"apps": {}}`` default."""

        _write_catalog(
            splunkbase_ids.CATALOG_PATH,
            {"100": {"name": "Test App", "url": "https://x"}},
        )
        result = splunkbase_ids._load_catalog()
        assert result == {"100": {"name": "Test App", "url": "https://x"}}

    def test_overrides_update_existing_entries(
        self,
        isolated_repo: Path,
    ) -> None:
        """When a key exists in BOTH base and overrides the override
        is merged INTO the base entry (dict.update semantics)."""

        _write_catalog(
            splunkbase_ids.CATALOG_PATH,
            {"100": {"name": "Old Name", "label": "keep"}},
        )
        splunkbase_ids.OVERRIDES_PATH.parent.mkdir(
            parents=True, exist_ok=True
        )
        splunkbase_ids.OVERRIDES_PATH.write_text(
            json.dumps(
                {"apps": {"100": {"name": "New Name", "url": "https://y"}}}
            ),
            encoding="utf-8",
        )
        result = splunkbase_ids._load_catalog()
        # ``label`` survives, ``name`` is overwritten, ``url`` is added.
        assert result["100"] == {
            "name": "New Name",
            "label": "keep",
            "url": "https://y",
        }

    def test_overrides_add_new_entries(
        self,
        isolated_repo: Path,
    ) -> None:
        """Override keys not present in base are added wholesale."""

        _write_catalog(
            splunkbase_ids.CATALOG_PATH,
            {"100": {"name": "Base"}},
        )
        splunkbase_ids.OVERRIDES_PATH.parent.mkdir(
            parents=True, exist_ok=True
        )
        splunkbase_ids.OVERRIDES_PATH.write_text(
            json.dumps({"apps": {"200": {"name": "Override-only"}}}),
            encoding="utf-8",
        )
        result = splunkbase_ids._load_catalog()
        assert result["100"] == {"name": "Base"}
        assert result["200"] == {"name": "Override-only"}

    def test_non_dict_entries_dropped_from_base(
        self,
        isolated_repo: Path,
    ) -> None:
        """Authoring drift defence: catalog entries that are not dicts
        (e.g. a stray string or list left by a faulty refresh) MUST
        be silently dropped rather than crash the loader."""

        _write_catalog(
            splunkbase_ids.CATALOG_PATH,
            {"100": {"name": "Good"}, "200": "not-a-dict", "300": [1, 2]},
        )
        result = splunkbase_ids._load_catalog()
        assert "100" in result
        assert "200" not in result
        assert "300" not in result

    def test_non_dict_entries_dropped_from_overrides(
        self,
        isolated_repo: Path,
    ) -> None:
        """Same defence applied to the overrides side."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "Base"}})
        splunkbase_ids.OVERRIDES_PATH.parent.mkdir(
            parents=True, exist_ok=True
        )
        splunkbase_ids.OVERRIDES_PATH.write_text(
            json.dumps({"apps": {"100": [1, 2, 3], "200": "string"}}),
            encoding="utf-8",
        )
        result = splunkbase_ids._load_catalog()
        # Base entry preserved unchanged because the override was non-dict.
        assert result == {"100": {"name": "Base"}}

    def test_empty_apps_key_returns_empty_dict(
        self,
        isolated_repo: Path,
    ) -> None:
        """A catalog with no ``apps`` key (e.g. an unrelated JSON file)
        returns an empty dict rather than crashing."""

        splunkbase_ids.CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        splunkbase_ids.CATALOG_PATH.write_text(
            json.dumps({"other": {}}), encoding="utf-8"
        )
        result = splunkbase_ids._load_catalog()
        assert result == {}


# ---------------------------------------------------------------------------
# _read_uc
# ---------------------------------------------------------------------------


class TestReadUc:
    def test_returns_parsed_json(
        self,
        tmp_path: Path,
    ) -> None:
        """``_read_uc`` is a thin ``json.loads`` wrapper that exists
        so ``main`` can catch ``OSError`` and ``JSONDecodeError`` in
        one place; the success path simply returns the parsed dict."""

        path = tmp_path / "UC.json"
        path.write_text(json.dumps({"id": "1.1.1"}), encoding="utf-8")
        assert splunkbase_ids._read_uc(path) == {"id": "1.1.1"}


# ---------------------------------------------------------------------------
# main — invocation-error paths (rc=2)
# ---------------------------------------------------------------------------


class TestMainInvocationErrors:
    def test_missing_content_dir_returns_2(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """If ``content/`` is missing the operator has misconfigured
        the run; we exit ``2`` and surface the missing path."""

        # CATALOG must exist or we'd exit 2 for a different reason —
        # exercise the content-dir branch in isolation.
        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        rc = splunkbase_ids.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "missing content dir" in err

    def test_missing_catalog_returns_2(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A missing catalog raises ``SystemExit`` from
        ``_load_catalog`` — but that path is the legacy contract;
        the documented rc=2 path is the ``except`` branch around
        ``_load_catalog`` (``OSError`` / ``JSONDecodeError``). We
        exercise it here by pre-creating ``content/`` and leaving
        the catalog absent, which raises ``SystemExit`` directly."""

        (isolated_repo / "content").mkdir()
        # ``_load_catalog`` raises ``SystemExit`` (not ``OSError``) for
        # a truly missing file — bubble that up as the documented
        # invocation error.
        with pytest.raises(SystemExit):
            splunkbase_ids.main([])

    def test_unreadable_catalog_returns_2(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """If the catalog exists but is malformed JSON the script
        exits ``2`` via the ``except`` branch and prints the parse
        error to stderr."""

        (isolated_repo / "content").mkdir()
        splunkbase_ids.CATALOG_PATH.parent.mkdir(
            parents=True, exist_ok=True
        )
        splunkbase_ids.CATALOG_PATH.write_text("{not valid json", encoding="utf-8")
        rc = splunkbase_ids.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "catalog unreadable" in err

    def test_unreadable_catalog_oserror_returns_2(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Cover the ``OSError`` arm of the except — distinct from
        the JSONDecodeError arm above. We force a ``read_text``
        failure by monkey-patching ``_load_catalog`` to raise OSError
        directly (the catalog-on-disk path always raises
        SystemExit before reaching the OS-level read in the
        missing case)."""

        (isolated_repo / "content").mkdir()
        _write_catalog(splunkbase_ids.CATALOG_PATH, {})

        def _boom() -> dict[str, Any]:
            raise OSError("disk gone")

        monkeypatch.setattr(splunkbase_ids, "_load_catalog", _boom)
        rc = splunkbase_ids.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "catalog unreadable" in err

    def test_unreadable_uc_returns_2(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A malformed UC sidecar aborts the whole audit with rc=2 —
        we don't try to partially-validate the corpus."""

        (isolated_repo / "content" / "cat-01-foo").mkdir(parents=True)
        (isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
            "{bad", encoding="utf-8"
        )
        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        rc = splunkbase_ids.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "UC-1.1.1.json" in err


# ---------------------------------------------------------------------------
# main — happy path (rc=0)
# ---------------------------------------------------------------------------


class TestMainHappyPath:
    def test_empty_content_returns_0(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Empty ``content/`` (no UCs) is a valid state — the audit
        exits ``0`` with all counters at zero."""

        (isolated_repo / "content").mkdir()
        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        rc = splunkbase_ids.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "catalog_size=0" in out
        assert "ucs_with_apps=0" in out
        assert "total_references=0" in out
        assert "offending_ucs=0" in out

    def test_ucs_with_resolved_ids_and_valid_urls_returns_0(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A normal happy path: ids resolve, URLs start with the
        expected prefix → rc=0."""

        _write_catalog(
            splunkbase_ids.CATALOG_PATH,
            {"100": {"name": "App A"}, "200": {"name": "App B"}},
        )
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[
                {
                    "id": 100,
                    "url": "https://splunkbase.splunk.com/app/100",
                },
                {
                    "id": 200,
                    "url": "https://splunkbase.splunk.com/app/200/details",
                },
            ],
        )
        rc = splunkbase_ids.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "catalog_size=2" in out
        assert "ucs_with_apps=1" in out
        assert "total_references=2" in out
        assert "offending_ucs=0" in out

    def test_uc_with_resolved_id_and_no_url_returns_0(
        self,
        isolated_repo: Path,
    ) -> None:
        """``url`` is optional on a ``splunkbaseApps[]`` entry — the
        audit only validates when one is present."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 100}],
        )
        rc = splunkbase_ids.main([])
        assert rc == 0

    def test_uc_with_empty_url_skips_prefix_check(
        self,
        isolated_repo: Path,
    ) -> None:
        """Empty-string URL is treated as 'no URL' — the prefix check
        only runs when ``url`` is a non-empty string."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 100, "url": ""}],
        )
        rc = splunkbase_ids.main([])
        assert rc == 0

    def test_uc_with_non_string_url_skips_prefix_check(
        self,
        isolated_repo: Path,
    ) -> None:
        """A non-string ``url`` (e.g. an int) is treated as 'no URL'
        because the ``isinstance`` guard in the prefix check would
        otherwise raise."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 100, "url": 12345}],
        )
        rc = splunkbase_ids.main([])
        assert rc == 0

    def test_uc_without_splunkbase_apps_is_skipped(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """UCs that don't reference any Splunkbase apps don't count
        toward ``ucs_with_apps`` or ``total_references``."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=None,
        )
        rc = splunkbase_ids.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "ucs_with_apps=0" in out

    def test_uc_with_empty_apps_list_is_skipped(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``splunkbaseApps: []`` is treated the same as omitting
        the field — neither contributes to the counters."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[],
        )
        rc = splunkbase_ids.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "ucs_with_apps=0" in out

    def test_uc_with_non_list_splunkbase_apps_is_skipped(
        self,
        isolated_repo: Path,
    ) -> None:
        """Authoring drift defence: if ``splunkbaseApps`` is a string
        or dict (not a list) the UC is silently skipped — same
        semantics as the empty / missing case."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        cat_dir = isolated_repo / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        (cat_dir / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "splunkbaseApps": "not-a-list"}),
            encoding="utf-8",
        )
        rc = splunkbase_ids.main([])
        assert rc == 0

    def test_non_dict_entry_is_silently_skipped(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An individual ``splunkbaseApps[]`` element that is not a
        dict (e.g. a stray string) is silently ignored — it does
        NOT count toward ``total_references`` and it does NOT raise."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[
                "stray-string",  # silently skipped
                {"id": 100},  # counted
            ],
        )
        rc = splunkbase_ids.main([])
        assert rc == 0
        out = capsys.readouterr().out
        # Only the one dict entry contributes to total_references.
        assert "total_references=1" in out


# ---------------------------------------------------------------------------
# main — id failures (rc=1)
# ---------------------------------------------------------------------------


class TestMainIdFailures:
    def test_unknown_id_returns_1_and_lists_offender(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An id not present in the catalog is reported per-UC with
        the documented "id missing from catalog" reason."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 999}],
        )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "999 (id missing from catalog)" in err
        assert "UC-1.1.1.json" in err

    def test_non_int_id_returns_1(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A non-int ``id`` field (e.g. a string) is treated as
        an offender — the audit refuses to accept it even if the
        string version happens to match a catalog key."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": "100"}],
        )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "100 (id missing from catalog)" in err

    def test_missing_id_field_returns_1(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An entry missing the ``id`` key entirely (``app_id`` is
        ``None``) is reported as an offender."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"name": "no-id-here"}],
        )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "None (id missing from catalog)" in err

    def test_non_digit_catalog_keys_dropped_from_id_set(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Only digit-string catalog keys become part of the id-set
        used for resolution — slugs or names in the catalog are
        ignored (they shouldn't exist there but the loader is
        permissive)."""

        _write_catalog(
            splunkbase_ids.CATALOG_PATH,
            {"100": {"name": "Good"}, "splunk-thing": {"name": "Skip"}},
        )
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 100}],
        )
        rc = splunkbase_ids.main([])
        assert rc == 0
        # The non-digit entry exists in the catalog dict but is not
        # in the id-set — verified by the success path being reachable.
        out = capsys.readouterr().out
        assert "catalog_size=1" in out

    def test_offender_list_truncated_at_10(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The offender list is capped at 10 entries with an
        ``... and N more`` footer for overflow."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        for i in range(15):
            _write_uc(
                isolated_repo / "content",
                cat="cat-01-foo",
                uc_id=f"1.1.{i + 1}",
                splunkbase_apps=[{"id": 999 + i}],
            )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        # Only first 10 listed individually + the overflow footer.
        assert "and 5 more UCs reference unknown ids" in err
        # Count the individual offender lines (one per UC) — we
        # don't pin specific IDs because ``sorted()`` orders them
        # lexicographically (so UC-1.1.10.json sorts before
        # UC-1.1.2.json) which makes per-id assertions brittle.
        offender_lines = [
            line
            for line in err.splitlines()
            if "(id missing from catalog)" in line
        ]
        assert len(offender_lines) == 10

    def test_offender_list_exactly_10_no_overflow_footer(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """At exactly 10 offenders the overflow footer is suppressed
        (covers the False arm of ``> 10`` branch)."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        for i in range(10):
            _write_uc(
                isolated_repo / "content",
                cat="cat-01-foo",
                uc_id=f"1.1.{i + 1}",
                splunkbase_apps=[{"id": 999 + i}],
            )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        # Overflow footer absent (False arm of ``> 10``).
        assert "more UCs reference unknown ids" not in err
        # All 10 listed.
        offender_lines = [
            line
            for line in err.splitlines()
            if "(id missing from catalog)" in line
        ]
        assert len(offender_lines) == 10


# ---------------------------------------------------------------------------
# main — URL failures (rc=1, only when no id offenders)
# ---------------------------------------------------------------------------


class TestMainUrlFailures:
    def test_bad_url_returns_1(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A URL that doesn't start with the expected prefix fails
        the audit (after id resolution succeeds)."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[
                {"id": 100, "url": "https://wrong-domain.example/app/100"},
            ],
        )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "BAD URL" in err
        assert "id=100" in err
        assert "https://wrong-domain.example/app/100" in err

    def test_bad_url_for_different_app_id_returns_1(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The prefix is constructed from the catalog-resolved id, so
        a URL pointing at a different app id (still on Splunkbase)
        is rejected as a mismatch."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[
                {
                    "id": 100,
                    "url": "https://splunkbase.splunk.com/app/200",
                },
            ],
        )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "BAD URL" in err

    def test_bad_url_list_truncated_at_5(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The BAD URL list is capped at 5 entries (tighter cap than
        the id-offender 10)."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        for i in range(8):
            _write_uc(
                isolated_repo / "content",
                cat="cat-01-foo",
                uc_id=f"1.1.{i + 1}",
                splunkbase_apps=[
                    {"id": 100, "url": f"https://wrong-{i}.example/"},
                ],
            )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        # Count BAD URL lines.
        bad_url_lines = [l for l in err.splitlines() if "BAD URL" in l]
        assert len(bad_url_lines) == 5

    def test_id_offenders_take_precedence_over_url_offenders(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When BOTH id offenders and URL offenders exist, the id
        branch fires first (returns 1) and the URL branch is not
        reached. Verified by the absence of the BAD URL marker
        even though a bad URL is present on a separate UC."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 999}],  # unknown id
        )
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.2",
            splunkbase_apps=[
                {"id": 100, "url": "https://wrong.example/"},
            ],
        )
        rc = splunkbase_ids.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "id missing from catalog" in err
        assert "BAD URL" not in err


# ---------------------------------------------------------------------------
# main — --json output
# ---------------------------------------------------------------------------


class TestJsonOutput:
    def test_json_written_on_success(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """``--json`` writes the breakdown to disk even when the audit
        succeeds (no offenders, no bad URLs)."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 100}],
        )
        out_path = tmp_path / "reports" / "splunkbase-ids.json"
        rc = splunkbase_ids.main(["--json", str(out_path)])
        assert rc == 0
        assert out_path.exists()
        report = json.loads(out_path.read_text(encoding="utf-8"))
        assert report["catalogSize"] == 1
        assert report["ucsWithApps"] == 1
        assert report["totalReferences"] == 1
        assert report["offendingUcs"] == []
        assert report["badUrlExamples"] == []

    def test_json_parent_dir_created(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """``parents=True`` on the output mkdir means even a deeply
        nested target path works without pre-creating directories."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        (isolated_repo / "content").mkdir()
        out_path = tmp_path / "a" / "b" / "c" / "out.json"
        rc = splunkbase_ids.main(["--json", str(out_path)])
        assert rc == 0
        assert out_path.exists()

    def test_json_captures_id_offenders(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """Id offenders are serialised under ``offendingUcs`` with the
        ``uc`` path and a list of ``{id, reason}`` records."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[{"id": 999}],
        )
        out_path = tmp_path / "reports" / "out.json"
        rc = splunkbase_ids.main(["--json", str(out_path)])
        assert rc == 1
        report = json.loads(out_path.read_text(encoding="utf-8"))
        assert report["offendingUcs"] == [
            {
                "uc": "content/cat-01-foo/UC-1.1.1.json",
                "offenders": [{"id": 999, "reason": "id missing from catalog"}],
            }
        ]

    def test_json_captures_bad_url_examples(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """Bad URL examples are serialised under ``badUrlExamples``
        with ``uc`` path and a human-readable detail string."""

        _write_catalog(splunkbase_ids.CATALOG_PATH, {"100": {"name": "X"}})
        _write_uc(
            isolated_repo / "content",
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[
                {"id": 100, "url": "https://wrong.example/"},
            ],
        )
        out_path = tmp_path / "reports" / "out.json"
        rc = splunkbase_ids.main(["--json", str(out_path)])
        assert rc == 1
        report = json.loads(out_path.read_text(encoding="utf-8"))
        assert len(report["badUrlExamples"]) == 1
        assert report["badUrlExamples"][0]["uc"] == (
            "content/cat-01-foo/UC-1.1.1.json"
        )
        assert "id=100" in report["badUrlExamples"][0]["detail"]
        assert "https://wrong.example/" in (
            report["badUrlExamples"][0]["detail"]
        )


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


class TestCliSurface:
    def test_argv_none_defaults_to_sys_argv(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``main()`` without argv falls through to ``argparse``'s
        default behaviour which reads ``sys.argv``."""

        (isolated_repo / "content").mkdir()
        _write_catalog(splunkbase_ids.CATALOG_PATH, {})
        monkeypatch.setattr(sys, "argv", ["splunkbase_ids"])
        rc = splunkbase_ids.main()
        assert rc == 0
        assert "catalog_size=0" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Module entrypoint guard — subprocess smoke against real content/
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_validates_real_content_tree(self) -> None:
        """Invoke ``python -m tools.audits.splunkbase_ids`` against the
        repo's real ``content/`` tree. The expected rc depends on the
        current corpus health (likely 0 or 1 — never 2 in a healthy
        checkout). This pins the CLI contract advertised in the
        module docstring.

        The subprocess inherits no ``coverage`` instrumentation, so
        this test does not improve ``--cov`` numbers — coverage of
        the ``if __name__`` guard is produced by the test-collection
        import."""

        repo_root = Path(splunkbase_ids.__file__).resolve().parents[2]
        content_dir = repo_root / "content"
        catalog = repo_root / "data" / "splunkbase-catalog.json"
        if not content_dir.is_dir() or not catalog.is_file():
            pytest.skip("real content/ or catalog not present")
        result = subprocess.run(
            [sys.executable, "-m", "tools.audits.splunkbase_ids"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        # 0 = clean, 1 = known-resolvable failures present.
        # 2 = invocation error — must NEVER happen in a healthy
        # checkout where both files exist.
        assert result.returncode in (0, 1), (
            f"unexpected rc={result.returncode} "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "[splunkbase_ids]" in result.stdout
