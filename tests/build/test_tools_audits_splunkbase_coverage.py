"""Unit-level coverage for ``tools/audits/splunkbase_coverage.py``.

``splunkbase_coverage`` is the v9.0 ``splunkbaseApps[]`` migration
tracker. Every UC sidecar is expected to either (a) carry a non-empty
``splunkbaseApps[]`` array with at least one signed-off entry
(``requiresSmeReview`` absent or false) or (b) be flagged as
not-yet-migrated (every entry still carries ``requiresSmeReview:
true``). Until v9.0 GA the audit is SOFT — it reports coverage stats
and always exits 0 unless ``--strict`` is passed.

Before this commit the module had zero unit tests
(``Module tools.audits.splunkbase_coverage was never imported``).

What this suite locks
---------------------

* ``_read_uc`` happy path returns the parsed dict.
* ``_structural_errors``:
    - non-dict entry -> 'entry [i] is not an object'
    - missing 'id' / 'name' / 'role' -> 'missing required fields'
    - role not in CANONICAL_ROLES enum -> 'role=X is not in [...]'
    - url present but not under splunkbase.splunk.com/app/ -> error
    - url present but non-string -> error
    - happy entry -> empty list
    - blank-only fields are treated as missing (``entry.get(k)``
      falsy)
* ``_classify``:
    - missing 'splunkbaseApps' field -> ('missing', 0, 0, [])
    - non-list 'splunkbaseApps' -> ('missing', ...)
    - empty list -> ('missing', ...)
    - any structural error -> ('broken', 0, 0, errors)
    - all entries requiresSmeReview -> ('open', 0, N, [])
    - no entries requiresSmeReview -> ('signed', N, 0, [])
    - mix -> ('partial', signed, open, [])
* ``_category_of`` -> parent directory name.
* ``main``:
    - missing content/ -> rc=2 + stderr msg
    - malformed UC sidecar -> rc=2 + stderr msg
    - empty content/ -> rc=0 with 0/0/0/0 counts, coverage 0.0%
    - mixed corpus -> totals add up, per-category bucket grows,
      coverage = (signed+partial)/total*100
    - strict mode + only signed -> rc=0
    - strict mode + missing/open/broken UCs -> rc=1 + FAIL list,
      truncated at 10 with overflow footer
    - non-strict mode never returns 1, even with open/missing
    - broken examples capped at 5 with overflow footer
    - --json writes per-category breakdown including coveragePct
* The ``if __name__ == "__main__":`` guard is exercised by a
  subprocess smoke check against the real ``content/`` tree.

Run
---

``pytest tests/build/test_tools_audits_splunkbase_coverage.py``

Coverage check
--------------

``pytest tests/build/test_tools_audits_splunkbase_coverage.py \
    --cov=tools.audits.splunkbase_coverage --cov-branch``
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.audits.splunkbase_coverage as splunkbase_coverage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _good_entry(
    *,
    app_id: int = 100,
    name: str = "Splunk App",
    role: str = "primary",
    url: str | None = "https://splunkbase.splunk.com/app/100",
    requires_sme_review: bool | None = None,
) -> dict[str, Any]:
    """Produce a well-formed splunkbaseApps[] entry."""

    entry: dict[str, Any] = {"id": app_id, "name": name, "role": role}
    if url is not None:
        entry["url"] = url
    if requires_sme_review is not None:
        entry["requiresSmeReview"] = requires_sme_review
    return entry


def _write_uc(
    content_dir: Path,
    *,
    cat: str = "cat-01-foo",
    uc_id: str,
    splunkbase_apps: list[dict[str, Any]] | None = None,
    omit_field: bool = False,
    override_field: Any = None,
) -> Path:
    """Write a synthetic UC sidecar.

    * ``omit_field=True`` -> no ``splunkbaseApps`` key at all
    * ``override_field`` -> use this exact value (e.g. ``"not-a-list"``)
    * ``splunkbase_apps`` -> populated list (default)
    """

    cat_dir = content_dir / cat
    cat_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"id": uc_id, "title": f"UC {uc_id}"}
    if not omit_field:
        if override_field is not None:
            payload["splunkbaseApps"] = override_field
        else:
            payload["splunkbaseApps"] = splunkbase_apps or []
    path = cat_dir / f"UC-{uc_id}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def isolated_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """Redirect REPO_ROOT and CONTENT_DIR to tmp_path."""

    monkeypatch.setattr(splunkbase_coverage, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        splunkbase_coverage, "CONTENT_DIR", tmp_path / "content"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# _read_uc
# ---------------------------------------------------------------------------


class TestReadUc:
    def test_returns_parsed_dict(self, tmp_path: Path) -> None:
        path = tmp_path / "UC.json"
        path.write_text(json.dumps({"id": "1.1.1"}), encoding="utf-8")
        assert splunkbase_coverage._read_uc(path) == {"id": "1.1.1"}


# ---------------------------------------------------------------------------
# _structural_errors
# ---------------------------------------------------------------------------


class TestStructuralErrors:
    def test_well_formed_entry_has_no_errors(self) -> None:
        assert splunkbase_coverage._structural_errors([_good_entry()]) == []

    def test_non_dict_entry_is_reported(self) -> None:
        errs = splunkbase_coverage._structural_errors(["string-entry"])
        assert any("entry [0] is not an object" in e for e in errs)

    def test_missing_required_fields_reported(self) -> None:
        errs = splunkbase_coverage._structural_errors([
            {"id": 100}  # missing name and role
        ])
        assert any("missing required fields" in e for e in errs)
        assert any("'name'" in e and "'role'" in e for e in errs)

    def test_role_not_in_enum_reported(self) -> None:
        errs = splunkbase_coverage._structural_errors([
            _good_entry(role="not-in-enum")
        ])
        assert any("role='not-in-enum'" in e for e in errs)
        # The error message includes the sorted canonical roles.
        assert any("data-source" in e and "primary" in e for e in errs)

    def test_role_in_enum_passes(self) -> None:
        for role in splunkbase_coverage.CANONICAL_ROLES:
            assert (
                splunkbase_coverage._structural_errors([
                    _good_entry(role=role)
                ])
                == []
            )

    def test_url_not_splunkbase_prefix_reported(self) -> None:
        errs = splunkbase_coverage._structural_errors([
            _good_entry(url="https://wrong.example/app/100")
        ])
        assert any("not under splunkbase.splunk.com/app/" in e for e in errs)

    def test_url_non_string_reported(self) -> None:
        """A non-string url fails the ``isinstance(url, str)`` arm
        of the URL check (combined into the same error message)."""

        errs = splunkbase_coverage._structural_errors([
            _good_entry(url=12345)
        ])
        assert any("not under splunkbase.splunk.com/app/" in e for e in errs)

    def test_url_absent_is_silent(self) -> None:
        """Url is optional — absent url does not raise an error."""

        assert (
            splunkbase_coverage._structural_errors([_good_entry(url=None)])
            == []
        )

    def test_role_absent_skips_enum_check(self) -> None:
        """If role is missing the enum check is skipped (the missing
        field is already covered by the missing-required-fields
        check). This pins the ``entry.get("role")`` guard around
        the enum membership test."""

        errs = splunkbase_coverage._structural_errors([
            {"id": 1, "name": "n"}  # role absent
        ])
        # Reports missing required fields but does NOT add a
        # spurious 'role is not in' error.
        assert any("missing required fields" in e for e in errs)
        assert all("is not in" not in e for e in errs)

    def test_blank_string_field_treated_as_missing(self) -> None:
        """``entry.get(k)`` returns "" -> falsy -> field is treated
        as missing. This locks the ``not entry.get(k)`` guard."""

        errs = splunkbase_coverage._structural_errors([
            {"id": "", "name": "", "role": ""}
        ])
        assert any("missing required fields" in e for e in errs)


# ---------------------------------------------------------------------------
# _classify
# ---------------------------------------------------------------------------


class TestClassify:
    def test_missing_field_classified_missing(self) -> None:
        state, s, o, errs = splunkbase_coverage._classify({"id": "1.1.1"})
        assert state == "missing"
        assert s == 0
        assert o == 0
        assert errs == []

    def test_non_list_field_classified_missing(self) -> None:
        state, _s, _o, _e = splunkbase_coverage._classify(
            {"splunkbaseApps": "string"}
        )
        assert state == "missing"

    def test_empty_list_classified_missing(self) -> None:
        state, _s, _o, _e = splunkbase_coverage._classify(
            {"splunkbaseApps": []}
        )
        assert state == "missing"

    def test_structural_error_classified_broken(self) -> None:
        state, s, o, errs = splunkbase_coverage._classify(
            {"splunkbaseApps": [{"id": 1}]}  # missing name + role
        )
        assert state == "broken"
        assert s == 0
        assert o == 0
        assert errs  # non-empty

    def test_all_requires_sme_review_classified_open(self) -> None:
        state, s, o, _ = splunkbase_coverage._classify(
            {
                "splunkbaseApps": [
                    _good_entry(requires_sme_review=True),
                    _good_entry(app_id=200, requires_sme_review=True),
                ]
            }
        )
        assert state == "open"
        assert s == 0
        assert o == 2

    def test_none_requires_sme_review_classified_signed(self) -> None:
        state, s, o, _ = splunkbase_coverage._classify(
            {
                "splunkbaseApps": [
                    _good_entry(),  # no requiresSmeReview = signed
                    _good_entry(app_id=200, requires_sme_review=False),
                ]
            }
        )
        assert state == "signed"
        assert s == 2
        assert o == 0

    def test_mixed_signed_and_open_classified_partial(self) -> None:
        state, s, o, _ = splunkbase_coverage._classify(
            {
                "splunkbaseApps": [
                    _good_entry(),  # signed
                    _good_entry(app_id=200, requires_sme_review=True),
                ]
            }
        )
        assert state == "partial"
        assert s == 1
        assert o == 1


# ---------------------------------------------------------------------------
# _category_of
# ---------------------------------------------------------------------------


class TestCategoryOf:
    def test_returns_parent_dir_name(self, tmp_path: Path) -> None:
        cat_dir = tmp_path / "cat-05-foo"
        cat_dir.mkdir()
        path = cat_dir / "UC-5.1.1.json"
        path.touch()
        assert splunkbase_coverage._category_of(path) == "cat-05-foo"


# ---------------------------------------------------------------------------
# main — invocation errors
# ---------------------------------------------------------------------------


class TestMainInvocationErrors:
    def test_missing_content_dir_returns_2(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Missing content/ -> rc=2, stderr message."""

        rc = splunkbase_coverage.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "missing content dir" in err

    def test_unreadable_uc_returns_2(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Malformed UC sidecar aborts the run with rc=2."""

        (isolated_repo / "content" / "cat-01-foo").mkdir(parents=True)
        (isolated_repo / "content" / "cat-01-foo" / "UC-1.1.1.json").write_text(
            "{not json", encoding="utf-8"
        )
        rc = splunkbase_coverage.main([])
        assert rc == 2
        err = capsys.readouterr().err
        assert "UC-1.1.1.json" in err


# ---------------------------------------------------------------------------
# main — happy path / counts
# ---------------------------------------------------------------------------


class TestMainHappyPath:
    def test_empty_content_returns_0_with_zero_counts(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Empty content/ -> all counts 0, coverage 0.0%."""

        (isolated_repo / "content").mkdir()
        rc = splunkbase_coverage.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "total=0" in out
        assert "coverage=0.0%" in out

    def test_mixed_corpus_counts_are_correct(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """One signed UC + one open UC + one missing UC + one broken
        UC -> totals 4, signed 1, open 1, missing 1, broken 1,
        coverage 25.0% ((signed+partial)/total)."""

        content = isolated_repo / "content"
        _write_uc(
            content, uc_id="1.1.1", splunkbase_apps=[_good_entry()]
        )
        _write_uc(
            content,
            uc_id="1.1.2",
            splunkbase_apps=[_good_entry(requires_sme_review=True)],
        )
        _write_uc(content, uc_id="1.1.3", omit_field=True)
        _write_uc(
            content,
            uc_id="1.1.4",
            splunkbase_apps=[{"id": 1}],  # missing name + role
        )
        rc = splunkbase_coverage.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "total=4" in out
        assert "signed=1" in out
        assert "open=1" in out
        assert "missing=1" in out
        assert "broken=1" in out
        assert "coverage=25.0%" in out

    def test_partial_uc_counted_in_coverage(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A partial UC (some signed + some open) contributes to the
        coverage numerator alongside fully-signed ones."""

        content = isolated_repo / "content"
        _write_uc(
            content,
            uc_id="1.1.1",
            splunkbase_apps=[
                _good_entry(),
                _good_entry(app_id=200, requires_sme_review=True),
            ],
        )
        rc = splunkbase_coverage.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "partial=1" in out
        assert "coverage=100.0%" in out

    def test_strict_mode_with_only_signed_returns_0(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Strict mode succeeds when every UC is signed or partial."""

        content = isolated_repo / "content"
        _write_uc(
            content, uc_id="1.1.1", splunkbase_apps=[_good_entry()]
        )
        rc = splunkbase_coverage.main(["--strict"])
        assert rc == 0
        assert "STRICT FAIL" not in capsys.readouterr().err

    def test_broken_examples_logged_to_stderr_capped_at_5(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Broken UCs are listed (capped at 5) with their per-entry
        error details on stderr — independent of strict mode."""

        content = isolated_repo / "content"
        for i in range(7):
            _write_uc(
                content,
                uc_id=f"1.1.{i + 1}",
                splunkbase_apps=[{"id": 1}],  # missing fields
            )
        rc = splunkbase_coverage.main([])
        assert rc == 0
        err = capsys.readouterr().err
        broken_lines = [line for line in err.splitlines() if "BROKEN" in line]
        assert len(broken_lines) == 5
        assert "and 2 more broken UCs" in err

    def test_broken_examples_exactly_5_no_footer(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Exactly 5 broken examples -> NO overflow footer (covers
        False arm of > 5 branch)."""

        content = isolated_repo / "content"
        for i in range(5):
            _write_uc(
                content,
                uc_id=f"1.1.{i + 1}",
                splunkbase_apps=[{"id": 1}],
            )
        rc = splunkbase_coverage.main([])
        assert rc == 0
        err = capsys.readouterr().err
        assert "and " not in err


# ---------------------------------------------------------------------------
# main — strict mode failures (rc=1)
# ---------------------------------------------------------------------------


class TestMainStrictFailures:
    def test_strict_fails_on_open_uc(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Strict mode + an 'open' UC -> rc=1 + STRICT FAIL banner +
        per-UC listing."""

        content = isolated_repo / "content"
        _write_uc(
            content,
            uc_id="1.1.1",
            splunkbase_apps=[_good_entry(requires_sme_review=True)],
        )
        rc = splunkbase_coverage.main(["--strict"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "STRICT FAIL: 1 UCs" in err
        assert "UC-1.1.1.json" in err

    def test_strict_fails_on_missing_uc(
        self,
        isolated_repo: Path,
    ) -> None:
        """Strict mode + a 'missing' UC -> rc=1."""

        content = isolated_repo / "content"
        _write_uc(content, uc_id="1.1.1", omit_field=True)
        rc = splunkbase_coverage.main(["--strict"])
        assert rc == 1

    def test_strict_fails_on_broken_uc(
        self,
        isolated_repo: Path,
    ) -> None:
        """Strict mode + a 'broken' UC -> rc=1."""

        content = isolated_repo / "content"
        _write_uc(
            content, uc_id="1.1.1", splunkbase_apps=[{"id": 1}]
        )
        rc = splunkbase_coverage.main(["--strict"])
        assert rc == 1

    def test_strict_failing_list_capped_at_10(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When >10 UCs fail under strict mode, the per-UC list is
        truncated to 10 with an overflow footer."""

        content = isolated_repo / "content"
        for i in range(15):
            _write_uc(content, uc_id=f"1.1.{i + 1}", omit_field=True)
        rc = splunkbase_coverage.main(["--strict"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "STRICT FAIL: 15 UCs" in err
        assert "and 5 more" in err
        # Count per-UC bullet lines.
        uc_lines = [line for line in err.splitlines() if line.startswith("  - ")]
        assert len(uc_lines) == 10

    def test_strict_failing_list_exactly_10_no_footer(
        self,
        isolated_repo: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Exactly 10 failures -> no overflow footer (covers False
        arm of > 10 branch)."""

        content = isolated_repo / "content"
        for i in range(10):
            _write_uc(content, uc_id=f"1.1.{i + 1}", omit_field=True)
        rc = splunkbase_coverage.main(["--strict"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "STRICT FAIL: 10 UCs" in err
        # No "... and N more" footer at exactly 10.
        assert "... and " not in err

    def test_non_strict_mode_never_returns_1(
        self,
        isolated_repo: Path,
    ) -> None:
        """Without --strict, missing/open/broken UCs are tolerated
        (audit always returns 0 unless invocation/IO fails)."""

        content = isolated_repo / "content"
        _write_uc(content, uc_id="1.1.1", omit_field=True)
        _write_uc(
            content,
            uc_id="1.1.2",
            splunkbase_apps=[_good_entry(requires_sme_review=True)],
        )
        _write_uc(
            content, uc_id="1.1.3", splunkbase_apps=[{"id": 1}]
        )
        rc = splunkbase_coverage.main([])
        assert rc == 0


# ---------------------------------------------------------------------------
# main — --json output
# ---------------------------------------------------------------------------


class TestJsonOutput:
    def test_json_written_with_summary_and_categories(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """--json writes the documented schema: summary block +
        byCategory dict keyed by category name, each carrying its
        own coveragePct."""

        content = isolated_repo / "content"
        _write_uc(
            content,
            cat="cat-01-foo",
            uc_id="1.1.1",
            splunkbase_apps=[_good_entry()],
        )
        _write_uc(
            content,
            cat="cat-02-bar",
            uc_id="2.1.1",
            splunkbase_apps=[_good_entry(requires_sme_review=True)],
        )
        out_path = tmp_path / "reports" / "coverage.json"
        rc = splunkbase_coverage.main(["--json", str(out_path)])
        assert rc == 0
        assert out_path.exists()
        report = json.loads(out_path.read_text(encoding="utf-8"))
        assert report["summary"]["total"] == 2
        assert report["summary"]["signed"] == 1
        assert report["summary"]["open"] == 1
        assert report["summary"]["coveragePct"] == 50.0
        # Per-category breakdown.
        assert "cat-01-foo" in report["byCategory"]
        assert "cat-02-bar" in report["byCategory"]
        assert report["byCategory"]["cat-01-foo"]["coveragePct"] == 100.0
        assert report["byCategory"]["cat-02-bar"]["coveragePct"] == 0.0

    def test_json_parent_dir_created(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """``parents=True`` on the output mkdir means deeply nested
        targets work without pre-creation."""

        (isolated_repo / "content").mkdir()
        out_path = tmp_path / "a" / "b" / "c" / "out.json"
        rc = splunkbase_coverage.main(["--json", str(out_path)])
        assert rc == 0
        assert out_path.exists()

    def test_json_category_with_zero_total_uses_0_coverage(
        self,
        isolated_repo: Path,
        tmp_path: Path,
    ) -> None:
        """When the category total is 0 (impossible in practice but
        the ternary protects against ZeroDivisionError) coverage
        defaults to 0.0. We exercise the False arm of the per-
        category ``if vals["total"]`` branch via the empty content
        case where byCategory ends up empty."""

        (isolated_repo / "content").mkdir()
        out_path = tmp_path / "out.json"
        rc = splunkbase_coverage.main(["--json", str(out_path)])
        assert rc == 0
        report = json.loads(out_path.read_text(encoding="utf-8"))
        # byCategory is empty when no UCs exist.
        assert report["byCategory"] == {}
        assert report["summary"]["coveragePct"] == 0.0


# ---------------------------------------------------------------------------
# Module entrypoint
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_against_real_content(self) -> None:
        """Invoke ``python -m tools.audits.splunkbase_coverage``
        against the real ``content/`` tree without --strict. We
        accept any rc (0, 1, 2) because the corpus state is
        unknown — only the CLI invocation surface is pinned."""

        repo_root = Path(splunkbase_coverage.__file__).resolve().parents[2]
        if not (repo_root / "content").is_dir():
            pytest.skip("content/ tree not present")
        result = subprocess.run(
            [sys.executable, "-m", "tools.audits.splunkbase_coverage"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=120,
        )
        # Non-strict default never returns 1; rc=2 only on IO error.
        assert result.returncode == 0, (
            f"unexpected rc={result.returncode} "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "[splunkbase_coverage]" in result.stdout
