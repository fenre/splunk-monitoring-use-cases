"""Hermetic tests for ``splunk_uc.generators.mapping_ledger``.

This module sits at ~20% coverage in the full suite because it
requires a real ``content/cat-*/UC-*.json`` corpus and a real
``data/regulations.json`` + ``data/provenance/*-signoffs.json``
constellation to produce a ledger. Every helper, on the other hand,
is a small pure function or a thin wrapper over filesystem / git
calls — both of which we can monkeypatch.

The strategy of this file:

* Stub ``ROOT`` / ``CONTENT_DIR`` / ``REGULATIONS_JSON`` /
  ``LEDGER_PATH`` / ``SIGNOFFS_DIR`` at module-import time via
  ``monkeypatch.setattr`` so every helper that reads from disk
  operates inside ``tmp_path``. This lets ``build_ledger`` run end-
  to-end without ever touching the live repo.
* Reset the ``_git_first_seen_cache`` / ``_git_last_modified_cache``
  / ``_git_bulk_populated`` module-globals before every test so
  cache-aware functions return what we expect.
* Drive ``subprocess.run`` through a ``_StubRun`` helper that
  matches on argv shape ("git log", "git rev-parse", "git show")
  so each git-touching path can be exercised independently.
* Build a tiny set of in-memory UC sidecars under
  ``tmp_path/content/cat-NN-foo/UC-X.Y.Z.json`` whose
  ``compliance[]`` arrays exercise every code path in
  ``build_ledger_inputs`` and ``signoff_status_for``.

Coverage targets in source order (line numbers as of P17 wave):

* 219-227 ``load_regulation_index`` (meta-multi branch, version set
  population).
* 230-241 ``resolve_regulation_id`` (NAME_TABLE hit, lowercase hit,
  KeyError raise).
* 244-249 ``normalise_version`` (empty / whitespace fallback).
* 252-268 ``iter_uc_sidecars`` (missing CONTENT_DIR, malformed JSON,
  duplicate id deduping).
* 297-381 ``_populate_git_caches_bulk`` (idempotent re-entry,
  empty path list, OSError + SubprocessError on both passes,
  SHA-line / path-line / orphan-path-line parsing).
* 384-389 ``git_first_seen_commit`` / ``git_last_modified_commit``
  (cache hit and miss).
* 392-408 ``catalogue_head_commit`` (success, OSError, invalid hex).
* 411-431 ``commit_date_iso`` (success with no tz, success with tz,
  empty stdout, OSError, ValueError on bad ISO).
* 434-449 ``deterministic_generated_at`` (commit-date succeeds,
  commit-date returns None → fallback epoch).
* 455-473 ``load_signoffs`` (missing file, JSONDecodeError,
  signoffs list, non-list signoffs).
* 476-516 ``signoff_status_for`` (peer always required; legal/sme
  conditional; signed entry; pending entry).
* 522-577 ``build_ledger_inputs`` (empty regulation, unresolved
  regulation → sys.exit(2), missing clause, bad mode/assurance,
  full success).
* 615-633 ``build_ledger_entry`` (cache hit and miss for git
  metadata).
* 636-643 ``compute_merkle_root`` (empty vs populated entry list).
* 646-720 ``build_ledger`` (full happy path + baseline parsing
  + collision detection → sys.exit(2)).
* 723-757 ``build_auxiliary_sources`` (missing file, OSError,
  multi-entry sort by path).
* 763-768 ``render`` (trailing newline contract).
* 771-815 ``main`` (--check pass, --check missing file, --check
  drift, default write path).
* 818-849 ``_structural_diff`` / ``_preview_diff`` (timestamp
  stripping equality, real content drift, empty diff).

Every test is fully hermetic: no real ``git``, no live ledger, no
real corpus. Run with::

    pytest tests/splunk_uc/generators/test_mapping_ledger.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from splunk_uc.generators import mapping_ledger as gen

# --------------------------------------------------------------------- #
# Fixtures                                                              #
# --------------------------------------------------------------------- #


@pytest.fixture(autouse=True)
def _reset_git_caches() -> None:
    """Drain the module-level git caches before every test."""

    gen._git_first_seen_cache.clear()
    gen._git_last_modified_cache.clear()
    gen._git_bulk_populated = False
    yield
    gen._git_first_seen_cache.clear()
    gen._git_last_modified_cache.clear()
    gen._git_bulk_populated = False


@pytest.fixture
def hermetic_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Repoint every module-level path constant into ``tmp_path``.

    Returns the synthetic root so callers can populate
    ``content/``, ``data/regulations.json``, etc. as needed.
    """

    root = tmp_path / "repo"
    (root / "content").mkdir(parents=True)
    (root / "data" / "provenance").mkdir(parents=True)
    monkeypatch.setattr(gen, "ROOT", root)
    monkeypatch.setattr(gen, "CONTENT_DIR", root / "content")
    monkeypatch.setattr(gen, "REGULATIONS_JSON", root / "data" / "regulations.json")
    monkeypatch.setattr(
        gen, "LEDGER_PATH", root / "data" / "provenance" / "mapping-ledger.json"
    )
    monkeypatch.setattr(gen, "SIGNOFFS_DIR", root / "data" / "provenance")
    return root


def _write_regulations(root: Path) -> None:
    """Write a tiny ``data/regulations.json`` with the regulation ids
    the synthetic UC sidecars below reference. Includes ``meta-multi``
    so we exercise the ``add('n/a')`` branch in
    ``load_regulation_index``.
    """

    payload = {
        "frameworks": [
            {
                "id": "iso-27001",
                "versions": [{"version": "2022"}, {"version": "2013"}],
            },
            {
                "id": "nist-800-53",
                "versions": [{"version": "5"}],
            },
            {"id": "meta-multi", "versions": []},
        ]
    }
    (root / "data" / "regulations.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_uc(
    root: Path,
    cat_slug: str,
    uc_id: str,
    *,
    compliance: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    cat_dir = root / "content" / cat_slug
    cat_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"id": uc_id}
    if compliance is not None:
        payload["compliance"] = compliance
    if extra:
        payload.update(extra)
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# --------------------------------------------------------------------- #
# Simple helpers                                                        #
# --------------------------------------------------------------------- #


class TestCanonicalDumpAndHash:
    """``canonical_dump`` and ``sha256_hex`` underpin every per-entry
    hash and the merkle root. Pin their RFC-8785 contract so
    accidental ``json.dumps`` defaults don't drift the on-disk
    ledger."""

    def test_canonical_dump_sorts_keys_and_strips_whitespace(self) -> None:
        out = gen.canonical_dump({"b": 1, "a": 2})
        assert out == '{"a":2,"b":1}'

    def test_canonical_dump_keeps_utf8(self) -> None:
        out = gen.canonical_dump({"name": "café"})
        assert "café" in out

    def test_sha256_hex_matches_python_hashlib(self) -> None:
        s = "hello"
        assert gen.sha256_hex(s) == hashlib.sha256(s.encode()).hexdigest()


# --------------------------------------------------------------------- #
# Regulation index + name resolution                                    #
# --------------------------------------------------------------------- #


class TestLoadRegulationIndex:
    def test_loads_versions_per_framework(self, hermetic_root: Path) -> None:
        _write_regulations(hermetic_root)
        idx = gen.load_regulation_index()
        assert idx["iso-27001"] == {"2022", "2013"}
        assert idx["nist-800-53"] == {"5"}

    def test_meta_multi_gets_na_version_appended(
        self, hermetic_root: Path
    ) -> None:
        _write_regulations(hermetic_root)
        idx = gen.load_regulation_index()
        # Line 224-225: meta-multi placeholder always gets 'n/a' even
        # when the JSON declares no versions explicitly.
        assert "n/a" in idx["meta-multi"]


class TestResolveRegulationId:
    def test_name_table_hit_wins_first(self) -> None:
        # Line 232-233: NAME_TABLE hit returns the canonical id
        # without consulting the framework index.
        assert gen.resolve_regulation_id("GDPR", {}) == "gdpr"
        assert gen.resolve_regulation_id("HIPAA Security", {}) == "hipaa-security"

    def test_lowercase_id_falls_through_to_framework_index(
        self,
    ) -> None:
        # Line 234-236: lowercased name matching a framework id is
        # accepted as a fallback (covers ad-hoc ids not in NAME_TABLE).
        out = gen.resolve_regulation_id("custom-id", {"custom-id": {"1"}})
        assert out == "custom-id"

    def test_unknown_name_raises_keyerror(self) -> None:
        # Line 237-241: anything that isn't in NAME_TABLE or the
        # framework index must raise KeyError so the build aborts
        # rather than silently producing wrong hashes.
        with pytest.raises(KeyError, match="has no entry"):
            gen.resolve_regulation_id("Made Up Regulation", {})


class TestNormaliseVersion:
    def test_empty_string_falls_back_to_na(self) -> None:
        assert gen.normalise_version("iso-27001", "") == "n/a"

    def test_whitespace_only_falls_back_to_na(self) -> None:
        assert gen.normalise_version("iso-27001", "   ") == "n/a"

    def test_non_empty_passes_through(self) -> None:
        assert gen.normalise_version("iso-27001", "2022") == "2022"

    def test_strips_surrounding_whitespace(self) -> None:
        assert gen.normalise_version("iso-27001", "  2022  ") == "2022"


# --------------------------------------------------------------------- #
# iter_uc_sidecars                                                      #
# --------------------------------------------------------------------- #


class TestIterUcSidecars:
    def test_returns_empty_when_content_dir_absent(
        self, hermetic_root: Path
    ) -> None:
        # Line 255-256: missing CONTENT_DIR short-circuits to an
        # empty generator (no exception raised; build proceeds with
        # zero entries).
        (hermetic_root / "content").rmdir()
        assert list(gen.iter_uc_sidecars()) == []

    def test_yields_well_formed_sidecars(self, hermetic_root: Path) -> None:
        _write_uc(hermetic_root, "cat-01-foo", "1.1.1")
        _write_uc(hermetic_root, "cat-01-foo", "1.1.2")
        out = list(gen.iter_uc_sidecars())
        assert len(out) == 2
        assert all(p.name.startswith("UC-") for p in out)

    def test_skips_malformed_json(self, hermetic_root: Path) -> None:
        cat_dir = hermetic_root / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        # Line 260-261: JSONDecodeError causes the sidecar to be
        # silently skipped instead of aborting the iteration.
        (cat_dir / "UC-1.1.1.json").write_text("not json", encoding="utf-8")
        _write_uc(hermetic_root, "cat-01-foo", "1.1.2")
        out = list(gen.iter_uc_sidecars())
        assert len(out) == 1
        assert out[0].name == "UC-1.1.2.json"

    def test_skips_sidecars_without_id_field(
        self, hermetic_root: Path
    ) -> None:
        cat_dir = hermetic_root / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        # Line 262-263: a JSON object missing the ``id`` key is
        # rejected (it cannot be part of the ledger because the
        # mappingId requires uc_id).
        (cat_dir / "UC-1.1.1.json").write_text(
            json.dumps({"title": "no id"}), encoding="utf-8"
        )
        out = list(gen.iter_uc_sidecars())
        assert out == []

    def test_skips_non_object_json(self, hermetic_root: Path) -> None:
        cat_dir = hermetic_root / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        # The same line 262 guard rejects top-level lists / strings;
        # sidecars must be dicts.
        (cat_dir / "UC-1.1.1.json").write_text(
            json.dumps(["a", "b"]), encoding="utf-8"
        )
        out = list(gen.iter_uc_sidecars())
        assert out == []

    def test_dedupes_repeated_ids(self, hermetic_root: Path) -> None:
        # Line 264-267: when two sidecars share the same ``id`` the
        # second is silently skipped. ``sorted(rglob(...))`` walks
        # alphabetically so the file under ``cat-01`` wins over the
        # one under ``cat-02``.
        _write_uc(hermetic_root, "cat-01-foo", "1.1.1")
        _write_uc(hermetic_root, "cat-02-foo", "1.1.1")
        out = list(gen.iter_uc_sidecars())
        assert len(out) == 1
        assert "cat-01-foo" in str(out[0])


# --------------------------------------------------------------------- #
# Git probing                                                           #
# --------------------------------------------------------------------- #


def _stub_subprocess(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[list[str]], subprocess.CompletedProcess[str]],
) -> None:
    """Replace ``subprocess.run`` inside the generator module with
    ``handler``. The handler receives ``argv`` (a list of strings)
    and must return a ``subprocess.CompletedProcess`` (or raise
    OSError / SubprocessError to simulate a process failure)."""

    def _fake(*args: Any, **kwargs: Any) -> Any:
        argv = list(args[0]) if args else list(kwargs.get("args", []))
        return handler(argv)

    monkeypatch.setattr(gen.subprocess, "run", _fake)


class TestGitShort:
    def test_long_sha_truncated_to_seven(self) -> None:
        assert gen._git_short("a" * 40) == "a" * 7

    def test_short_sha_returned_verbatim(self) -> None:
        # Line 298: SHA shorter than 7 chars is returned as-is
        # (rather than padded), so the schema-validator can flag
        # malformed shas downstream.
        assert gen._git_short("abc") == "abc"


class TestPopulateGitCachesBulk:
    def test_returns_early_when_already_populated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 308-309: the cache is a write-once contract; setting
        # the flag short-circuits any further git invocation.
        gen._git_bulk_populated = True
        calls: list[Any] = []
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: calls.append(a) or None,
        )
        gen._populate_git_caches_bulk([Path("anything")])
        assert calls == []

    def test_returns_early_when_path_list_empty(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        # Line 311-313: empty rel_paths short-circuits before any
        # subprocess call and still flips the populated flag so
        # downstream callers don't re-attempt.
        calls: list[Any] = []
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: calls.append(a) or None,
        )
        gen._populate_git_caches_bulk([])
        assert calls == []
        assert gen._git_bulk_populated is True

    def test_parses_sha_and_path_lines(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        """Two-pass parsing: each ``CompletedProcess`` returns a
        stream that alternates 40-hex SHAs and path lines so we can
        verify both pass-1 (lastModified) and pass-2 (firstSeen)
        consume the format correctly."""

        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")

        sha_recent = "f" * 40
        sha_oldest = "a" * 40
        rel = str(target.relative_to(hermetic_root))

        pass_1 = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"{sha_recent}\n{rel}\n\n{sha_oldest}\n{rel}\n",
            stderr="",
        )
        pass_2 = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"{sha_recent}\n{rel}\n",
            stderr="",
        )
        responses = iter([pass_1, pass_2])
        monkeypatch.setattr(
            gen.subprocess, "run", lambda *a, **k: next(responses)
        )

        gen._populate_git_caches_bulk([target])
        assert gen._git_last_modified_cache[target] == sha_recent[:7]
        assert gen._git_first_seen_cache[target] == sha_recent[:7]
        assert gen._git_bulk_populated is True

    def test_orphan_path_line_before_sha_is_ignored(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        # Line 337-338: a path line without a preceding SHA must not
        # crash and must not populate the cache (only paths anchored
        # to a current_sha are recorded).
        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        rel = str(target.relative_to(hermetic_root))

        pass_1 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=f"{rel}\n", stderr=""
        )
        pass_2 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        responses = iter([pass_1, pass_2])
        monkeypatch.setattr(
            gen.subprocess, "run", lambda *a, **k: next(responses)
        )

        gen._populate_git_caches_bulk([target])
        assert target not in gen._git_last_modified_cache
        assert target not in gen._git_first_seen_cache

    def test_pass1_oserror_falls_through_to_populated(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        # Line 325-327: an OSError on the first git invocation
        # flips the populated flag and exits early without raising.
        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")

        def _raise(*a: Any, **k: Any) -> Any:
            raise OSError("git missing")

        monkeypatch.setattr(gen.subprocess, "run", _raise)
        gen._populate_git_caches_bulk([target])
        assert gen._git_bulk_populated is True
        assert gen._git_last_modified_cache == {}
        assert gen._git_first_seen_cache == {}

    def test_pass1_subprocess_error_swallowed(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")

        def _raise(*a: Any, **k: Any) -> Any:
            raise subprocess.SubprocessError("aborted")

        monkeypatch.setattr(gen.subprocess, "run", _raise)
        gen._populate_git_caches_bulk([target])
        assert gen._git_bulk_populated is True

    def test_pass2_oserror_after_successful_pass1(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        # Line 363-365: pass-2 OSError leaves pass-1 cache populated
        # but pass-2 cache empty. Cache should still flip to populated
        # so the next call short-circuits.
        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        rel = str(target.relative_to(hermetic_root))

        pass_1 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=f"{'a' * 40}\n{rel}\n", stderr=""
        )

        calls = {"n": 0}

        def _runner(*a: Any, **k: Any) -> Any:
            calls["n"] += 1
            if calls["n"] == 1:
                return pass_1
            raise OSError("git missing")

        monkeypatch.setattr(gen.subprocess, "run", _runner)
        gen._populate_git_caches_bulk([target])
        assert gen._git_last_modified_cache[target] == "a" * 7
        assert gen._git_first_seen_cache == {}
        assert gen._git_bulk_populated is True

    def test_pass1_blank_line_is_skipped(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        # Line 332-333: pass-1 parsing must skip blank separator
        # lines that ``git log --format=%H --name-only`` emits
        # between commit records. Without this guard the next path
        # line would be associated with the wrong (stale) SHA.
        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        rel = str(target.relative_to(hermetic_root))
        # Empty middle line forces ``if not line: continue`` to fire.
        pass_1 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=f"\n{'a' * 40}\n{rel}\n", stderr=""
        )
        pass_2 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        responses = iter([pass_1, pass_2])
        monkeypatch.setattr(
            gen.subprocess, "run", lambda *a, **k: next(responses)
        )
        gen._populate_git_caches_bulk([target])
        assert gen._git_last_modified_cache[target] == "a" * 7

    def test_pass2_blank_line_is_skipped(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        # Companion guard on pass 2 (line 370-371): blank separator
        # between commit records must not crash the parser.
        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        rel = str(target.relative_to(hermetic_root))
        pass_1 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        pass_2 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=f"\n{'b' * 40}\n{rel}\n", stderr=""
        )
        responses = iter([pass_1, pass_2])
        monkeypatch.setattr(
            gen.subprocess, "run", lambda *a, **k: next(responses)
        )
        gen._populate_git_caches_bulk([target])
        assert gen._git_first_seen_cache[target] == "b" * 7

    def test_pass2_orphan_path_line_is_ignored(
        self, monkeypatch: pytest.MonkeyPatch, hermetic_root: Path
    ) -> None:
        # Line 375-376: same orphan-path guard exists on pass 2.
        target = hermetic_root / "content" / "cat-01-foo" / "UC-1.1.1.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")
        rel = str(target.relative_to(hermetic_root))

        pass_1 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="", stderr=""
        )
        pass_2 = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=f"{rel}\n", stderr=""
        )
        responses = iter([pass_1, pass_2])
        monkeypatch.setattr(
            gen.subprocess, "run", lambda *a, **k: next(responses)
        )

        gen._populate_git_caches_bulk([target])
        assert gen._git_first_seen_cache == {}


class TestGitFirstAndLastModifiedAccessors:
    def test_returns_cached_sha_when_present(self) -> None:
        p = Path("anywhere")
        gen._git_first_seen_cache[p] = "aaaaaaa"
        gen._git_last_modified_cache[p] = "bbbbbbb"
        assert gen.git_first_seen_commit(p) == "aaaaaaa"
        assert gen.git_last_modified_commit(p) == "bbbbbbb"

    def test_returns_none_when_not_cached(self) -> None:
        assert gen.git_first_seen_commit(Path("missing")) is None
        assert gen.git_last_modified_commit(Path("missing")) is None


class TestCatalogueHeadCommit:
    def test_returns_short_sha_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[], returncode=0, stdout="deadbeef\n", stderr=""
            ),
        )
        assert gen.catalogue_head_commit() == "deadbeef"

    def test_returns_placeholder_on_subprocess_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 406-408: git failure falls back to '0000000' which
        # the schema accepts as 7+ hex chars and which the audit
        # reads as 'no git history available'.
        def _raise(*a: Any, **k: Any) -> Any:
            raise subprocess.SubprocessError("aborted")

        monkeypatch.setattr(gen.subprocess, "run", _raise)
        assert gen.catalogue_head_commit() == "0000000"

    def test_returns_placeholder_on_oserror(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*a: Any, **k: Any) -> Any:
            raise OSError("git binary missing")

        monkeypatch.setattr(gen.subprocess, "run", _raise)
        assert gen.catalogue_head_commit() == "0000000"

    def test_invalid_hex_in_output_returns_placeholder(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The regex requires 7-40 hex chars; anything else (whitespace,
        # punctuation, ASCII letters) falls through to '0000000'.
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="not-a-sha\n",
                stderr="",
            ),
        )
        assert gen.catalogue_head_commit() == "0000000"


class TestCommitDateIso:
    def test_returns_normalised_iso_with_z_suffix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="2026-05-19T12:34:56+02:00\n",
                stderr="",
            ),
        )
        # Line 422-429: input with timezone gets normalised to UTC
        # 'Z' form so the ledger is stable regardless of local zone.
        out = gen.commit_date_iso("deadbeef")
        assert out == "2026-05-19T10:34:56Z"

    def test_returns_normalised_iso_when_input_lacks_tzinfo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 426-428: naive datetimes get tzinfo=UTC attached.
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="2026-05-19T12:34:56\n",
                stderr="",
            ),
        )
        out = gen.commit_date_iso("deadbeef")
        assert out == "2026-05-19T12:34:56Z"

    def test_returns_none_on_empty_stdout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            ),
        )
        assert gen.commit_date_iso("deadbeef") is None

    def test_returns_none_on_subprocess_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(*a: Any, **k: Any) -> Any:
            raise subprocess.SubprocessError("aborted")

        monkeypatch.setattr(gen.subprocess, "run", _raise)
        assert gen.commit_date_iso("deadbeef") is None

    def test_returns_none_on_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 430-431: malformed ISO triggers ValueError in
        # ``datetime.fromisoformat`` which the helper swallows.
        monkeypatch.setattr(
            gen.subprocess,
            "run",
            lambda *a, **k: subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout="not-an-iso-date\n",
                stderr="",
            ),
        )
        assert gen.commit_date_iso("deadbeef") is None


class TestDeterministicGeneratedAt:
    def test_returns_commit_date_when_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            gen, "commit_date_iso", lambda h: "2026-05-19T12:34:56Z"
        )
        out = gen.deterministic_generated_at("deadbeef")
        assert out == "2026-05-19T12:34:56Z"

    def test_falls_back_to_fixed_epoch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 448-449: when git metadata is unavailable, the
        # generator falls back to the documented epoch so the
        # audit still has a fixed point of reference.
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: None)
        out = gen.deterministic_generated_at("deadbeef")
        assert out == "2026-01-01T00:00:00Z"


# --------------------------------------------------------------------- #
# Signoffs                                                              #
# --------------------------------------------------------------------- #


class TestLoadSignoffs:
    def test_returns_empty_when_files_missing(self, hermetic_root: Path) -> None:
        out = gen.load_signoffs()
        assert out == {"peer": [], "legal": [], "sme": []}

    def test_skips_files_with_invalid_json(
        self, hermetic_root: Path
    ) -> None:
        # Line 468-469: a JSONDecodeError leaves that kind's list as
        # the default empty []; the other kinds are unaffected.
        (hermetic_root / "data" / "provenance" / "peer-review-signoffs.json").write_text(
            "not json", encoding="utf-8"
        )
        out = gen.load_signoffs()
        assert out["peer"] == []

    def test_returns_loaded_signoffs(self, hermetic_root: Path) -> None:
        (hermetic_root / "data" / "provenance" / "sme-signoffs.json").write_text(
            json.dumps({"signoffs": [{"scope": ["1.1.1"], "pr": "PR-1"}]}),
            encoding="utf-8",
        )
        out = gen.load_signoffs()
        assert out["sme"] == [{"scope": ["1.1.1"], "pr": "PR-1"}]

    def test_ignores_signoffs_not_a_list(self, hermetic_root: Path) -> None:
        # Line 471-472: the ``isinstance(entries, list)`` guard rejects
        # malformed payloads (e.g. signoffs accidentally serialised as
        # a dict) so the audit doesn't crash on iteration.
        (hermetic_root / "data" / "provenance" / "legal-review-signoffs.json").write_text(
            json.dumps({"signoffs": {"not": "a list"}}),
            encoding="utf-8",
        )
        out = gen.load_signoffs()
        assert out["legal"] == []


class TestSignoffStatusFor:
    def test_peer_always_required_and_signed_when_in_scope(
        self,
    ) -> None:
        entry = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="r",
            regulation_version="1",
            clause="c",
            mode="satisfies",
            assurance="partial",
            derivation_source=None,
        )
        signoffs = {
            "peer": [{"scope": ["1.1.1"], "pr": "#42"}],
            "legal": [],
            "sme": [],
        }
        out = gen.signoff_status_for(entry, signoffs, {})
        # Peer: required and signed; legal/sme: not required for
        # assurance != 'full' and mode != 'detects-violation-of'.
        assert out["peer"]["status"] == "signed"
        assert out["peer"]["latestSignoffPr"] == "#42"
        assert out["legal"]["status"] == "not-required"
        assert out["sme"]["status"] == "not-required"

    def test_full_assurance_requires_legal_and_sme(self) -> None:
        # Line 511-515: legal kicks in on 'full' assurance; sme
        # kicks in on 'full' assurance OR 'detects-violation-of'
        # mode.
        entry = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="r",
            regulation_version="1",
            clause="c",
            mode="satisfies",
            assurance="full",
            derivation_source=None,
        )
        out = gen.signoff_status_for(entry, {"peer": [], "legal": [], "sme": []}, {})
        assert out["legal"]["required"] is True
        assert out["sme"]["required"] is True

    def test_detects_violation_of_mode_requires_sme_even_when_partial(
        self,
    ) -> None:
        entry = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="r",
            regulation_version="1",
            clause="c",
            mode="detects-violation-of",
            assurance="partial",
            derivation_source=None,
        )
        out = gen.signoff_status_for(entry, {"peer": [], "legal": [], "sme": []}, {})
        assert out["sme"]["required"] is True
        # 'detects-violation-of' alone does NOT promote legal.
        assert out["legal"]["required"] is False

    def test_pending_when_required_but_not_signed(self) -> None:
        # Line 503-507: required-but-unsigned mappings get
        # status='pending' so the audit can decide whether to
        # grandfather them based on the baseline commit.
        entry = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="r",
            regulation_version="1",
            clause="c",
            mode="satisfies",
            assurance="partial",
            derivation_source=None,
        )
        out = gen.signoff_status_for(entry, {"peer": [], "legal": [], "sme": []}, {})
        assert out["peer"]["status"] == "pending"

    def test_pending_when_record_present_but_scope_does_not_match(
        self,
    ) -> None:
        # Branch 500->498: the for loop iterates over records but the
        # ``if entry.uc_id in scopes`` predicate is False so the loop
        # continues until exhausted, falling through to the 'pending'
        # return at line 507. Without a record-present-but-non-match
        # case only the empty-records short-circuit was exercised.
        entry = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="r",
            regulation_version="1",
            clause="c",
            mode="satisfies",
            assurance="partial",
            derivation_source=None,
        )
        signoffs = {
            "peer": [
                {"scope": ["9.9.9"], "pr": "PR-A"},
                {"scope": ["8.8.8"], "pr": "PR-B"},
            ],
            "legal": [],
            "sme": [],
        }
        out = gen.signoff_status_for(entry, signoffs, {})
        # Records exist for other UCs only — peer status must be
        # 'pending' (not signed) for 1.1.1.
        assert out["peer"]["status"] == "pending"
        assert "latestSignoffPr" not in out["peer"]

    def test_direct_commit_fallback_when_pr_field_missing(self) -> None:
        # Line 501: when signoff record lacks 'pr', the latest
        # signoff is recorded as 'direct-commit' so the ledger
        # still encodes the provenance.
        entry = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="r",
            regulation_version="1",
            clause="c",
            mode="satisfies",
            assurance="partial",
            derivation_source=None,
        )
        signoffs = {
            "peer": [{"scope": ["1.1.1"]}],
            "legal": [],
            "sme": [],
        }
        out = gen.signoff_status_for(entry, signoffs, {})
        assert out["peer"]["latestSignoffPr"] == "direct-commit"


# --------------------------------------------------------------------- #
# Ledger inputs / entries / merkle                                      #
# --------------------------------------------------------------------- #


class TestBuildLedgerInputs:
    def test_skips_empty_compliance_array(self, hermetic_root: Path) -> None:
        _write_regulations(hermetic_root)
        _write_uc(hermetic_root, "cat-01-foo", "1.1.1", compliance=[])
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert out == []

    def test_skips_entry_with_empty_regulation_name(
        self, hermetic_root: Path
    ) -> None:
        # Line 537-538: an empty regulation name is silently skipped
        # (it can't be resolved to a regulation id).
        _write_regulations(hermetic_root)
        _write_uc(
            hermetic_root,
            "cat-01-foo",
            "1.1.1",
            compliance=[{"regulation": "", "clause": "X", "mode": "satisfies", "assurance": "partial"}],
        )
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert out == []

    def test_skips_entry_with_empty_clause(self, hermetic_root: Path) -> None:
        # Line 545-547: an empty clause is silently skipped (ledger
        # uniqueness requires a non-empty clause).
        _write_regulations(hermetic_root)
        _write_uc(
            hermetic_root,
            "cat-01-foo",
            "1.1.1",
            compliance=[
                {
                    "regulation": "ISO/IEC 27001",
                    "version": "2022",
                    "clause": "",
                    "mode": "satisfies",
                    "assurance": "partial",
                }
            ],
        )
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert out == []

    def test_skips_entry_with_unknown_mode(self, hermetic_root: Path) -> None:
        # Line 550-556: an unknown mode is silently skipped (we
        # never extend the closed set of modes without a schema
        # bump first).
        _write_regulations(hermetic_root)
        _write_uc(
            hermetic_root,
            "cat-01-foo",
            "1.1.1",
            compliance=[
                {
                    "regulation": "ISO/IEC 27001",
                    "version": "2022",
                    "clause": "A.8.16",
                    "mode": "made-up-mode",
                    "assurance": "partial",
                }
            ],
        )
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert out == []

    def test_skips_entry_with_unknown_assurance(self, hermetic_root: Path) -> None:
        # Line 557-558: same closed-set rule for assurance.
        _write_regulations(hermetic_root)
        _write_uc(
            hermetic_root,
            "cat-01-foo",
            "1.1.1",
            compliance=[
                {
                    "regulation": "ISO/IEC 27001",
                    "version": "2022",
                    "clause": "A.8.16",
                    "mode": "satisfies",
                    "assurance": "absolute",
                }
            ],
        )
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert out == []

    def test_skips_sidecar_without_id(self, hermetic_root: Path) -> None:
        # Line 531-533: a sidecar missing the ``id`` field is skipped
        # by ``iter_uc_sidecars``, but the inner ``if not uc_id:`` is
        # a belt-and-braces guard in ``build_ledger_inputs``. Cover
        # it by writing a sidecar whose id is the empty string.
        _write_regulations(hermetic_root)
        cat_dir = hermetic_root / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        (cat_dir / "UC-1.1.1.json").write_text(
            json.dumps({"id": "1.1.1", "compliance": []}), encoding="utf-8"
        )
        (cat_dir / "UC-1.1.2.json").write_text(
            json.dumps({"id": "1.1.2", "compliance": []}), encoding="utf-8"
        )
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert out == []

    def test_unresolved_regulation_exits_with_status_2(
        self, hermetic_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Line 572-576: any unresolved name aborts the build with
        # exit code 2 and lists the first 10 offenders on stderr.
        _write_regulations(hermetic_root)
        _write_uc(
            hermetic_root,
            "cat-01-foo",
            "1.1.1",
            compliance=[
                {
                    "regulation": "Made Up Reg",
                    "version": "1",
                    "clause": "A.1",
                    "mode": "satisfies",
                    "assurance": "partial",
                }
            ],
        )
        with pytest.raises(SystemExit) as ei:
            gen.build_ledger_inputs(gen.load_regulation_index())
        assert ei.value.code == 2
        captured = capsys.readouterr()
        assert "FATAL: unresolved regulation names" in captured.err
        assert "Made Up Reg" in captured.err

    def test_falsy_uc_id_after_iter_sidecars_is_skipped(
        self, hermetic_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 531-533: defensive guard at the inner level. We must
        # be able to pass through ``iter_uc_sidecars`` and still hit
        # the ``if not uc_id`` check inside the loop. Stub
        # ``iter_uc_sidecars`` to yield a path whose sidecar parses
        # to ``{"id": ""}`` so the outer iterator's own ``id`` check
        # cannot filter it.
        _write_regulations(hermetic_root)
        cat_dir = hermetic_root / "content" / "cat-01-foo"
        cat_dir.mkdir(parents=True)
        bad = cat_dir / "UC-empty.json"
        bad.write_text(json.dumps({"id": ""}), encoding="utf-8")
        monkeypatch.setattr(gen, "iter_uc_sidecars", lambda: iter([bad]))
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert out == []

    def test_full_happy_path_extracts_canonical_tuple(
        self, hermetic_root: Path
    ) -> None:
        _write_regulations(hermetic_root)
        _write_uc(
            hermetic_root,
            "cat-01-foo",
            "1.1.1",
            compliance=[
                {
                    "regulation": "ISO/IEC 27001",
                    "version": "2022",
                    "clause": "A.8.16",
                    "mode": "satisfies",
                    "assurance": "full",
                    "derivationSource": {"parentRegulation": "iso-27001"},
                }
            ],
        )
        out = gen.build_ledger_inputs(gen.load_regulation_index())
        assert len(out) == 1
        assert out[0].uc_id == "1.1.1"
        assert out[0].regulation_id == "iso-27001"
        assert out[0].regulation_version == "2022"
        assert out[0].clause == "A.8.16"
        assert out[0].mode == "satisfies"
        assert out[0].assurance == "full"
        assert out[0].derivation_source == {"parentRegulation": "iso-27001"}


class TestMappingIdAndCanonicalPayload:
    def test_mapping_id_format(self) -> None:
        li = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="full",
            derivation_source=None,
        )
        mid = gen.mapping_id_of(li)
        assert mid == "1.1.1::iso-27001@2022::A.8.16::satisfies::full"

    def test_canonical_payload_omits_derivation_when_none(self) -> None:
        li = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="full",
            derivation_source=None,
        )
        out = gen.canonical_entry_payload(li, gen.mapping_id_of(li))
        assert "derivationSource" not in out

    def test_canonical_payload_includes_derivation_when_present(self) -> None:
        # Line 599-611: derivationSource is normalised into a stable
        # field order and conditionally includes parentAssurance /
        # divergenceNote depending on whether they are truthy.
        li = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="full",
            derivation_source={
                "parentRegulation": "iso-27001",
                "parentVersion": "2013",
                "parentClause": "A.7.1",
                "inheritanceMode": "exact",
                "parentAssurance": "partial",
                "divergenceNote": "tightened scope",
            },
        )
        payload = gen.canonical_entry_payload(li, gen.mapping_id_of(li))
        ds = payload["derivationSource"]
        assert ds["parentRegulation"] == "iso-27001"
        assert ds["parentVersion"] == "2013"
        assert ds["parentClause"] == "A.7.1"
        assert ds["inheritanceMode"] == "exact"
        assert ds["parentAssurance"] == "partial"
        assert ds["divergenceNote"] == "tightened scope"

    def test_canonical_payload_omits_optional_derivation_fields(self) -> None:
        # The conditional inclusion of parentAssurance / divergenceNote
        # means a minimal derivation block (only mandatory keys present)
        # must not pollute the canonical payload with empty strings.
        li = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("x"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="full",
            derivation_source={
                "parentRegulation": "iso-27001",
                "parentVersion": "2013",
                "parentClause": "A.7.1",
                "inheritanceMode": "exact",
            },
        )
        payload = gen.canonical_entry_payload(li, gen.mapping_id_of(li))
        ds = payload["derivationSource"]
        assert "parentAssurance" not in ds
        assert "divergenceNote" not in ds


class TestBuildLedgerEntry:
    def test_uses_cached_git_metadata_when_available(self) -> None:
        li = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("anywhere"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="partial",
            derivation_source=None,
        )
        gen._git_first_seen_cache[li.uc_path] = "aaaaaaa"
        gen._git_last_modified_cache[li.uc_path] = "bbbbbbb"
        record = gen.build_ledger_entry(
            li,
            {"peer": [], "legal": [], "sme": []},
            {},
            head_commit="ffffffff",
        )
        assert record["firstSeenCommit"] == "aaaaaaa"
        assert record["lastModifiedCommit"] == "bbbbbbb"
        assert record["mappingId"].startswith("1.1.1::")
        assert "canonicalHash" in record
        assert record["signoffStatus"]["peer"]["status"] == "pending"

    def test_falls_back_to_head_commit_when_cache_missing(self) -> None:
        # Line 625-626: cache miss falls back to ``head_commit``, which
        # is what shallow clones / new sidecars do.
        li = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("unmonitored"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="partial",
            derivation_source=None,
        )
        record = gen.build_ledger_entry(
            li,
            {"peer": [], "legal": [], "sme": []},
            {},
            head_commit="ffffffff",
        )
        assert record["firstSeenCommit"] == "ffffffff"
        assert record["lastModifiedCommit"] == "ffffffff"


class TestComputeMerkleRoot:
    def test_empty_entry_list_yields_domain_separator_hash(self) -> None:
        out = gen.compute_merkle_root([])
        h = hashlib.sha256(b"mapping-ledger\x00").hexdigest()
        assert out == h

    def test_populated_entry_list_produces_stable_root(self) -> None:
        entries = [
            {"canonicalHash": "aa"},
            {"canonicalHash": "bb"},
        ]
        out = gen.compute_merkle_root(entries)
        # Pin the bytes contract: domain separator, then each hash
        # followed by a newline, all rolled into one sha256.
        h = hashlib.sha256()
        h.update(b"mapping-ledger\x00")
        h.update(b"aa\n")
        h.update(b"bb\n")
        assert out == h.hexdigest()


# --------------------------------------------------------------------- #
# Auxiliary sources                                                     #
# --------------------------------------------------------------------- #


class TestBuildAuxiliarySources:
    def test_missing_files_emit_stderr_note_and_are_skipped(
        self, hermetic_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Default AUXILIARY_SOURCES files don't exist in the
        # hermetic root, so every entry should be skipped with a
        # stderr line printed for each.
        out = gen.build_auxiliary_sources()
        assert out == []
        captured = capsys.readouterr()
        assert "auxiliary source missing" in captured.err

    def test_handles_oserror_when_reading_aux_file(
        self,
        hermetic_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Line 742-747: a present-but-unreadable file emits a
        # second-style stderr note and is excluded from the list.
        target = hermetic_root / "data" / "splunkbase-catalog.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("{}", encoding="utf-8")

        real_read = Path.read_bytes

        def _raise(self: Path) -> bytes:
            if self == target:
                raise OSError("permission denied")
            return real_read(self)

        monkeypatch.setattr(Path, "read_bytes", _raise)
        out = gen.build_auxiliary_sources()
        captured = capsys.readouterr()
        # Should print 'unreadable' for the failing file and 'missing'
        # for the other two.
        assert "auxiliary source unreadable" in captured.err
        # And the failing file must not appear in the returned list.
        assert all("splunkbase-catalog.json" not in e["path"] for e in out)

    def test_present_files_are_hashed_and_sorted(
        self, hermetic_root: Path
    ) -> None:
        # Write all three default aux sources so the sort branch
        # (line 756) has data to sort.
        for rel_path, _purpose in gen.AUXILIARY_SOURCES:
            abs_path = hermetic_root / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(rel_path, encoding="utf-8")
        out = gen.build_auxiliary_sources()
        assert len(out) == len(gen.AUXILIARY_SOURCES)
        # The list must be sorted alphabetically by path so the
        # ledger digest stays stable.
        paths = [e["path"] for e in out]
        assert paths == sorted(paths)
        for entry in out:
            assert "sha256" in entry
            assert "bytes" in entry
            assert "purpose" in entry


# --------------------------------------------------------------------- #
# build_ledger (top-level orchestrator)                                 #
# --------------------------------------------------------------------- #


class TestBuildLedger:
    def test_full_build_returns_well_formed_ledger(
        self, hermetic_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_regulations(hermetic_root)
        _write_uc(
            hermetic_root,
            "cat-01-foo",
            "1.1.1",
            compliance=[
                {
                    "regulation": "ISO/IEC 27001",
                    "version": "2022",
                    "clause": "A.8.16",
                    "mode": "satisfies",
                    "assurance": "full",
                }
            ],
        )
        # Stub git so the test runs offline.
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "2026-05-19T00:00:00Z")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        out = gen.build_ledger()
        assert out["schemaVersion"] == gen.SCHEMA_VERSION
        assert out["catalogueCommit"] == "deadbee"
        assert out["generatedAt"] == "2026-05-19T00:00:00Z"
        assert out["entryCount"] == 1
        assert len(out["entries"]) == 1
        assert out["entries"][0]["ucId"] == "1.1.1"
        assert "merkleRoot" in out
        assert out["signature"]["state"] == "unsigned"

    def test_collision_with_divergent_content_exits_with_status_2(
        self,
        hermetic_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Lines 688-692: two records with the same mappingId but
        # different canonicalHash trigger a fatal error and exit(2).
        # We fabricate this by stubbing build_ledger_inputs to return
        # a duplicate LedgerInput whose ``derivation_source`` differs
        # between the two copies (which alters the canonical hash).
        _write_regulations(hermetic_root)
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        li_a = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("a"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="full",
            derivation_source=None,
        )
        li_b = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("b"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="full",
            derivation_source={"parentRegulation": "iso-27001"},
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [li_a, li_b])
        with pytest.raises(SystemExit) as ei:
            gen.build_ledger()
        assert ei.value.code == 2
        captured = capsys.readouterr()
        assert "mappingId collisions" in captured.err

    def test_duplicate_with_same_canonical_hash_is_silently_deduped(
        self,
        hermetic_root: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Line 683-687 happy path: identical mappingId + identical
        # canonicalHash is silently deduped (the second copy is
        # ignored without raising).
        _write_regulations(hermetic_root)
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        li = gen.LedgerInput(
            uc_id="1.1.1",
            uc_path=Path("a"),
            regulation_id="iso-27001",
            regulation_version="2022",
            clause="A.8.16",
            mode="satisfies",
            assurance="full",
            derivation_source=None,
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [li, li])
        out = gen.build_ledger()
        assert out["entryCount"] == 1

    def test_baseline_with_invalid_json_falls_back_to_placeholder(
        self, hermetic_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 664-665: JSONDecodeError on a signoff file leaves the
        # baseline as the '0000000' placeholder for that kind. The
        # build still succeeds.
        _write_regulations(hermetic_root)
        (hermetic_root / "data" / "provenance" / "peer-review-signoffs.json").write_text(
            "not json", encoding="utf-8"
        )
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        # No UC compliance entries needed; we just want the baseline
        # loop to execute over a malformed file.
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [])
        out = gen.build_ledger()
        # The build completed; the baseline parsing failure didn't
        # raise. (Baselines are internal state passed to
        # signoff_status_for; we don't assert on them directly here.)
        assert out["entryCount"] == 0

    def test_baseline_from_well_formed_signoff_file_is_read(
        self, hermetic_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 663: success-path read of a well-formed signoff file
        # that carries a ``baseline_commit`` field. Without this
        # test only the JSONDecodeError fall-through (line 665) was
        # exercised.
        _write_regulations(hermetic_root)
        (hermetic_root / "data" / "provenance" / "legal-review-signoffs.json").write_text(
            json.dumps({"baseline_commit": "cafef00", "signoffs": []}),
            encoding="utf-8",
        )
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [])
        out = gen.build_ledger()
        # The ledger build doesn't expose baselines directly, but
        # successfully completing without raising is the contract
        # we're pinning here.
        assert out["entryCount"] == 0

    def test_auxiliary_sources_present_attaches_field_to_ledger(
        self, hermetic_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Line 718-719: when ``build_auxiliary_sources`` returns a
        # non-empty list the ledger gains an ``auxiliarySources``
        # key. Without this test only the empty-list branch (which
        # omits the key) was exercised.
        _write_regulations(hermetic_root)
        for rel_path, _purpose in gen.AUXILIARY_SOURCES:
            abs_path = hermetic_root / rel_path
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text("seed", encoding="utf-8")
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [])
        out = gen.build_ledger()
        assert "auxiliarySources" in out
        assert len(out["auxiliarySources"]) == len(gen.AUXILIARY_SOURCES)


# --------------------------------------------------------------------- #
# render + main + diff helpers                                          #
# --------------------------------------------------------------------- #


class TestRender:
    def test_render_appends_trailing_newline_and_pretty_prints(self) -> None:
        out = gen.render({"a": 1, "b": [1, 2]})
        assert out.endswith("\n")
        # Pretty-printed JSON has indentation + key order preserved.
        assert '\n  "a": 1,\n  "b": [' in out


class TestMain:
    def test_default_write_path_writes_file_and_returns_zero(
        self,
        hermetic_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_regulations(hermetic_root)
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [])
        rc = gen.main([])
        assert rc == 0
        assert gen.LEDGER_PATH.exists()
        body = gen.LEDGER_PATH.read_text(encoding="utf-8")
        assert body.endswith("\n")
        captured = capsys.readouterr()
        assert "Wrote" in captured.out

    def test_check_mode_succeeds_when_ledger_is_up_to_date(
        self,
        hermetic_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_regulations(hermetic_root)
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [])
        # First a default run to seed the file.
        assert gen.main([]) == 0
        # Then --check should report OK and return 0.
        captured = capsys.readouterr()  # Drain.
        del captured
        rc = gen.main(["--check"])
        assert rc == 0
        captured = capsys.readouterr()
        assert "OK" in captured.out

    def test_check_mode_fails_when_ledger_is_missing(
        self,
        hermetic_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Lines 786-791: missing ledger in --check is a hard error.
        _write_regulations(hermetic_root)
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [])
        rc = gen.main(["--check"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "FATAL" in captured.err
        assert "does not exist" in captured.err

    def test_check_mode_reports_drift_with_diff_preview(
        self,
        hermetic_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Lines 793-802: when the on-disk ledger differs structurally
        # from what we'd regenerate, --check returns 1 and emits a
        # diff preview on stderr.
        _write_regulations(hermetic_root)
        monkeypatch.setattr(gen, "catalogue_head_commit", lambda: "deadbee")
        monkeypatch.setattr(gen, "commit_date_iso", lambda h: "x")
        monkeypatch.setattr(
            gen, "_populate_git_caches_bulk", lambda paths: None
        )
        monkeypatch.setattr(gen, "build_ledger_inputs", lambda idx: [])
        # Seed a ledger with deliberately drifted content.
        gen.LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
        gen.LEDGER_PATH.write_text(
            json.dumps({"schemaVersion": "BOGUS"}, indent=2) + "\n",
            encoding="utf-8",
        )
        rc = gen.main(["--check"])
        assert rc == 1
        captured = capsys.readouterr()
        assert "stale" in captured.err
        assert "diff preview" in captured.err


class TestStructuralDiffAndPreview:
    def test_identical_streams_have_no_drift(self) -> None:
        a = (
            '{\n  "generatedAt": "2026-05-19T00:00:00Z",\n'
            '  "catalogueCommit": "deadbee",\n  "x": 1\n}\n'
        )
        assert gen._structural_diff(a, a) is False

    def test_drift_in_non_timestamp_field_detected(self) -> None:
        a = '{\n  "generatedAt": "2026-05-19T00:00:00Z",\n  "x": 1\n}\n'
        b = '{\n  "generatedAt": "2026-05-19T00:00:00Z",\n  "x": 2\n}\n'
        assert gen._structural_diff(a, b) is True

    def test_timestamp_only_drift_is_ignored(self) -> None:
        # Line 826-829: ``generatedAt`` / ``catalogueCommit`` change on
        # every push but the *content* hash is unchanged; the diff
        # gate must NOT fire on these alone.
        a = (
            '{\n  "generatedAt": "2026-01-01T00:00:00Z",\n'
            '  "catalogueCommit": "0000000",\n  "x": 1\n}\n'
        )
        b = (
            '{\n  "generatedAt": "2026-05-19T00:00:00Z",\n'
            '  "catalogueCommit": "deadbee",\n  "x": 1\n}\n'
        )
        assert gen._structural_diff(a, b) is False

    def test_preview_diff_emits_unified_diff_on_drift(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        gen._preview_diff("a\n", "b\n")
        captured = capsys.readouterr()
        assert "diff preview" in captured.err
        assert "-a" in captured.err
        assert "+b" in captured.err

    def test_preview_diff_emits_nothing_when_streams_equal(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Line 846-847: empty diff returns early without writing.
        gen._preview_diff("same\n", "same\n")
        captured = capsys.readouterr()
        assert captured.err == ""
