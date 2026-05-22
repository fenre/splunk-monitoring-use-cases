"""Unit-level coverage for ``tools/audits/schema_diff.py``.

``schema_diff`` enforces the schema-versioning contract documented in
``docs/schema-versioning.md`` § "CI enforcement". For every
``schemas/**/*.schema.json`` it loads the matching baseline copy from
a git tag (``git show <tag>:<path>``), classifies each difference
between baseline and head as ``additive``, ``breaking`` or
``metadata`` (silently ignored), and then cross-checks the change
class against the schema's ``version`` bump and ``x-stability``:

* a ``stable`` schema with a breaking change MUST carry a major
  version bump AND a fresh ``$id`` URL (so old consumers can keep
  resolving the old URL);
* any additive change must carry at least a minor bump (a patch-only
  bump on an additive change is a SemVer violation).

Before this commit the module had zero unit tests
(``Module tools.audits.schema_diff was never imported`` warning).

What this suite locks
---------------------

* ``_load_baseline`` returns None on ``CalledProcessError`` (tag
  missing), on ``FileNotFoundError`` (git not installed) and on
  ``JSONDecodeError`` (tag exists but file is garbage).
* ``_safe_load`` returns None on ``OSError`` and on
  ``JSONDecodeError``; returns the parsed dict on success.
* ``_semver_parts`` parses ``"1.2.3"`` -> ``(1,2,3)``;
  ``"1"`` -> ``(1,0,0)``; ``"1.2-rc1"`` -> ``(1,2,0)``;
  malformed input -> None.
* ``_bump_kind`` returns ``major`` / ``minor`` / ``patch`` /
  ``none`` / ``unknown`` for the documented cases.
* ``_classify`` / ``_walk`` recognise: added/removed properties,
  newly-required / dropped-required, enum additions / removals,
  type / $ref changes, minLength tightening, maxLength
  tightening, pattern changes. Recursion happens via the
  properties subtree.
* ``main`` returns ``2`` when the schemas dir is missing.
* ``main`` returns ``0`` with "N schema(s) checked. OK." when no
  breaking change exists.
* ``main`` returns ``0`` and SKIPs when ``_load_baseline`` returns
  None (covers the early-continue for first-release schemas).
* ``main`` returns ``0`` and SKIPs when ``_safe_load`` returns None
  (covers the head-unreadable branch).
* ``main`` returns ``0`` when a schema has only ``metadata`` changes
  (no additive / no breaking — continue).
* ``main`` returns ``1`` and lists the per-schema FAIL line when:
    - a stable schema breaks without a major version bump
    - a stable schema breaks without a fresh $id
    - an additive change ships with a patch-only bump
* ``main`` returns ``0`` (NOT 1) when a non-stable schema breaks
  even without a major bump (preview is allowed to break).
* The ``if __name__ == "__main__":`` guard is exercised by a
  subprocess smoke check against the real ``schemas/`` tree.

Run
---

``pytest tests/build/test_tools_audits_schema_diff.py``

Coverage check
--------------

``pytest tests/build/test_tools_audits_schema_diff.py \
    --cov=tools.audits.schema_diff --cov-branch``
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import tools.audits.schema_diff as schema_diff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stable_schema(
    *,
    version: str = "1.0.0",
    schema_id: str = "https://example.com/v1/foo.schema.json",
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    """A minimal valid head schema (stable, properties + required)."""

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": schema_id,
        "version": version,
        "x-stability": "stable",
        "x-since": "2026-01-01",
        "x-changelog": "schemas/changelogs/foo.md",
        "type": "object",
        "properties": properties or {"a": {"type": "string"}},
        "required": required or ["a"],
    }


def _write_schema(
    root: Path,
    *,
    name: str = "foo.schema.json",
    payload: dict[str, Any],
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# _load_baseline
# ---------------------------------------------------------------------------


class TestLoadBaseline:
    def test_called_process_error_returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``git show`` exits non-zero (tag absent) -> None."""

        def _explode(*_args, **_kwargs):
            raise subprocess.CalledProcessError(
                returncode=128, cmd=["git", "show"]
            )

        monkeypatch.setattr(subprocess, "check_output", _explode)
        assert schema_diff._load_baseline("vX", "schemas/foo.schema.json") is None

    def test_file_not_found_returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``git`` binary missing -> None."""

        def _no_git(*_args, **_kwargs):
            raise FileNotFoundError("no git")

        monkeypatch.setattr(subprocess, "check_output", _no_git)
        assert schema_diff._load_baseline("vX", "x") is None

    def test_invalid_json_returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``git show`` succeeds but returns garbage -> None
        (covers the JSONDecodeError ``return None`` branch)."""

        monkeypatch.setattr(
            subprocess, "check_output", lambda *a, **k: b"{not json"
        )
        assert schema_diff._load_baseline("vX", "x") is None

    def test_happy_path_returns_dict(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``git show`` returns valid JSON -> parsed dict."""

        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps({"x": 1}).encode("utf-8"),
        )
        assert schema_diff._load_baseline("vX", "x") == {"x": 1}


# ---------------------------------------------------------------------------
# _safe_load
# ---------------------------------------------------------------------------


class TestSafeLoad:
    def test_missing_path_returns_none(self, tmp_path: Path) -> None:
        """OSError from ``read_text`` -> None."""

        assert schema_diff._safe_load(tmp_path / "missing.json") is None

    def test_invalid_json_returns_none(self, tmp_path: Path) -> None:
        """Malformed JSON on disk -> None."""

        path = tmp_path / "x.json"
        path.write_text("{not json", encoding="utf-8")
        assert schema_diff._safe_load(path) is None

    def test_happy_path_returns_dict(self, tmp_path: Path) -> None:
        path = tmp_path / "x.json"
        path.write_text(json.dumps({"a": 1}), encoding="utf-8")
        assert schema_diff._safe_load(path) == {"a": 1}


# ---------------------------------------------------------------------------
# _semver_parts
# ---------------------------------------------------------------------------


class TestSemverParts:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("1.2.3", (1, 2, 3)),
            ("0.0.0", (0, 0, 0)),
            ("10.20.30", (10, 20, 30)),
            # Pre-release suffix is dropped (everything before the '-').
            ("2.3.4-rc1", (2, 3, 4)),
            # Missing segments default to zero.
            ("1", (1, 0, 0)),
            ("1.2", (1, 2, 0)),
        ],
    )
    def test_valid_inputs(
        self,
        raw: str,
        expected: tuple[int, int, int],
    ) -> None:
        assert schema_diff._semver_parts(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "not.a.version",
            "1.x.3",
        ],
    )
    def test_malformed_returns_none(self, raw: str) -> None:
        """ValueError / IndexError on parse -> None."""

        assert schema_diff._semver_parts(raw) is None


# ---------------------------------------------------------------------------
# _bump_kind
# ---------------------------------------------------------------------------


class TestBumpKind:
    @pytest.mark.parametrize(
        "old,new,expected",
        [
            ("1.0.0", "2.0.0", "major"),
            ("1.0.0", "1.1.0", "minor"),
            ("1.0.0", "1.0.1", "patch"),
            ("1.0.0", "1.0.0", "none"),
            # Higher major wins even if minor/patch decrease.
            ("1.5.5", "2.0.0", "major"),
            ("1.0.0", "1.2.0", "minor"),
        ],
    )
    def test_documented_bumps(
        self,
        old: str,
        new: str,
        expected: str,
    ) -> None:
        assert schema_diff._bump_kind(old, new) == expected

    def test_unparseable_old_returns_unknown(self) -> None:
        """Malformed ``old`` propagates as 'unknown'."""

        assert schema_diff._bump_kind("garbage", "1.0.0") == "unknown"

    def test_unparseable_new_returns_unknown(self) -> None:
        """Malformed ``new`` propagates as 'unknown'."""

        assert schema_diff._bump_kind("1.0.0", "garbage") == "unknown"


# ---------------------------------------------------------------------------
# _classify / _walk
# ---------------------------------------------------------------------------


class TestWalkAndClassify:
    def test_added_property_is_additive(self) -> None:
        baseline = {"properties": {"a": {"type": "string"}}}
        head = {
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            }
        }
        out = schema_diff._classify(baseline, head)
        assert any("added property $.properties.b" in c for c in out["additive"])
        assert out["breaking"] == []

    def test_removed_property_is_breaking(self) -> None:
        baseline = {
            "properties": {
                "a": {"type": "string"},
                "b": {"type": "string"},
            }
        }
        head = {"properties": {"a": {"type": "string"}}}
        out = schema_diff._classify(baseline, head)
        assert any(
            "removed property $.properties.b" in c for c in out["breaking"]
        )
        assert out["additive"] == []

    def test_newly_required_is_breaking(self) -> None:
        baseline = {
            "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
            "required": ["a"],
        }
        head = {
            "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
            "required": ["a", "b"],
        }
        out = schema_diff._classify(baseline, head)
        assert any("newly required" in c for c in out["breaking"])

    def test_dropped_required_is_breaking(self) -> None:
        baseline = {
            "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
            "required": ["a", "b"],
        }
        head = {
            "properties": {"a": {"type": "string"}, "b": {"type": "string"}},
            "required": ["a"],
        }
        out = schema_diff._classify(baseline, head)
        assert any("dropped from required" in c for c in out["breaking"])

    def test_enum_addition_is_additive(self) -> None:
        baseline = {"enum": ["a"]}
        head = {"enum": ["a", "b"]}
        out = schema_diff._classify(baseline, head)
        assert any("added value 'b'" in c for c in out["additive"])
        assert out["breaking"] == []

    def test_enum_removal_is_breaking(self) -> None:
        baseline = {"enum": ["a", "b"]}
        head = {"enum": ["a"]}
        out = schema_diff._classify(baseline, head)
        assert any("removed value 'b'" in c for c in out["breaking"])

    def test_enum_only_one_side_is_silent(self) -> None:
        """If either side lacks an ``enum`` we do NOT classify
        anything for that node (covers the ``if b_enum and h_enum``
        guard)."""

        baseline = {"enum": ["a"]}
        head = {"type": "string"}  # no enum
        out = schema_diff._classify(baseline, head)
        assert out["additive"] == []
        # The type-change branch may fire if both have a "type"
        # field, but enum drift alone is silent. Verify no enum-
        # related strings appear.
        assert all("enum" not in c for c in out["breaking"])

    def test_type_change_is_breaking(self) -> None:
        baseline = {"type": "string"}
        head = {"type": "integer"}
        out = schema_diff._classify(baseline, head)
        assert any("$.type changed" in c for c in out["breaking"])

    def test_ref_change_is_breaking(self) -> None:
        baseline = {"$ref": "#/$defs/A"}
        head = {"$ref": "#/$defs/B"}
        out = schema_diff._classify(baseline, head)
        assert any("$.$ref changed" in c for c in out["breaking"])

    def test_minlength_tightened_is_breaking(self) -> None:
        baseline = {"minLength": 1}
        head = {"minLength": 5}
        out = schema_diff._classify(baseline, head)
        assert any("$.minLength narrowed" in c for c in out["breaking"])

    def test_minlength_loosened_is_silent(self) -> None:
        """Lowering minLength is permissive — not classified."""

        baseline = {"minLength": 5}
        head = {"minLength": 1}
        out = schema_diff._classify(baseline, head)
        assert out["breaking"] == []

    def test_maxlength_tightened_is_breaking(self) -> None:
        baseline = {"maxLength": 100}
        head = {"maxLength": 50}
        out = schema_diff._classify(baseline, head)
        assert any("$.maxLength narrowed" in c for c in out["breaking"])

    def test_maxlength_loosened_is_silent(self) -> None:
        """Raising maxLength is permissive — not classified."""

        baseline = {"maxLength": 50}
        head = {"maxLength": 100}
        out = schema_diff._classify(baseline, head)
        assert out["breaking"] == []

    def test_pattern_change_is_breaking(self) -> None:
        baseline = {"pattern": "^a"}
        head = {"pattern": "^b"}
        out = schema_diff._classify(baseline, head)
        assert any("$.pattern changed" in c for c in out["breaking"])

    def test_pattern_only_one_side_is_silent(self) -> None:
        """Pattern added or removed (vs. changed) doesn't flow
        through the ``"pattern" in b and "pattern" in h`` AND-arm —
        verified by NO pattern-related breaking entry appearing."""

        baseline = {"pattern": "^a"}
        head: dict[str, Any] = {}
        out = schema_diff._classify(baseline, head)
        assert all("pattern" not in c for c in out["breaking"])

    def test_non_dict_nodes_are_silent(self) -> None:
        """When either side is not a dict (e.g. when the property
        is a scalar default value) ``_walk`` returns immediately."""

        out: dict[str, list[str]] = {"breaking": [], "additive": []}
        schema_diff._walk("$", "not-a-dict", {"a": 1}, out)
        assert out["breaking"] == []
        assert out["additive"] == []
        schema_diff._walk("$", {"a": 1}, ["list"], out)
        assert out["breaking"] == []
        assert out["additive"] == []

    def test_recursion_into_property_subtree(self) -> None:
        """Changes nested under ``properties.foo`` carry the
        documented dotted path in the change string."""

        baseline = {
            "properties": {"foo": {"type": "string"}}
        }
        head = {
            "properties": {"foo": {"type": "integer"}}
        }
        out = schema_diff._classify(baseline, head)
        assert any(
            "$.properties.foo.type changed" in c for c in out["breaking"]
        )

    def test_minlength_no_diff_is_silent(self) -> None:
        """Equal minLength values trigger no entry (covers
        the ``b[k] != h[k]`` short-circuit)."""

        baseline = {"minLength": 5}
        head = {"minLength": 5}
        out = schema_diff._classify(baseline, head)
        assert out["breaking"] == []


# ---------------------------------------------------------------------------
# main — invocation errors
# ---------------------------------------------------------------------------


class TestMainInvocation:
    def test_missing_schemas_dir_returns_2(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The ``--schemas`` path must exist; missing -> rc=2 +
        stderr message."""

        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(tmp_path / "missing")]
        )
        assert rc == 2
        err = capsys.readouterr().err
        assert "missing schemas dir" in err


# ---------------------------------------------------------------------------
# main — happy paths (rc=0)
# ---------------------------------------------------------------------------


class TestMainHappyPaths:
    def test_no_schemas_returns_0_with_zero_count(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Empty ``schemas/`` -> rc=0, "0 schema(s) checked"."""

        schemas = tmp_path / "schemas"
        schemas.mkdir()
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "0 schema(s) checked" in out

    def test_baseline_missing_skips_schema(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``_load_baseline`` returns None (e.g. first-release
        schema not in the baseline tag), the schema is SKIPped
        (no OK / no FAIL line) but the run still exits 0."""

        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=_stable_schema())

        def _no_baseline(*_a, **_k):
            raise subprocess.CalledProcessError(128, ["git", "show"])

        monkeypatch.setattr(subprocess, "check_output", _no_baseline)
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "1 schema(s) checked" in out

    def test_head_unreadable_skips_schema(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When ``_safe_load`` returns None on the head copy (e.g.
        malformed JSON), the schema is SKIPped and the audit
        continues."""

        schemas = tmp_path / "schemas"
        schemas.mkdir()
        # Write malformed JSON so _safe_load returns None.
        (schemas / "broken.schema.json").write_text(
            "{not json", encoding="utf-8"
        )
        # Baseline has to be present so we reach the ``head is
        # None`` continue rather than the baseline-None continue.
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(_stable_schema()).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "1 schema(s) checked" in out

    def test_no_change_returns_0_no_per_schema_output(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Identical baseline and head -> no classified changes ->
        no per-schema OK line, just the summary."""

        schemas = tmp_path / "schemas"
        head = _stable_schema()
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(head).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        # Summary present, per-schema OK line NOT (no changes -> continue).
        assert "1 schema(s) checked. OK." in out
        assert "OK   " not in out  # would imply per-schema OK with delta

    def test_metadata_only_change_is_silent(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Changes that don't surface as additive OR breaking (e.g.
        descriptions, title) -> no per-schema FAIL/OK line."""

        baseline = _stable_schema()
        head = _stable_schema()
        head["description"] = "added later"  # not classified by _walk
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "1 schema(s) checked. OK." in out

    def test_additive_with_minor_bump_emits_per_schema_ok(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A clean additive change with a minor bump -> per-schema OK
        line with the breaking/additive counts."""

        baseline = _stable_schema(version="1.0.0")
        head = _stable_schema(
            version="1.1.0",
            properties={
                "a": {"type": "string"},
                "b": {"type": "string"},
            },
        )
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "OK   " in out
        assert "0 breaking" in out
        assert "1 additive" in out
        assert "1.0.0 -> 1.1.0" in out

    def test_preview_schema_breaks_without_major_bump_is_allowed(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Preview schemas may break without a major bump — only
        ``x-stability: stable`` triggers the major-bump enforcement."""

        baseline = _stable_schema(
            properties={"a": {"type": "string"}, "b": {"type": "string"}}
        )
        head = _stable_schema(
            properties={"a": {"type": "string"}}  # removed b
        )
        head["x-stability"] = "preview"
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        # Breaking change present, but the audit still exits 0 and
        # emits the per-schema OK line because x-stability != stable.
        assert "OK   " in out


# ---------------------------------------------------------------------------
# main — breaking-change failures (rc=1)
# ---------------------------------------------------------------------------


class TestMainBreakingFailures:
    def test_stable_break_without_major_bump_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Removing a property on a stable schema with only a minor
        bump fails with both the no-major-bump and no-fresh-id
        problems."""

        baseline = _stable_schema(
            version="1.0.0",
            schema_id="https://example.com/v1/foo.schema.json",
            properties={"a": {"type": "string"}, "b": {"type": "string"}},
        )
        head = _stable_schema(
            version="1.1.0",  # minor bump only
            schema_id="https://example.com/v1/foo.schema.json",  # same $id
            properties={"a": {"type": "string"}},  # removed b
        )
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert "FAIL" in err
        assert "breaking change without major bump" in err
        assert "breaking change without fresh $id" in err
        # Breaking change detail listed (capped at 5).
        assert "removed property" in err
        # Footer advisory points at the contract doc.
        assert "docs/schema-versioning.md" in err

    def test_stable_break_with_major_bump_and_fresh_id_passes(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A clean stable break: major bump + fresh $id -> rc=0
        with the per-schema OK line."""

        baseline = _stable_schema(
            version="1.0.0",
            schema_id="https://example.com/v1/foo.schema.json",
            properties={"a": {"type": "string"}, "b": {"type": "string"}},
        )
        head = _stable_schema(
            version="2.0.0",  # major bump
            schema_id="https://example.com/v2/foo.schema.json",  # fresh $id
            properties={"a": {"type": "string"}},  # removed b
        )
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "OK   " in out

    def test_stable_break_with_major_but_stale_id_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Major bump but reused $id -> only the no-fresh-id problem
        fires (covers the bump != 'major' False arm)."""

        baseline = _stable_schema(
            version="1.0.0",
            schema_id="https://example.com/v1/foo.schema.json",
            properties={"a": {"type": "string"}, "b": {"type": "string"}},
        )
        head = _stable_schema(
            version="2.0.0",  # major
            schema_id="https://example.com/v1/foo.schema.json",  # NOT bumped
            properties={"a": {"type": "string"}},  # removed b
        )
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert "FAIL" in err
        assert "without fresh $id" in err
        # The no-major-bump line MUST NOT appear (bump WAS major).
        assert "without major bump" not in err

    def test_additive_with_patch_bump_only_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An additive change shipped with a patch bump only -> rc=1
        (SemVer requires at least a minor bump for additions)."""

        baseline = _stable_schema(
            version="1.0.0",
            properties={"a": {"type": "string"}},
        )
        head = _stable_schema(
            version="1.0.1",  # patch only
            properties={
                "a": {"type": "string"},
                "b": {"type": "string"},
            },
        )
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 1
        err = capsys.readouterr().err
        assert "FAIL" in err
        assert "additive change with patch bump only" in err
        assert "minor required" in err
        # Additive change detail listed (capped at 5).
        assert "+ additive:" in err

    def test_breaking_changes_truncated_at_5(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """When more than 5 breaking changes exist, only the first
        5 are listed in the FAIL output."""

        baseline_props = {
            f"prop{i}": {"type": "string"} for i in range(10)
        }
        baseline = _stable_schema(
            version="1.0.0", properties=baseline_props
        )
        head = _stable_schema(
            version="1.1.0", properties={}  # removed all 10
        )
        schemas = tmp_path / "schemas"
        _write_schema(schemas, payload=head)
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *a, **k: json.dumps(baseline).encode(),
        )
        rc = schema_diff.main(
            ["--baseline-tag", "vX", "--schemas", str(schemas)]
        )
        assert rc == 1
        err = capsys.readouterr().err
        # Count breaking-change detail lines (each starts with the
        # documented "! breaking:" prefix).
        breaking_lines = [
            line for line in err.splitlines() if "! breaking:" in line
        ]
        assert len(breaking_lines) == 5


# ---------------------------------------------------------------------------
# Module entrypoint guard
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_against_real_schemas_tree(self) -> None:
        """Invoke ``python -m tools.audits.schema_diff`` against the
        real repo schemas/ tree using a non-existent baseline tag.
        All schemas should SKIP (baseline missing) and the audit
        should exit 0. This pins the CLI contract from the
        docstring."""

        repo_root = Path(schema_diff.__file__).resolve().parents[2]
        schemas_dir = repo_root / "schemas"
        if not schemas_dir.is_dir():
            pytest.skip("schemas/ tree not present")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.audits.schema_diff",
                "--baseline-tag",
                "nonexistent-tag-for-coverage-smoke",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        # With a bogus tag every baseline lookup returns None so
        # every schema is SKIPped -> rc=0.
        assert result.returncode == 0, (
            f"unexpected rc={result.returncode} "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "schema(s) checked. OK." in result.stdout
