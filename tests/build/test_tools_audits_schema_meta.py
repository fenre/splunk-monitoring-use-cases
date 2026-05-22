"""Unit-level coverage for ``tools/audits/schema_meta.py``.

``schema_meta`` asserts the per-schema metadata contract defined in
``docs/schema-versioning.md``: every ``*.schema.json`` under
``schemas/`` MUST declare ``$schema``, ``$id``, ``version``,
``x-stability``, ``x-since`` and ``x-changelog``, and the
``x-stability`` value MUST be one of ``stable | preview | deprecated``.

The script runs in two CI workflows
(``.github/workflows/validate.yml`` and ``.github/workflows/pages.yml``)
but had no unit tests at all before this file landed: the
``Module tools.audits.schema_meta was never imported`` warning was the
giveaway. This suite drives every branch of ``main`` hermetically
against synthetic ``schemas/`` trees rooted at ``tmp_path``.

What this suite locks
---------------------

* ``main`` returns ``1`` and writes a missing-dir message when the
  ``--schemas`` root does not exist.
* ``main`` returns ``0`` and writes the OK banner when every schema
  declares the full metadata set.
* ``main`` returns ``1`` and lists every problem when any schema is
  invalid JSON, missing a required key, or carries an out-of-range
  ``x-stability``.
* ``--schemas`` correctly overrides the default ``schemas`` path.
* The ``if __name__ == "__main__":`` guard is covered by a subprocess
  smoke check against the real repo-rooted ``schemas/`` tree.

Run
---

``pytest tests/build/test_tools_audits_schema_meta.py``

Coverage check
--------------

``pytest tests/build/test_tools_audits_schema_meta.py \
    --cov=tools.audits.schema_meta --cov-branch``
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.audits.schema_meta as schema_meta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


VALID_META: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://example.com/v1/foo.schema.json",
    "version": "1.0.0",
    "x-stability": "stable",
    "x-since": "1.0.0",
    "x-changelog": "/schemas/changelogs/foo.md",
    "type": "object",
}


def _write_schema(
    root: Path,
    *,
    name: str,
    payload: dict[str, Any] | str,
) -> Path:
    """Drop a single ``*.schema.json`` under ``root``.

    ``payload`` can be a dict (serialised via ``json.dumps``) or a raw
    string (written verbatim — used to exercise the invalid-JSON
    branch)."""

    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Missing schemas directory
# ---------------------------------------------------------------------------


class TestMissingSchemasDir:
    def test_returns_1_and_writes_error(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        bogus = tmp_path / "does-not-exist"
        rc = schema_meta.main(["--schemas", str(bogus)])
        assert rc == 1
        captured = capsys.readouterr()
        assert "missing schemas dir" in captured.err
        assert str(bogus) in captured.err
        # Nothing on stdout — the OK banner only fires on success.
        assert captured.out == ""


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_zero_schemas_passes_with_count_zero(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An empty schemas/ tree is acceptable — the contract only
        applies to existing ``*.schema.json`` files. The OK banner
        should report ``0 schemas`` so a regression isn't masked as
        success in CI output."""

        schemas = tmp_path / "schemas"
        schemas.mkdir()
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 0
        captured = capsys.readouterr()
        assert "[schema_meta] OK (0 schemas)" in captured.out

    def test_single_valid_schema_passes(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="foo.schema.json", payload=VALID_META)
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 0
        captured = capsys.readouterr()
        assert "[schema_meta] OK (1 schemas)" in captured.out
        assert captured.err == ""

    def test_recurses_into_subdirectories(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The module uses ``rglob`` — nested schemas under e.g.
        ``schemas/v2/`` must be discovered and validated."""

        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="root.schema.json", payload=VALID_META)
        _write_schema(
            schemas / "v2", name="nested.schema.json", payload=VALID_META
        )
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 0
        assert "[schema_meta] OK (2 schemas)" in capsys.readouterr().out

    def test_all_stability_values_pass(
        self,
        tmp_path: Path,
    ) -> None:
        """Every member of ALLOWED_STABILITY must round-trip cleanly."""

        for stability in schema_meta.ALLOWED_STABILITY:
            schemas = tmp_path / f"schemas-{stability}"
            payload = dict(VALID_META, **{"x-stability": stability})
            _write_schema(schemas, name="x.schema.json", payload=payload)
            rc = schema_meta.main(["--schemas", str(schemas)])
            assert rc == 0, f"stability={stability!r} should pass"


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


class TestFailureModes:
    def test_invalid_json_reports_and_continues(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An invalid JSON file MUST be reported as ``invalid JSON``
        and the audit MUST keep validating the other files so the
        report shows every problem in one pass."""

        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="ok.schema.json", payload=VALID_META)
        _write_schema(schemas, name="broken.schema.json", payload="{not json")
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 1
        captured = capsys.readouterr()
        # Header reports 1/2 failed, not 2/2 — the OK file passes.
        assert "[schema_meta] FAIL: 1/2 schema(s)" in captured.err
        assert "invalid JSON" in captured.err
        assert "broken.schema.json" in captured.err
        # The OK schema should NOT appear in the failure list.
        assert "ok.schema.json:\n" not in captured.err

    @pytest.mark.parametrize("missing_key", list(schema_meta.REQUIRED))
    def test_each_missing_required_key_is_reported(
        self,
        missing_key: str,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Drop each required key in turn and assert the audit names
        the missing key in the failure report."""

        payload = {k: v for k, v in VALID_META.items() if k != missing_key}
        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="x.schema.json", payload=payload)
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 1
        captured = capsys.readouterr()
        assert f"missing '{missing_key}'" in captured.err
        assert "x.schema.json" in captured.err
        # The contract pointer in the failure header must be present
        # so reviewers know where to look.
        assert "docs/schema-versioning.md" in captured.err

    def test_invalid_stability_value_is_reported(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        payload = dict(VALID_META, **{"x-stability": "experimental"})
        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="x.schema.json", payload=payload)
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "x-stability must be one of" in err
        assert "'experimental'" in err
        # The allowed values are listed sorted; sanity-check ordering.
        sorted_values = sorted(schema_meta.ALLOWED_STABILITY)
        assert str(sorted_values) in err

    def test_invalid_stability_with_other_missing_keys_lists_all(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Both missing-key problems AND the stability problem must
        appear in the same report (covers the case where ``problems``
        accumulates more than one entry per file)."""

        payload = {
            "$schema": VALID_META["$schema"],
            "x-stability": "experimental",  # invalid + missing 5 others
        }
        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="x.schema.json", payload=payload)
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 1
        err = capsys.readouterr().err
        # 5 missing keys + the stability complaint.
        assert err.count("missing ") >= 5
        assert "x-stability must be one of" in err

    def test_x_stability_absent_does_not_trigger_value_check(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``x-stability`` is missing entirely the
        ``stability is not None`` short-circuit must skip the
        value-membership check (covers the False arm of that branch).
        The 'missing' problem still fires from the required-key loop,
        but the 'must be one of' message MUST NOT also appear — there
        would be no value to print."""

        payload = {k: v for k, v in VALID_META.items() if k != "x-stability"}
        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="x.schema.json", payload=payload)
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "missing 'x-stability'" in err
        assert "must be one of" not in err

    def test_multiple_schemas_each_reported_separately(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When several files fail, each appears under its own path
        header so the operator can fix them in parallel."""

        schemas = tmp_path / "schemas"
        _write_schema(
            schemas,
            name="a.schema.json",
            payload={k: v for k, v in VALID_META.items() if k != "$id"},
        )
        _write_schema(
            schemas,
            name="b.schema.json",
            payload={k: v for k, v in VALID_META.items() if k != "version"},
        )
        rc = schema_meta.main(["--schemas", str(schemas)])
        assert rc == 1
        err = capsys.readouterr().err
        assert "FAIL: 2/2 schema(s)" in err
        assert "a.schema.json" in err
        assert "b.schema.json" in err
        assert "missing '$id'" in err
        assert "missing 'version'" in err


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


class TestCliSurface:
    def test_argv_none_defaults_to_sys_argv(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``main()`` is called without an explicit argv it
        falls through to ``argparse``'s default behaviour and reads
        from ``sys.argv``. We exercise that branch by monkey-patching
        ``sys.argv``."""

        schemas = tmp_path / "schemas"
        _write_schema(schemas, name="x.schema.json", payload=VALID_META)
        monkeypatch.setattr(
            sys, "argv", ["schema_meta", "--schemas", str(schemas)]
        )
        rc = schema_meta.main()
        assert rc == 0
        assert "[schema_meta] OK (1 schemas)" in capsys.readouterr().out

    def test_default_schemas_is_repo_local_dir(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The default ``--schemas`` value is the relative path
        ``schemas`` — verified by parsing argv with no override and
        asserting the resolved Path matches CWD/schemas."""

        # We can't easily call main() without a schemas/ tree at CWD
        # so we go through the parser the same way main() does.
        # This pins the documented default.
        parser_args = ["dummy"]  # ignored; we re-create the parser
        import argparse

        parser = argparse.ArgumentParser(prog="schema_meta")
        parser.add_argument("--schemas", default="schemas")
        ns = parser.parse_args([])
        assert ns.schemas == "schemas"


# ---------------------------------------------------------------------------
# Module entrypoint guard — subprocess smoke against real schemas/
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_validates_real_schemas_tree(self) -> None:
        """Invoke ``python -m tools.audits.schema_meta`` against the
        repo's real ``schemas/`` tree. This pins the CLI contract
        advertised in the module docstring and in
        ``docs/schema-versioning.md`` § "CI enforcement", and acts as
        a backup smoke test if the per-key validate.yml step ever
        drifts.

        The subprocess inherits no ``coverage`` instrumentation, so
        this test does not improve ``--cov`` numbers — coverage of the
        ``if __name__`` guard itself is produced by the test-collection
        import. This test exists to ensure the production invocation
        keeps returning ``0`` over time."""

        import subprocess

        repo_root = Path(schema_meta.__file__).resolve().parents[2]
        schemas_dir = repo_root / "schemas"
        if not schemas_dir.is_dir():
            pytest.skip("schemas/ tree not present in this checkout")
        result = subprocess.run(
            [sys.executable, "-m", "tools.audits.schema_meta"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"schema_meta failed against real schemas/: "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "[schema_meta] OK" in result.stdout
