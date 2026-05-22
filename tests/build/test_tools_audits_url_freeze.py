"""Unit-level coverage for ``tools/audits/url_freeze.py``.

``url_freeze`` is the URL-stability guard documented in
``docs/url-scheme.md`` § "Permanence promise": once a public URL ships
in a release it MUST keep resolving in every later release. The audit
fetches the previous release's ``dist/api/manifest.json`` from git
(``git show <tag>:<path>``) and diffs the URL set against the current
build; any URL that disappears fails CI.

Before this commit the module had zero unit coverage
(``Module tools.audits.url_freeze was never imported`` warning).
This suite drives every branch of ``main``, ``_load_baseline``,
``_extract_urls`` and ``_walk`` hermetically. The ``git show``
subprocess is monkey-patched so no real git history is needed.

What this suite locks
---------------------

* ``main`` returns ``2`` when the HEAD manifest is missing on disk.
* ``main`` returns ``0`` with a "first-release allowlist" message
  when the baseline tag has no manifest at the requested path
  (covers both ``git show`` failure modes — CalledProcessError and
  FileNotFoundError — AND the JSON decode failure path).
* ``main`` returns ``0`` with the OK banner when no URLs were
  removed (counts new URLs added since baseline).
* ``main`` returns ``1`` and writes the per-URL diff to stderr when
  URLs were removed, capped at 50 entries with an "and N more"
  footer for overflow.
* ``_extract_urls`` ignores non-list groups, non-dict entries, and
  non-string values; collects from the four documented keys
  (``html``, ``json``, ``url``, ``path``).
* ``_walk`` recursively collects every string starting with ``/`` —
  this helper is the legacy fallback for older manifest shapes and
  is currently unused by ``main`` but still exported.
* ``__main__`` guard exercised by a subprocess smoke that passes a
  bogus baseline tag and asserts the documented "first-release
  allowlist" exit (rc=0).

Run
---

``pytest tests/build/test_tools_audits_url_freeze.py``

Coverage check
--------------

``pytest tests/build/test_tools_audits_url_freeze.py \
    --cov=tools.audits.url_freeze --cov-branch``
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.audits.url_freeze as url_freeze


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_manifest(
    tmp_path: Path,
    *,
    name: str,
    paths: dict[str, Any] | None = None,
) -> Path:
    """Write a synthetic manifest under ``tmp_path``."""

    manifest = {"paths": paths or {}}
    path = tmp_path / name
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _baseline_payload(urls: list[str]) -> dict[str, Any]:
    return {
        "paths": {
            "category-a": [{"html": u} for u in urls]
        }
    }


# ---------------------------------------------------------------------------
# Missing HEAD manifest
# ---------------------------------------------------------------------------


class TestMissingHead:
    def test_returns_2_when_head_missing(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = url_freeze.main(
            [
                "--baseline-tag",
                "v0.0.0",
                "--head",
                str(tmp_path / "absent.json"),
            ]
        )
        assert rc == 2
        err = capsys.readouterr().err
        assert "missing HEAD manifest" in err


# ---------------------------------------------------------------------------
# Baseline lookup
# ---------------------------------------------------------------------------


class TestBaselineMissing:
    def test_called_process_error_returns_none_and_main_returns_0(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``git show`` exits non-zero (e.g. the tag does not
        exist), ``_load_baseline`` returns None and ``main`` treats
        the run as a first-release allowlist (rc=0 + advisory msg)."""

        head = _make_manifest(tmp_path, name="head.json")

        def _explode(*_args, **_kwargs):
            raise subprocess.CalledProcessError(
                returncode=128, cmd=["git", "show"]
            )

        monkeypatch.setattr(subprocess, "check_output", _explode)
        rc = url_freeze.main(
            ["--baseline-tag", "v0.0.0", "--head", str(head)]
        )
        assert rc == 0
        err = capsys.readouterr().err
        assert "treating as first-release allowlist" in err
        assert "v0.0.0" in err

    def test_file_not_found_returns_none_and_main_returns_0(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If ``git`` is not installed at all, ``check_output`` raises
        FileNotFoundError. The audit must still treat the missing
        baseline as a first-release allowlist."""

        head = _make_manifest(tmp_path, name="head.json")

        def _no_git(*_args, **_kwargs):
            raise FileNotFoundError("git not found")

        monkeypatch.setattr(subprocess, "check_output", _no_git)
        rc = url_freeze.main(
            ["--baseline-tag", "v0.0.0", "--head", str(head)]
        )
        assert rc == 0

    def test_invalid_baseline_json_treats_as_first_release(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """``git show`` succeeds but returns garbage. ``_load_baseline``
        must catch ``json.JSONDecodeError`` and return None (covers
        the second ``return None`` branch)."""

        head = _make_manifest(tmp_path, name="head.json")
        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: b"{not json"
        )
        rc = url_freeze.main(
            ["--baseline-tag", "v0.0.0", "--head", str(head)]
        )
        assert rc == 0
        assert "first-release allowlist" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Happy path — no URLs removed
# ---------------------------------------------------------------------------


class TestNoRemovals:
    def test_identical_baseline_and_head_pass(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        urls = ["/uc/UC-1.1.1", "/uc/UC-2.2.2"]
        baseline = _baseline_payload(urls)
        head = _make_manifest(tmp_path, name="head.json", paths=baseline["paths"])
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode("utf-8"),
        )
        rc = url_freeze.main(
            ["--baseline-tag", "v1.0.0", "--head", str(head)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "[url_freeze] OK" in out
        assert "2 URLs" in out
        assert "+0 new since v1.0.0" in out

    def test_head_adds_urls_count_appears_in_banner(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        baseline = _baseline_payload(["/uc/UC-1.1.1"])
        head_payload = _baseline_payload(
            ["/uc/UC-1.1.1", "/uc/UC-2.2.2", "/uc/UC-3.3.3"]
        )
        head = _make_manifest(
            tmp_path, name="head.json", paths=head_payload["paths"]
        )
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode("utf-8"),
        )
        rc = url_freeze.main(
            ["--baseline-tag", "v1.0.0", "--head", str(head)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "+2 new since v1.0.0" in out


# ---------------------------------------------------------------------------
# Failure mode — URLs removed
# ---------------------------------------------------------------------------


class TestRemovals:
    def test_single_removal_returns_1_and_lists_url(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        baseline = _baseline_payload(
            ["/uc/UC-1.1.1", "/uc/UC-2.2.2"]
        )
        head_payload = _baseline_payload(["/uc/UC-1.1.1"])  # 2.2.2 removed
        head = _make_manifest(
            tmp_path, name="head.json", paths=head_payload["paths"]
        )
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode("utf-8"),
        )
        rc = url_freeze.main(
            ["--baseline-tag", "v1.0.0", "--head", str(head)]
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert "[url_freeze] FAIL" in err
        assert "1 URL(s) removed" in err
        assert "- /uc/UC-2.2.2" in err
        # Cross-references for the operator are part of the failure
        # message so the audit is self-documenting.
        assert "docs/url-scheme.md" in err
        assert "docs/api-versioning.md" in err

    def test_overflow_lists_only_50_with_footer(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        baseline_urls = [f"/uc/UC-1.1.{i}" for i in range(60)]
        baseline = _baseline_payload(baseline_urls)
        head_payload = _baseline_payload([])  # remove ALL 60
        head = _make_manifest(
            tmp_path, name="head.json", paths=head_payload["paths"]
        )
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode("utf-8"),
        )
        rc = url_freeze.main(
            ["--baseline-tag", "v1.0.0", "--head", str(head)]
        )
        assert rc == 1
        err = capsys.readouterr().err
        # 60 removed, 50 listed, "...and 10 more" footer.
        assert "60 URL(s) removed" in err
        # Count the per-URL bullet prefix ``  - /uc/`` — must be 50.
        assert err.count("  - /uc/") == 50
        assert "and 10 more" in err

    def test_no_overflow_footer_when_exactly_50_removals(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The False branch of ``if len(removed) > 50:`` — at
        exactly 50 removals the footer must NOT print."""

        baseline_urls = [f"/uc/UC-1.1.{i}" for i in range(50)]
        baseline = _baseline_payload(baseline_urls)
        head = _make_manifest(
            tmp_path, name="head.json", paths={"category-a": []}
        )
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode("utf-8"),
        )
        rc = url_freeze.main(
            ["--baseline-tag", "v1.0.0", "--head", str(head)]
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert err.count("  - /uc/") == 50
        assert "and " not in err.split("Once published")[0]


# ---------------------------------------------------------------------------
# _extract_urls
# ---------------------------------------------------------------------------


class TestExtractUrls:
    def test_empty_manifest_returns_empty_set(self) -> None:
        assert url_freeze._extract_urls({}) == set()

    def test_collects_from_all_four_keys(self) -> None:
        manifest = {
            "paths": {
                "g1": [
                    {
                        "html": "/a",
                        "json": "/a.json",
                        "url": "/a/url",
                        "path": "/a/path",
                    }
                ]
            }
        }
        assert url_freeze._extract_urls(manifest) == {
            "/a",
            "/a.json",
            "/a/url",
            "/a/path",
        }

    def test_skips_non_list_groups(self) -> None:
        manifest = {
            "paths": {
                "g1": [{"html": "/x"}],
                "g2": {"html": "/y"},   # not a list — ignored
                "g3": "not a list",      # not a list — ignored
            }
        }
        assert url_freeze._extract_urls(manifest) == {"/x"}

    def test_skips_non_dict_entries(self) -> None:
        manifest = {
            "paths": {
                "g1": [
                    {"html": "/x"},
                    "raw string — not a dict",
                    42,
                    None,
                ]
            }
        }
        assert url_freeze._extract_urls(manifest) == {"/x"}

    def test_skips_non_string_values(self) -> None:
        manifest = {
            "paths": {
                "g1": [
                    {"html": "/x", "json": 42, "url": None, "path": ["/y"]}
                ]
            }
        }
        # Only the string value /x is collected.
        assert url_freeze._extract_urls(manifest) == {"/x"}

    def test_unknown_keys_are_ignored(self) -> None:
        manifest = {
            "paths": {
                "g1": [{"html": "/x", "extra": "/y"}]
            }
        }
        # ``extra`` is not in the documented key set — ignored.
        assert url_freeze._extract_urls(manifest) == {"/x"}


# ---------------------------------------------------------------------------
# _walk — legacy/fallback recursive collector
# ---------------------------------------------------------------------------


class TestWalk:
    def test_collects_strings_starting_with_slash(self) -> None:
        data = {
            "a": ["/uc/1", "not-a-url"],
            "b": {"c": "/api/v1", "d": 5},
            "e": "/uc/2",
            "f": None,
        }
        # ``into`` parameter is currently unused by the function so
        # any iterable is acceptable.
        result = url_freeze._walk(data, [])
        assert result == {"/uc/1", "/api/v1", "/uc/2"}

    def test_non_collection_non_string_returns_empty(self) -> None:
        assert url_freeze._walk(42, []) == set()
        assert url_freeze._walk(None, []) == set()
        assert url_freeze._walk(False, []) == set()

    def test_strings_without_slash_prefix_are_skipped(self) -> None:
        assert url_freeze._walk(["a", "b", "/c"], []) == {"/c"}

    def test_deeply_nested_structures_are_walked(self) -> None:
        data = [[[{"x": "/deep"}]]]
        assert url_freeze._walk(data, []) == {"/deep"}


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


class TestCliSurface:
    def test_argv_none_falls_through_to_sys_argv(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        head = _make_manifest(tmp_path, name="head.json")
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: (_ for _ in ()).throw(
                subprocess.CalledProcessError(1, "git show")
            ),
        )
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "url_freeze",
                "--baseline-tag",
                "vx.y.z",
                "--head",
                str(head),
            ],
        )
        assert url_freeze.main() == 0
        assert "first-release allowlist" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Module entrypoint guard
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_with_bogus_tag_returns_0(
        self, tmp_path: Path
    ) -> None:
        """Invoke ``python -m tools.audits.url_freeze`` with a known-
        non-existent baseline tag. The documented behaviour is to
        treat the missing baseline as a first-release allowlist and
        exit 0. We require a valid HEAD manifest path (anything that
        exists on disk); the test writes a minimal one to
        ``tmp_path``.

        The subprocess inherits no ``coverage`` instrumentation so
        this test exists for end-to-end CLI smoke purposes only —
        unit coverage of the ``if __name__`` guard is produced by
        the test-collection import."""

        import subprocess

        repo_root = Path(url_freeze.__file__).resolve().parents[2]
        head = tmp_path / "head.json"
        head.write_text(json.dumps({"paths": {}}), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.audits.url_freeze",
                "--baseline-tag",
                "vx.y.z-does-not-exist",
                "--head",
                str(head),
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "first-release allowlist" in result.stderr
