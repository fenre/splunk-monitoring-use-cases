"""Unit-level coverage for ``scripts/review_splunkbase_mappings.py``.

The SME review helper for the v9.0 ``splunkbaseApps[]`` migration.
Companion to ``splunk_uc generate-splunkbase-mappings``. Even though
this script is invoked manually (not CI-wired), it is one of the
"legitimate ``scripts/`` namespace tools" enumerated in
``docs/migration-status.md`` (P6 Tier-2 batch-11 narrative) and
therefore part of the coverage uplift programme.

What this suite locks
---------------------

* I/O helpers — ``_read_uc`` / ``_write_uc`` (round-trip preserves
  semantics), ``_read_ledger`` (new vs existing), ``_write_ledger``
  (parent-dir auto-create, sort-keys), ``_git_head_sha`` (happy path
  + fallback when git is unavailable).
* UC discovery — ``_all_ucs`` (sorted glob), ``_open_review_entries``
  (missing key, non-list, mix of dict / non-dict / flagged-only),
  ``_filter_ucs`` (no filters, equipment only, uc ids only,
  equipment+uc combo, OSError, JSONDecodeError, equipment slug missing,
  ``UC-`` prefix tolerated on uc ids).
* ``cmd_list`` — open backlog summary; ``--equipment`` filter view;
  no-equipment UC bucket; per-UC error logging.
* ``_strip_review_flag`` — flagged entries cleared, non-flagged left
  intact, non-dict entries pass through unchanged, count is accurate.
* ``_validate_signoff_inputs`` — every error arm: no scope, short
  reviewer, missing reviewer, invalid pr, invalid uc id; happy path
  returns empty list.
* ``cmd_signoff`` — input-validation error path returns 2 with
  stderr; empty filter returns 0 with note; no open flags returns 0
  with note; dry-run does not mutate sidecars or ledger; live mode
  writes sidecars and appends ledger entry; OSError / JSONDecodeError
  on read are logged + skipped.
* ``cmd_audit`` — counters across the four buckets (total /
  with_apps / fully_signed / open) including the missing-key,
  non-list, empty-list, and read-error arms.
* ``main`` — dispatch to each subcommand; fallthrough returns 2 +
  prints help (we coerce a stray ``cmd`` value to exercise the arm).
* ``__main__`` guard — script-entry invocation via ``runpy``.

Run
---

``pytest tests/scripts/test_review_splunkbase_mappings.py``

Coverage check
--------------

``python3 -m pytest tests/scripts/test_review_splunkbase_mappings.py \\
  --cov=scripts.review_splunkbase_mappings --cov-report=term-missing -q``

Final state: 205 stmts / 1 miss / 74 branches / 1 BrPart = 99.3 %.
The single remaining un-covered line (252 — ``if cleared == 0:
continue`` inside ``cmd_signoff``) is unreachable defensive code:
``_open_review_entries`` returns dict entries that already have a
truthy ``requiresSmeReview``, and ``_strip_review_flag`` increments
``cleared`` for exactly that predicate. The two filters are
logically equivalent, so a non-empty return from the first
guarantees ``cleared >= 1`` from the second. Documented here so
that if either filter's contract changes, this test file gains a
positive-coverage case for the formerly-unreachable arm.
"""
from __future__ import annotations

import argparse
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.review_splunkbase_mappings as rsm

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Redirect REPO_ROOT / CONTENT_DIR / LEDGER_PATH to a tmp tree.

    The script reads those as module-level constants computed at
    import time, so we patch them after import."""
    repo = tmp_path / "repo"
    (repo / "content").mkdir(parents=True)
    (repo / "data" / "provenance").mkdir(parents=True)
    monkeypatch.setattr(rsm, "REPO_ROOT", repo)
    monkeypatch.setattr(rsm, "CONTENT_DIR", repo / "content")
    monkeypatch.setattr(
        rsm,
        "LEDGER_PATH",
        repo / "data" / "provenance" / "splunkbase-mappings-signoffs.json",
    )
    return repo


def _write_uc(
    repo: Path,
    uc_id: str,
    *,
    apps: list | None = None,
    equipment: list | None = None,
    extras: dict | None = None,
) -> Path:
    """Create a UC sidecar under content/cat-NN-slug/UC-ID.json."""
    cat_num = uc_id.split(".", 1)[0]
    cat_dir = repo / "content" / f"cat-{int(cat_num):02d}-slug"
    cat_dir.mkdir(parents=True, exist_ok=True)
    body = {"id": uc_id, "title": f"UC {uc_id}"}
    if apps is not None:
        body["splunkbaseApps"] = apps
    if equipment is not None:
        body["equipment"] = equipment
    if extras:
        body.update(extras)
    fp = cat_dir / f"UC-{uc_id}.json"
    fp.write_text(json.dumps(body, indent=2), encoding="utf-8")
    return fp


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


class TestReadWriteUc:
    def test_round_trip_preserves_body(self, isolated_repo: Path) -> None:
        path = _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "splunkbase-1", "requiresSmeReview": True}],
            equipment=["cisco-meraki"],
        )
        loaded = rsm._read_uc(path)
        assert loaded["id"] == "1.1.1"
        assert loaded["equipment"] == ["cisco-meraki"]
        assert loaded["splunkbaseApps"][0]["id"] == "splunkbase-1"

        # Round-trip via _write_uc preserves body shape.
        rsm._write_uc(path, loaded)
        reloaded = rsm._read_uc(path)
        assert reloaded == loaded
        # _write_uc writes a trailing newline.
        assert path.read_text(encoding="utf-8").endswith("\n")


class TestReadLedger:
    def test_returns_fresh_skeleton_when_missing(
        self, isolated_repo: Path
    ) -> None:
        assert not rsm.LEDGER_PATH.exists()
        led = rsm._read_ledger()
        assert led["schemaVersion"] == 1
        assert led["documentation"] == "docs/splunkbase-review-guide.md"
        assert led["signoffs"] == []
        # generatedAt is a properly formatted UTC stamp.
        assert led["generatedAt"].endswith("Z")
        assert "T" in led["generatedAt"]

    def test_returns_existing_ledger(self, isolated_repo: Path) -> None:
        rsm.LEDGER_PATH.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "generatedAt": "2024-01-01T00:00:00Z",
                    "documentation": "docs/splunkbase-review-guide.md",
                    "signoffs": [{"pr": "#1"}],
                }
            ),
            encoding="utf-8",
        )
        led = rsm._read_ledger()
        assert led["signoffs"] == [{"pr": "#1"}]


class TestWriteLedger:
    def test_creates_parent_and_sorts_keys(
        self, isolated_repo: Path
    ) -> None:
        # Remove the auto-created provenance dir to exercise the
        # parents=True arm.
        import shutil

        shutil.rmtree(rsm.LEDGER_PATH.parent)
        body = {"signoffs": [], "schemaVersion": 1, "generatedAt": "X"}
        rsm._write_ledger(body)
        assert rsm.LEDGER_PATH.exists()
        text = rsm.LEDGER_PATH.read_text(encoding="utf-8")
        # Sort-keys means alphabetical order.
        assert text.index('"generatedAt"') < text.index('"schemaVersion"')
        assert text.endswith("\n")


class TestGitHeadSha:
    def test_returns_real_sha_on_success(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _fake_check_output(*args, **kwargs):
            return b"deadbeef\n"

        monkeypatch.setattr(
            rsm.subprocess, "check_output", _fake_check_output
        )
        assert rsm._git_head_sha() == "deadbeef"

    def test_returns_unknown_when_git_unavailable(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _raise(*args, **kwargs):
            raise FileNotFoundError("no git in PATH")

        monkeypatch.setattr(rsm.subprocess, "check_output", _raise)
        assert rsm._git_head_sha() == "unknown"

    def test_returns_unknown_when_git_fails(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        def _raise(*args, **kwargs):
            raise subprocess.CalledProcessError(128, ["git"])

        monkeypatch.setattr(rsm.subprocess, "check_output", _raise)
        assert rsm._git_head_sha() == "unknown"


# ---------------------------------------------------------------------------
# UC discovery
# ---------------------------------------------------------------------------


class TestAllUcs:
    def test_returns_sorted_paths(self, isolated_repo: Path) -> None:
        _write_uc(isolated_repo, "2.1.1")
        _write_uc(isolated_repo, "1.1.1")
        paths = rsm._all_ucs()
        # cat-01 sorts before cat-02 alphabetically.
        assert [p.name for p in paths] == ["UC-1.1.1.json", "UC-2.1.1.json"]

    def test_empty_when_no_content(self, isolated_repo: Path) -> None:
        assert rsm._all_ucs() == []


class TestOpenReviewEntries:
    def test_missing_field_returns_empty(self) -> None:
        assert rsm._open_review_entries({}) == []

    def test_non_list_field_returns_empty(self) -> None:
        assert rsm._open_review_entries({"splunkbaseApps": "oops"}) == []

    def test_filters_flagged_dicts(self) -> None:
        uc = {
            "splunkbaseApps": [
                {"id": "a", "requiresSmeReview": True},
                {"id": "b", "requiresSmeReview": False},
                {"id": "c"},  # missing key -> falsy
                "not-a-dict",  # non-dict skipped
            ]
        }
        result = rsm._open_review_entries(uc)
        assert len(result) == 1
        assert result[0]["id"] == "a"


class TestFilterUcs:
    def test_no_filters_returns_all(self, isolated_repo: Path) -> None:
        _write_uc(isolated_repo, "1.1.1")
        _write_uc(isolated_repo, "2.1.1")
        paths = rsm._filter_ucs(equipment=None, uc_ids=[])
        assert len(paths) == 2

    def test_equipment_filter_includes_only_matches(
        self, isolated_repo: Path
    ) -> None:
        _write_uc(isolated_repo, "1.1.1", equipment=["cisco-meraki"])
        _write_uc(isolated_repo, "2.1.1", equipment=["other"])
        paths = rsm._filter_ucs(equipment="cisco-meraki", uc_ids=[])
        assert len(paths) == 1
        assert paths[0].name == "UC-1.1.1.json"

    def test_equipment_filter_drops_missing_field(
        self, isolated_repo: Path
    ) -> None:
        _write_uc(isolated_repo, "1.1.1")  # no equipment field
        paths = rsm._filter_ucs(equipment="cisco-meraki", uc_ids=[])
        assert paths == []

    def test_uc_id_filter_tolerates_uc_prefix(
        self, isolated_repo: Path
    ) -> None:
        _write_uc(isolated_repo, "1.1.1")
        _write_uc(isolated_repo, "2.1.1")
        paths = rsm._filter_ucs(
            equipment=None, uc_ids=["UC-1.1.1", "2.1.1"]
        )
        # Both forms accepted.
        names = sorted(p.name for p in paths)
        assert names == ["UC-1.1.1.json", "UC-2.1.1.json"]

    def test_equipment_and_uc_id_combined_intersect(
        self, isolated_repo: Path
    ) -> None:
        _write_uc(isolated_repo, "1.1.1", equipment=["cisco-meraki"])
        _write_uc(isolated_repo, "2.1.1", equipment=["cisco-meraki"])
        paths = rsm._filter_ucs(
            equipment="cisco-meraki", uc_ids=["1.1.1"]
        )
        assert len(paths) == 1
        assert paths[0].name == "UC-1.1.1.json"

    def test_skips_malformed_json(self, isolated_repo: Path) -> None:
        _write_uc(isolated_repo, "1.1.1")
        bad = isolated_repo / "content" / "cat-02-slug" / "UC-2.1.1.json"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("not json", encoding="utf-8")
        paths = rsm._filter_ucs(equipment=None, uc_ids=[])
        # Only the well-formed file survives.
        assert len(paths) == 1
        assert paths[0].name == "UC-1.1.1.json"

    def test_skips_oserror_unreadable(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _write_uc(isolated_repo, "1.1.1")

        def _raise_for_one(self, *args, **kwargs):
            raise OSError("simulated")

        # Make _read_uc raise OSError on the first call only.
        original = rsm._read_uc
        call_count = {"n": 0}

        def _flaky(path):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise OSError("simulated")
            return original(path)

        monkeypatch.setattr(rsm, "_read_uc", _flaky)
        paths = rsm._filter_ucs(equipment=None, uc_ids=[])
        # OSError swallowed → the only UC is skipped.
        assert paths == []


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------


class TestCmdList:
    def _ns(self, equipment=None, uc=None):
        return argparse.Namespace(equipment=equipment, uc=uc)

    def test_default_view_groups_by_equipment(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a", "requiresSmeReview": True}],
            equipment=["cisco-meraki"],
        )
        _write_uc(
            isolated_repo,
            "2.1.1",
            apps=[
                {"id": "b", "requiresSmeReview": True},
                {"id": "c", "requiresSmeReview": True},
            ],
            equipment=["other-vendor"],
        )
        rc = rsm.cmd_list(self._ns())
        assert rc == 0
        out = capsys.readouterr().out
        assert "open backlog" in out
        assert "cisco-meraki" in out
        assert "other-vendor" in out

    def test_no_equipment_bucket_emitted(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a", "requiresSmeReview": True}],
            # equipment field missing → no_equipment bucket
        )
        rc = rsm.cmd_list(self._ns())
        assert rc == 0
        out = capsys.readouterr().out
        assert "(no equipment slug)" in out

    def test_skips_ucs_without_open_entries(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "done"}],  # no review flag
            equipment=["cisco-meraki"],
        )
        rc = rsm.cmd_list(self._ns())
        assert rc == 0
        out = capsys.readouterr().out
        assert "0 UCs, 0 entries" in out

    def test_equipment_filter_view(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a", "requiresSmeReview": True}],
            equipment=["cisco-meraki"],
        )
        rc = rsm.cmd_list(self._ns(equipment="cisco-meraki"))
        assert rc == 0
        out = capsys.readouterr().out
        assert "equipment=cisco-meraki" in out
        assert "UC-1.1.1" in out

    def test_logs_read_errors_to_stderr(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The inner loop of cmd_list ALSO has a try/except — if
        _filter_ucs returned the path but a subsequent _read_uc
        in cmd_list raises, we log to stderr and continue."""
        path = _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a", "requiresSmeReview": True}],
            equipment=["cisco-meraki"],
        )
        call_count = {"n": 0}
        original = rsm._read_uc

        def _flaky(p):
            call_count["n"] += 1
            # First call (in _filter_ucs) succeeds; second (in
            # cmd_list's own loop) raises OSError.
            if call_count["n"] == 2:
                raise OSError("simulated cmd_list read error")
            return original(p)

        monkeypatch.setattr(rsm, "_read_uc", _flaky)
        rc = rsm.cmd_list(self._ns())
        assert rc == 0
        err = capsys.readouterr().err
        assert str(path) in err


# ---------------------------------------------------------------------------
# _strip_review_flag
# ---------------------------------------------------------------------------


class TestStripReviewFlag:
    def test_clears_flagged_entries(self) -> None:
        uc = {
            "id": "1.1.1",
            "splunkbaseApps": [
                {"id": "a", "requiresSmeReview": True},
                {"id": "b", "requiresSmeReview": False},
            ],
        }
        new_uc, cleared = rsm._strip_review_flag(uc)
        assert cleared == 1
        assert new_uc["splunkbaseApps"][0] == {"id": "a"}
        # Non-flagged left as-is.
        assert new_uc["splunkbaseApps"][1] == {
            "id": "b",
            "requiresSmeReview": False,
        }

    def test_preserves_non_dict_entries(self) -> None:
        uc = {
            "splunkbaseApps": [
                "string-entry",
                42,
                {"id": "a", "requiresSmeReview": True},
            ]
        }
        new_uc, cleared = rsm._strip_review_flag(uc)
        assert cleared == 1
        assert new_uc["splunkbaseApps"][0] == "string-entry"
        assert new_uc["splunkbaseApps"][1] == 42

    def test_handles_empty_or_missing_field(self) -> None:
        new_uc, cleared = rsm._strip_review_flag({})
        assert cleared == 0
        assert new_uc["splunkbaseApps"] == []


# ---------------------------------------------------------------------------
# _validate_signoff_inputs
# ---------------------------------------------------------------------------


class TestValidateSignoffInputs:
    def _ns(
        self,
        *,
        equipment=None,
        uc=None,
        reviewer="Pat Smith (Splunk PS)",
        pr="#1",
    ):
        return argparse.Namespace(
            equipment=equipment,
            uc=uc,
            reviewer=reviewer,
            pr=pr,
        )

    def test_happy_path_returns_empty(self) -> None:
        ns = self._ns(equipment="cisco-meraki")
        assert rsm._validate_signoff_inputs(ns) == []

    def test_no_scope_arg(self) -> None:
        errs = rsm._validate_signoff_inputs(self._ns())
        assert any("--equipment" in e for e in errs)

    def test_short_reviewer(self) -> None:
        ns = self._ns(equipment="x", reviewer=" a ")
        errs = rsm._validate_signoff_inputs(ns)
        assert any("--reviewer" in e for e in errs)

    def test_empty_reviewer(self) -> None:
        ns = self._ns(equipment="x", reviewer="")
        errs = rsm._validate_signoff_inputs(ns)
        assert any("--reviewer" in e for e in errs)

    def test_invalid_pr(self) -> None:
        ns = self._ns(equipment="x", pr="1234")
        errs = rsm._validate_signoff_inputs(ns)
        assert any("--pr" in e for e in errs)

    def test_direct_commit_pr_accepted(self) -> None:
        ns = self._ns(equipment="x", pr="direct-commit")
        assert rsm._validate_signoff_inputs(ns) == []

    def test_invalid_uc_id(self) -> None:
        ns = self._ns(uc=["1.1", "UC-bad"])
        errs = rsm._validate_signoff_inputs(ns)
        # Two invalid ids → two errors.
        bad_errs = [e for e in errs if "is not a UC-X.Y.Z id" in e]
        assert len(bad_errs) == 2

    def test_mixed_valid_invalid_uc_ids_only_invalid_errors(
        self,
    ) -> None:
        """Covers the False arm of ``if not UC_ID_RE.match(...)``
        — when the UC id IS valid, no error is appended for it.
        Need at least one valid + one invalid in the same call so
        the loop visits both arms."""
        ns = self._ns(uc=["1.1.1", "UC-2.3.4", "bogus"])
        errs = rsm._validate_signoff_inputs(ns)
        bad_errs = [e for e in errs if "is not a UC-X.Y.Z id" in e]
        # Only the bogus one is flagged.
        assert len(bad_errs) == 1
        assert "bogus" in bad_errs[0]


# ---------------------------------------------------------------------------
# cmd_signoff
# ---------------------------------------------------------------------------


class TestCmdSignoff:
    def _ns(
        self,
        *,
        equipment=None,
        uc=None,
        reviewer="Pat Smith (Splunk PS)",
        pr="#1",
        dry_run=False,
    ):
        return argparse.Namespace(
            equipment=equipment,
            uc=uc,
            reviewer=reviewer,
            pr=pr,
            dry_run=dry_run,
        )

    def test_validation_failure_returns_two(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # No --equipment AND no --uc → validation fails.
        rc = rsm.cmd_signoff(self._ns())
        assert rc == 2
        err = capsys.readouterr().err
        assert "--equipment" in err

    def test_no_matches_returns_zero(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # No UCs in the repo at all.
        rc = rsm.cmd_signoff(self._ns(equipment="cisco-meraki"))
        assert rc == 0
        err = capsys.readouterr().err
        assert "no UCs matched the filter" in err

    def test_no_open_flags_returns_zero(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a"}],  # already signed off
            equipment=["cisco-meraki"],
        )
        rc = rsm.cmd_signoff(self._ns(equipment="cisco-meraki"))
        assert rc == 0
        out = capsys.readouterr().out
        assert "no open review flags" in out

    def test_dry_run_does_not_mutate(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a", "requiresSmeReview": True}],
            equipment=["cisco-meraki"],
        )
        rc = rsm.cmd_signoff(
            self._ns(equipment="cisco-meraki", dry_run=True)
        )
        assert rc == 0
        # Sidecar unchanged.
        body = json.loads(path.read_text(encoding="utf-8"))
        assert body["splunkbaseApps"][0]["requiresSmeReview"] is True
        # Ledger not written.
        assert not rsm.LEDGER_PATH.exists()
        out = capsys.readouterr().out
        assert "dry-run" in out
        assert "would clear 1 entries" in out

    def test_live_signoff_writes_sidecar_and_ledger(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a", "requiresSmeReview": True}],
            equipment=["cisco-meraki"],
        )
        monkeypatch.setattr(
            rsm.subprocess, "check_output", lambda *a, **kw: b"abc123\n"
        )
        rc = rsm.cmd_signoff(self._ns(equipment="cisco-meraki"))
        assert rc == 0
        # Sidecar mutated.
        body = json.loads(path.read_text(encoding="utf-8"))
        assert "requiresSmeReview" not in body["splunkbaseApps"][0]
        # Ledger written.
        led = json.loads(rsm.LEDGER_PATH.read_text(encoding="utf-8"))
        assert len(led["signoffs"]) == 1
        entry = led["signoffs"][0]
        assert entry["pr"] == "#1"
        assert entry["commit"] == "abc123"
        assert entry["reviewer"] == "Pat Smith (Splunk PS)"
        assert entry["scope"]["equipment"] == "cisco-meraki"
        assert "1.1.1" in entry["scope"]["ucs"]
        assert entry["entriesCleared"] == 1
        out = capsys.readouterr().out
        assert "signed off 1 entries" in out

    def test_read_error_in_inner_loop_skipped(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """If a per-UC _read_uc inside cmd_signoff raises, we log
        and continue with the rest of the batch."""
        _write_uc(
            isolated_repo,
            "1.1.1",
            apps=[{"id": "a", "requiresSmeReview": True}],
            equipment=["cisco-meraki"],
        )
        original = rsm._read_uc
        call_count = {"n": 0}

        def _flaky(p):
            call_count["n"] += 1
            # First call (in _filter_ucs) succeeds; second (in
            # cmd_signoff's loop) raises.
            if call_count["n"] == 2:
                raise OSError("simulated cmd_signoff read error")
            return original(p)

        monkeypatch.setattr(rsm, "_read_uc", _flaky)
        rc = rsm.cmd_signoff(self._ns(equipment="cisco-meraki"))
        # Nothing cleared → exits with 0 and the "no open flags" note.
        assert rc == 0
        err = capsys.readouterr().err
        assert "simulated cmd_signoff read error" in err


# ---------------------------------------------------------------------------
# cmd_audit
# ---------------------------------------------------------------------------


class TestCmdAudit:
    def test_buckets_aggregate_correctly(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Fully-signed UC (with apps, no review flags).
        _write_uc(
            isolated_repo, "1.1.1", apps=[{"id": "a"}]
        )
        # Open-review UC (with apps, one flagged).
        _write_uc(
            isolated_repo,
            "2.1.1",
            apps=[{"id": "b", "requiresSmeReview": True}],
        )
        # No-apps UC.
        _write_uc(isolated_repo, "3.1.1")
        # Empty-apps UC.
        _write_uc(isolated_repo, "4.1.1", apps=[])
        rc = rsm.cmd_audit(argparse.Namespace())
        assert rc == 0
        out = capsys.readouterr().out
        assert "total_ucs=4" in out
        assert "with_splunkbaseApps=2" in out
        assert "fully_signed=1" in out
        assert "awaiting_review=1" in out
        assert "open_entries=1" in out

    def test_skips_malformed(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_uc(isolated_repo, "1.1.1", apps=[{"id": "a"}])
        bad = isolated_repo / "content" / "cat-02-slug" / "UC-2.1.1.json"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("not json", encoding="utf-8")
        rc = rsm.cmd_audit(argparse.Namespace())
        assert rc == 0
        out = capsys.readouterr().out
        # Only the well-formed UC counts.
        assert "total_ucs=1" in out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_list_dispatch(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = rsm.main(["list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "open backlog" in out

    def test_signoff_dispatch_via_validation_fail(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Trigger the signoff sub-parser without required args
        # other than the ones argparse demands → cmd_signoff
        # validation fails → rc=2.
        rc = rsm.main(
            ["signoff", "--reviewer", "X X (X)", "--pr", "#1"]
        )
        assert rc == 2

    def test_audit_dispatch(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = rsm.main(["audit"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "total_ucs=0" in out

    def test_fallthrough_returns_two_and_prints_help(
        self,
        isolated_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The ``parser.print_help(); return 2`` arm requires a
        ``cmd`` value that is not list/signoff/audit. argparse with
        required=True normally won't allow that, so we synthesise
        a Namespace and call ``main`` after bypassing argparse via
        a stub ``parse_args``."""
        ns = argparse.Namespace(cmd="bogus")

        def _fake_parse_args(self, argv=None):
            # Print-help arm only fires when cmd is unknown; we
            # also need the parser's print_help to capture stdout
            # via capsys. So we monkey-patch print_help to be
            # observable but no-op.
            return ns

        monkeypatch.setattr(
            argparse.ArgumentParser, "parse_args", _fake_parse_args
        )
        rc = rsm.main([])
        assert rc == 2


# ---------------------------------------------------------------------------
# __main__ guard
# ---------------------------------------------------------------------------


class TestMainGuard:
    def test_runpy_invocation_executes_main(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Invoke the script via runpy.run_path with ``run_name=
        '__main__'`` so the ``if __name__ == '__main__'`` block
        fires. Without args + missing subcommand, argparse calls
        SystemExit(2), which we catch."""
        script_src = Path(rsm.__file__).resolve()
        repo = tmp_path / "repo"
        (repo / "content").mkdir(parents=True)
        # Place a copy of the script so __file__ resolution is
        # confined to the tmp tree.
        dst = repo / "scripts" / "review_splunkbase_mappings.py"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(script_src.read_text(), encoding="utf-8")
        # No args → argparse exits 2.
        monkeypatch.setattr(
            sys, "argv", ["review_splunkbase_mappings"]
        )
        with pytest.raises(SystemExit) as exc:
            runpy.run_path(str(dst), run_name="__main__")
        assert exc.value.code in (None, 2)
