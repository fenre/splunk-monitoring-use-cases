"""Unit-level coverage for ``tools/validate/validate_md.py``.

The validator is the pre-build hard gate for the JSON SSOT under
``content/cat-NN-<slug>/UC-X.Y.Z.json`` (it replaces the v6 markdown
walker — see the module docstring and ``docs/migration-build-parity.md``
§ "Pre-build validation"). It is wired in via the
``no_use_cases_dir`` audit allowlist as the canonical active-code
successor to the legacy root-level ``validate_md.py``.

Despite that prominence, the module was at 0% coverage before this file
landed: no test ever imported it (coverage emits the explicit
``Module tools.validate.validate_md was never imported`` warning when
``--cov=tools.validate.validate_md`` is requested). This suite closes
the gap to 100% line + branch coverage by exercising every public
function and every branch of the built-in JSON-Schema fallback that
``_walk`` implements.

Hermetic strategy
-----------------

The module computes ``REPO_ROOT``, ``CONTENT_DIR`` and ``UC_SCHEMA`` at
import time relative to its own file. To keep tests deterministic and
free of dependencies on the real repo we monkeypatch those module
attributes per test. ``_check_uc_file`` and ``_check_category`` use
``Path.relative_to(REPO_ROOT)`` in every error string, so REPO_ROOT
must be a parent of the synthetic tree we build. All synthetic trees
are rooted at ``tmp_path``.

The schema fallback validator is exhaustively tested with hand-built
schema fragments — using the real ``schemas/uc.schema.json`` would
couple this suite to schema evolution and obscure which branch each
test exercises.

Both validator backends are exercised:

* ``_try_jsonschema_validator`` is asked to build a validator with
  ``jsonschema`` available (the typical case in CI), with
  Draft 2020-12 missing (forcing the Draft 7 fallback) and with
  ``jsonschema`` itself missing (forcing the built-in fallback).
* ``_builtin_validator`` is driven directly through every branch of
  ``_walk``.

Run
---

``pytest tests/build/test_tools_validate_validate_md.py``

Coverage check
--------------

``pytest tests/build/test_tools_validate_validate_md.py \
    --cov=tools.validate.validate_md --cov-branch``
"""
from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

# Importing the module by its canonical dotted path registers it with
# coverage under the name we pass via ``--cov``. The legacy
# ``importlib.util`` dance used elsewhere is unnecessary because
# ``tools/`` is already on ``sys.path`` via ``tests/build/conftest.py``.
import tools.validate.validate_md as validate_md


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


MINIMAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "title"],
    "properties": {
        "id": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        # ``minLength`` is intentionally 2 so the canonical "ok"
        # placeholder used throughout the fixture payloads passes the
        # real ``jsonschema`` backend (which DOES enforce minLength)
        # as well as the built-in fallback.
        "title": {"type": "string", "minLength": 2},
    },
}


def _write_schema(tmp_path: Path, schema: dict[str, Any] | str | None) -> Path:
    """Write a ``uc.schema.json`` under ``tmp_path/schemas`` and
    return its path. Pass a ``str`` to emit raw bytes (used for the
    malformed-JSON case)."""

    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_path = schema_dir / "uc.schema.json"
    if schema is None:
        return schema_path  # caller wants it missing
    if isinstance(schema, str):
        schema_path.write_text(schema, encoding="utf-8")
    else:
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
    return schema_path


def _patch_layout(
    monkeypatch: pytest.MonkeyPatch,
    *,
    repo_root: Path,
    content_dir: Path | None = None,
    schema_path: Path | None = None,
) -> None:
    """Repoint the module-level constants at the synthetic tree."""

    monkeypatch.setattr(validate_md, "REPO_ROOT", repo_root)
    monkeypatch.setattr(
        validate_md,
        "CONTENT_DIR",
        content_dir if content_dir is not None else repo_root / "content",
    )
    monkeypatch.setattr(
        validate_md,
        "UC_SCHEMA",
        schema_path
        if schema_path is not None
        else repo_root / "schemas" / "uc.schema.json",
    )


def _make_category(
    content_dir: Path,
    *,
    folder: str,
    meta: dict[str, Any] | None,
    ucs: dict[str, dict[str, Any] | str] | None = None,
) -> Path:
    """Create one ``content/cat-XX-slug/`` directory.

    ``ucs`` maps filename (e.g. ``UC-1.1.1.json``) to either a JSON
    payload (written with ``json.dumps``) or a raw string (written
    verbatim — used to exercise invalid-JSON branches)."""

    cat_dir = content_dir / folder
    cat_dir.mkdir(parents=True, exist_ok=True)
    if meta is not None:
        (cat_dir / "_category.json").write_text(
            json.dumps(meta), encoding="utf-8"
        )
    for filename, payload in (ucs or {}).items():
        path = cat_dir / filename
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload), encoding="utf-8")
    return cat_dir


# ---------------------------------------------------------------------------
# _load_schema
# ---------------------------------------------------------------------------


class TestLoadSchema:
    def test_returns_parsed_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
        _patch_layout(monkeypatch, repo_root=tmp_path, schema_path=schema_path)
        loaded = validate_md._load_schema()
        assert loaded == MINIMAL_SCHEMA

    def test_missing_file_raises_systemexit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(
            monkeypatch,
            repo_root=tmp_path,
            schema_path=tmp_path / "nope.json",
        )
        with pytest.raises(SystemExit) as excinfo:
            validate_md._load_schema()
        assert "FATAL: cannot read" in str(excinfo.value)

    def test_malformed_json_raises_systemexit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        schema_path = _write_schema(tmp_path, "{not json")
        _patch_layout(monkeypatch, repo_root=tmp_path, schema_path=schema_path)
        with pytest.raises(SystemExit) as excinfo:
            validate_md._load_schema()
        assert "FATAL: cannot read" in str(excinfo.value)


# ---------------------------------------------------------------------------
# _try_jsonschema_validator
# ---------------------------------------------------------------------------


class TestTryJsonschemaValidator:
    def test_returns_callable_when_available(self) -> None:
        # jsonschema is a transitive dev dep; if it isn't installed
        # in this environment the test simply asserts the documented
        # ``None`` fallback. Either branch is fine — both are exercised
        # explicitly in the dedicated tests below.
        result = validate_md._try_jsonschema_validator(MINIMAL_SCHEMA)
        if result is None:
            return
        errors = result({"id": "1.2.3", "title": "ok"})
        assert errors == []

    def test_returns_none_when_jsonschema_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force the ``import jsonschema`` line to fail. We use
        # builtins.__import__ rather than nuking ``sys.modules`` so
        # that the real module is restored after the test finishes.
        real_import = __builtins__["__import__"] if isinstance(
            __builtins__, dict
        ) else __builtins__.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "jsonschema":
                raise ImportError("forced for test")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr("builtins.__import__", fake_import)
        assert validate_md._try_jsonschema_validator(MINIMAL_SCHEMA) is None

    def test_falls_back_to_draft7_when_draft202012_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The nested ``from jsonschema import Draft202012Validator``
        line is the modern path; older ``jsonschema`` versions only
        ship ``Draft7Validator``. We simulate the older shape by
        stubbing the ``jsonschema`` module."""

        pytest.importorskip("jsonschema")

        class FakeValidator:
            def __init__(self, schema: dict[str, Any]) -> None:
                self.schema = schema

            def iter_errors(self, payload: dict[str, Any]):
                if "id" not in payload:
                    yield _FakeError("missing required property: id", ["id"])

        class _FakeError:
            def __init__(self, message: str, path: list[str]) -> None:
                self.message = message
                self.path = path

        # Stub the inner imports inside the function: the first
        # ``from jsonschema import Draft202012Validator`` raises,
        # the fallback ``from jsonschema import Draft7Validator`` wins.
        class _StubJsonschema:
            pass

        real_import = __builtins__["__import__"] if isinstance(
            __builtins__, dict
        ) else __builtins__.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "jsonschema":
                module = _StubJsonschema()
                if fromlist and "Draft202012Validator" in fromlist:
                    raise ImportError(
                        "Draft202012Validator missing — simulated older jsonschema"
                    )
                if fromlist and "Draft7Validator" in fromlist:
                    module.Draft7Validator = FakeValidator  # type: ignore[attr-defined]
                return module
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr("builtins.__import__", fake_import)
        validator = validate_md._try_jsonschema_validator(MINIMAL_SCHEMA)
        assert validator is not None
        errors = validator({})
        assert errors == ["id: missing required property: id"]

    def test_returns_none_when_both_validator_classes_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        class _StubJsonschema:
            pass

        real_import = __builtins__["__import__"] if isinstance(
            __builtins__, dict
        ) else __builtins__.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "jsonschema":
                if fromlist and (
                    "Draft202012Validator" in fromlist
                    or "Draft7Validator" in fromlist
                ):
                    raise ImportError("simulated empty jsonschema")
                return _StubJsonschema()
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr("builtins.__import__", fake_import)
        assert validate_md._try_jsonschema_validator(MINIMAL_SCHEMA) is None


# ---------------------------------------------------------------------------
# _type_matches
# ---------------------------------------------------------------------------


class TestTypeMatches:
    @pytest.mark.parametrize(
        "value, type_name, expected",
        [
            ({}, "object", True),
            ([], "array", True),
            ("x", "string", True),
            (5, "integer", True),
            (True, "integer", False),  # bool is NOT integer
            (3.14, "number", True),
            (5, "number", True),
            (True, "number", False),  # bool is NOT number
            (False, "boolean", True),
            (None, "null", True),
            ({}, "string", False),
            ([], "object", False),
            ("x", "integer", False),
            (5, "string", False),
            (1, "object", False),
            (None, "string", False),
            ("x", "anything-else", True),  # unknown type → permissive
        ],
    )
    def test_matrix(
        self, value: Any, type_name: str, expected: bool
    ) -> None:
        assert validate_md._type_matches(value, type_name) is expected


# ---------------------------------------------------------------------------
# _walk — built-in validator branches
# ---------------------------------------------------------------------------


def _validate_with(schema: dict[str, Any], payload: Any) -> list[str]:
    return validate_md._builtin_validator(schema)(payload)


class TestWalkOneOf:
    def test_exactly_one_match_passes(self) -> None:
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        assert _validate_with(schema, "hello") == []
        assert _validate_with(schema, 42) == []

    def test_zero_matches_fails(self) -> None:
        schema = {"oneOf": [{"type": "string"}, {"type": "integer"}]}
        errs = _validate_with(schema, [])
        assert len(errs) == 1
        assert "did not match exactly one schema in oneOf" in errs[0]
        assert "(0 matches)" in errs[0]

    def test_multiple_matches_fails(self) -> None:
        # ``5`` matches both ``integer`` and ``number``.
        schema = {"oneOf": [{"type": "integer"}, {"type": "number"}]}
        errs = _validate_with(schema, 5)
        assert "(2 matches)" in errs[0]

    def test_nested_path_appears_in_error(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "field": {
                    "oneOf": [{"type": "string"}, {"type": "integer"}]
                }
            },
        }
        errs = _validate_with(schema, {"field": []})
        assert errs == [
            "field: did not match exactly one schema in oneOf (0 matches)"
        ]


class TestWalkTypeAndEnum:
    def test_type_mismatch_at_root(self) -> None:
        errs = _validate_with({"type": "string"}, 42)
        assert errs == ["<root>: expected type 'string' but got int"]

    def test_type_mismatch_short_circuits_further_checks(self) -> None:
        # When the type is wrong, ``_walk`` returns immediately —
        # the ``minLength`` branch must NOT fire.
        schema = {"type": "string", "minLength": 99}
        errs = _validate_with(schema, 42)
        assert errs == ["<root>: expected type 'string' but got int"]

    def test_enum_reject(self) -> None:
        schema = {"type": "string", "enum": ["red", "blue"]}
        errs = _validate_with(schema, "green")
        assert errs == ["<root>: value 'green' is not one of ['red', 'blue']"]

    def test_enum_accept(self) -> None:
        schema = {"type": "string", "enum": ["red", "blue"]}
        assert _validate_with(schema, "red") == []


class TestWalkStrings:
    def test_min_length_violation(self) -> None:
        schema = {"type": "string", "minLength": 5}
        errs = _validate_with(schema, "no")
        assert errs == ["<root>: string length 2 < minLength 5"]

    def test_min_length_satisfied(self) -> None:
        assert _validate_with({"type": "string", "minLength": 2}, "ok") == []

    def test_pattern_match_passes(self) -> None:
        schema = {"type": "string", "pattern": r"^\d+$"}
        assert _validate_with(schema, "123") == []

    def test_pattern_mismatch_fails(self) -> None:
        schema = {"type": "string", "pattern": r"^\d+$"}
        errs = _validate_with(schema, "abc")
        assert errs == [
            "<root>: value 'abc' does not match pattern ^\\d+$"
        ]

    def test_invalid_pattern_is_silently_skipped(self) -> None:
        """A broken regex must not raise — it's silently ignored so
        an upstream typo in the schema cannot brick the whole gate."""

        schema = {"type": "string", "pattern": "[unbalanced"}
        # ``re.compile`` raises on this. ``_walk`` swallows it.
        assert _validate_with(schema, "anything") == []

    def test_format_uri_accepts_http_and_https(self) -> None:
        schema = {"type": "string", "format": "uri"}
        assert _validate_with(schema, "http://example.com") == []
        assert _validate_with(schema, "HTTPS://Example.com") == []  # case-insensitive

    def test_format_uri_rejects_other_schemes(self) -> None:
        schema = {"type": "string", "format": "uri"}
        errs = _validate_with(schema, "ftp://example.com")
        assert errs == ["<root>: value 'ftp://example.com' does not look like a URI"]

    def test_format_date_accepts_iso8601(self) -> None:
        schema = {"type": "string", "format": "date"}
        assert _validate_with(schema, "2026-05-19") == []

    def test_format_date_rejects_non_iso8601(self) -> None:
        schema = {"type": "string", "format": "date"}
        errs = _validate_with(schema, "5/19/2026")
        assert errs == ["<root>: value '5/19/2026' is not an ISO-8601 date"]

    def test_unknown_format_is_ignored(self) -> None:
        # The validator only knows ``uri`` and ``date`` — any other
        # ``format`` value must be accepted as-is.
        schema = {"type": "string", "format": "ipv6"}
        assert _validate_with(schema, "::1") == []


class TestWalkArrays:
    def test_min_items_violation(self) -> None:
        schema = {"type": "array", "minItems": 2}
        errs = _validate_with(schema, ["x"])
        assert errs == ["<root>: array length 1 < minItems 2"]

    def test_min_items_satisfied(self) -> None:
        assert _validate_with({"type": "array", "minItems": 1}, ["x"]) == []

    def test_unique_items_violation_reports_first_duplicate(self) -> None:
        schema = {"type": "array", "uniqueItems": True}
        errs = _validate_with(schema, ["a", "b", "a", "c"])
        # Only the first duplicate is reported (the ``break`` is there
        # to keep error spam manageable).
        assert errs == ["<root>: array contains duplicate item 'a'"]

    def test_unique_items_passes_for_distinct(self) -> None:
        schema = {"type": "array", "uniqueItems": True}
        assert _validate_with(schema, [1, 2, 3]) == []

    def test_items_schema_is_applied_to_every_index(self) -> None:
        schema = {"type": "array", "items": {"type": "string"}}
        errs = _validate_with(schema, ["ok", 5, True])
        assert errs == [
            "1: expected type 'string' but got int",
            "2: expected type 'string' but got bool",
        ]

    def test_items_schema_ignored_when_not_a_dict(self) -> None:
        # JSON-Schema 2020-12 allows ``items`` to be a list (tuple
        # validation). The fallback only handles the dict shape so a
        # list ``items`` must NOT raise — it's just ignored.
        schema = {"type": "array", "items": [{"type": "string"}]}
        assert _validate_with(schema, [42]) == []


class TestWalkObjects:
    def test_missing_required_property(self) -> None:
        schema = {
            "type": "object",
            "required": ["id", "title"],
            "properties": {"id": {"type": "string"}, "title": {"type": "string"}},
        }
        errs = _validate_with(schema, {"id": "x"})
        assert errs == ["<root>: missing required property 'title'"]

    def test_additional_property_rejected(self) -> None:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"id": {"type": "string"}},
        }
        errs = _validate_with(schema, {"id": "x", "stray": True})
        assert errs == ["<root>: additional property 'stray' not allowed"]

    def test_additional_property_allowed_when_flag_absent(self) -> None:
        schema = {
            "type": "object",
            "properties": {"id": {"type": "string"}},
        }
        # No ``additionalProperties: false`` → stray keys must pass.
        assert _validate_with(schema, {"id": "x", "stray": True}) == []

    def test_property_present_recurses_into_sub_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "kpi": {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                }
            },
        }
        errs = _validate_with(schema, {"kpi": {}})
        assert errs == ["kpi: missing required property 'name'"]

    def test_property_absent_is_not_checked(self) -> None:
        """Schema validation should only run on properties that are
        present in the payload — absent optional properties are not
        an error."""

        schema = {
            "type": "object",
            "properties": {"kpi": {"type": "object", "required": ["x"]}},
        }
        assert _validate_with(schema, {}) == []


# ---------------------------------------------------------------------------
# Tree walkers
# ---------------------------------------------------------------------------


class TestIterCategories:
    def test_returns_only_cat_dirs_sorted(self, tmp_path: Path) -> None:
        content = tmp_path / "content"
        content.mkdir()
        (content / "cat-02-zeta").mkdir()
        (content / "cat-01-alpha").mkdir()
        (content / "non-cat").mkdir()  # ignored
        (content / "cat-99.txt").write_text("ignored", encoding="utf-8")  # not a dir
        result = [p.name for p in validate_md._iter_categories(content)]
        assert result == ["cat-01-alpha", "cat-02-zeta"]


class TestReadJson:
    def test_happy_path(self, tmp_path: Path) -> None:
        path = tmp_path / "p.json"
        path.write_text(json.dumps({"a": 1}), encoding="utf-8")
        assert validate_md._read_json(path) == {"a": 1}

    def test_missing_returns_none(self, tmp_path: Path) -> None:
        assert validate_md._read_json(tmp_path / "missing.json") is None

    def test_malformed_returns_none(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not json", encoding="utf-8")
        assert validate_md._read_json(path) is None


# ---------------------------------------------------------------------------
# _check_uc_file
# ---------------------------------------------------------------------------


def _build_validator() -> Any:
    return validate_md._builtin_validator(MINIMAL_SCHEMA)


class TestCheckUcFile:
    def test_invalid_json_short_circuits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        uc_path = tmp_path / "UC-1.1.1.json"
        uc_path.write_text("{not json", encoding="utf-8")
        errors: list[str] = []
        validate_md._check_uc_file(uc_path, cat_id=1, validator=_build_validator(), errors=errors)
        assert errors == ["UC-1.1.1.json: invalid JSON"]

    def test_filename_pattern_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        uc_path = tmp_path / "UC-notvalid.json"
        uc_path.write_text(json.dumps({"id": "1.1.1", "title": "ok"}), encoding="utf-8")
        errors: list[str] = []
        validate_md._check_uc_file(
            uc_path, cat_id=1, validator=_build_validator(), errors=errors
        )
        assert errors == ["UC-notvalid.json: filename does not match UC-X.Y.Z.json"]

    def test_filename_id_does_not_match_payload_id(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        uc_path = tmp_path / "UC-1.1.1.json"
        uc_path.write_text(
            json.dumps({"id": "2.2.2", "title": "drift"}), encoding="utf-8"
        )
        errors: list[str] = []
        validate_md._check_uc_file(
            uc_path, cat_id=2, validator=_build_validator(), errors=errors
        )
        # Two errors expected: filename mismatch + cat mismatch is OK because cat_id=2 matches
        assert any(
            "filename id '1.1.1' != payload id '2.2.2'" in err for err in errors
        )

    def test_category_id_drift(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        uc_path = tmp_path / "UC-3.1.1.json"
        uc_path.write_text(
            json.dumps({"id": "3.1.1", "title": "ok"}), encoding="utf-8"
        )
        errors: list[str] = []
        validate_md._check_uc_file(
            uc_path, cat_id=99, validator=_build_validator(), errors=errors
        )
        assert any(
            "id starts with category '3' but parent _category.json declares cat id 99"
            in err
            for err in errors
        )

    def test_schema_errors_propagate_with_relative_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        uc_path = tmp_path / "UC-1.1.1.json"
        uc_path.write_text(
            json.dumps({"id": "1.1.1"}), encoding="utf-8"  # missing 'title'
        )
        errors: list[str] = []
        validate_md._check_uc_file(
            uc_path, cat_id=1, validator=_build_validator(), errors=errors
        )
        assert any("missing required property 'title'" in err for err in errors)
        # The relative path prefix must be applied to schema errors too.
        assert all(err.startswith("UC-1.1.1.json: ") for err in errors)

    def test_happy_path_records_no_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        uc_path = tmp_path / "UC-1.1.1.json"
        uc_path.write_text(
            json.dumps({"id": "1.1.1", "title": "ok"}), encoding="utf-8"
        )
        errors: list[str] = []
        validate_md._check_uc_file(
            uc_path, cat_id=1, validator=_build_validator(), errors=errors
        )
        assert errors == []

    def test_empty_payload_id_does_not_synthesise_cat_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When the payload ``id`` is missing or empty, the
        ``payload_cat`` short-circuit must skip the cat-id comparison
        (covers the ``if payload_cat`` False branch). The
        filename-vs-payload mismatch still fires, so that error is
        expected — but the cat-id mismatch must NOT appear."""

        _patch_layout(monkeypatch, repo_root=tmp_path)
        uc_path = tmp_path / "UC-1.1.1.json"
        uc_path.write_text(json.dumps({"title": "ok"}), encoding="utf-8")
        errors: list[str] = []
        validate_md._check_uc_file(
            uc_path, cat_id=99, validator=_build_validator(), errors=errors
        )
        joined = "\n".join(errors)
        assert "missing required property 'id'" in joined
        # Filename mismatch fires because payload id is "" not "1.1.1".
        assert "filename id '1.1.1' != payload id ''" in joined
        # But the cat-id drift error MUST NOT appear: payload_cat is "" → False.
        assert "starts with category" not in joined


# ---------------------------------------------------------------------------
# _check_category
# ---------------------------------------------------------------------------


class TestCheckCategory:
    def test_missing_category_meta(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        content = tmp_path / "content"
        content.mkdir()
        cat_dir = content / "cat-01-empty"
        cat_dir.mkdir()
        errors: list[str] = []
        count = validate_md._check_category(cat_dir, _build_validator(), errors)
        assert count == 0
        assert errors == ["content/cat-01-empty/: missing _category.json"]

    def test_invalid_category_meta_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        content = tmp_path / "content"
        content.mkdir()
        cat_dir = content / "cat-01-bad"
        cat_dir.mkdir()
        (cat_dir / "_category.json").write_text("{not json", encoding="utf-8")
        errors: list[str] = []
        count = validate_md._check_category(cat_dir, _build_validator(), errors)
        assert count == 0
        assert errors == ["content/cat-01-bad/_category.json: invalid JSON"]

    def test_category_id_not_integer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        content = tmp_path / "content"
        content.mkdir()
        _make_category(
            content,
            folder="cat-01-noint",
            meta={"id": "one", "name": "x", "slug": "y", "subcategories": []},
        )
        errors: list[str] = []
        count = validate_md._check_category(
            content / "cat-01-noint", _build_validator(), errors
        )
        assert count == 0
        assert errors == [
            "content/cat-01-noint/_category.json: 'id' must be an integer"
        ]

    def test_missing_required_meta_keys_each_reported(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        content = tmp_path / "content"
        content.mkdir()
        _make_category(
            content,
            folder="cat-01-partial",
            meta={"id": 1},  # missing name/slug/subcategories
        )
        errors: list[str] = []
        validate_md._check_category(
            content / "cat-01-partial", _build_validator(), errors
        )
        joined = "\n".join(errors)
        for key in ("name", "slug", "subcategories"):
            assert f"missing '{key}'" in joined

    def test_happy_path_counts_ucs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        content = tmp_path / "content"
        content.mkdir()
        _make_category(
            content,
            folder="cat-01-good",
            meta={"id": 1, "name": "x", "slug": "y", "subcategories": []},
            ucs={
                "UC-1.1.1.json": {"id": "1.1.1", "title": "ok"},
                "UC-1.1.2.json": {"id": "1.1.2", "title": "ok"},
            },
        )
        errors: list[str] = []
        count = validate_md._check_category(
            content / "cat-01-good", _build_validator(), errors
        )
        assert count == 2
        assert errors == []

    def test_uc_errors_collected_alongside_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_layout(monkeypatch, repo_root=tmp_path)
        content = tmp_path / "content"
        content.mkdir()
        _make_category(
            content,
            folder="cat-01-mixed",
            meta={"id": 1, "name": "x", "slug": "y", "subcategories": []},
            ucs={
                "UC-1.1.1.json": {"id": "1.1.1", "title": "ok"},
                "UC-1.1.2.json": {"id": "1.1.2"},  # missing title
            },
        )
        errors: list[str] = []
        count = validate_md._check_category(
            content / "cat-01-mixed", _build_validator(), errors
        )
        assert count == 2
        assert any("missing required property 'title'" in err for err in errors)


# ---------------------------------------------------------------------------
# _print_errors
# ---------------------------------------------------------------------------


class TestPrintErrors:
    def test_empty_prints_nothing(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        validate_md._print_errors([], 50)
        assert capsys.readouterr().out == ""

    def test_under_limit_prints_all(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        validate_md._print_errors(["a", "b", "c"], 50)
        out = capsys.readouterr().out
        assert out == "a\nb\nc\n"

    def test_over_limit_truncates_with_summary(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        validate_md._print_errors(["a", "b", "c", "d", "e"], 2)
        out = capsys.readouterr().out
        assert out.startswith("a\nb\n")
        assert "plus 3 more error(s)" in out

    def test_at_limit_does_not_print_summary(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        validate_md._print_errors(["a", "b"], 2)
        out = capsys.readouterr().out
        assert out == "a\nb\n"


# ---------------------------------------------------------------------------
# main — CLI orchestration
# ---------------------------------------------------------------------------


def _build_full_layout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Standard happy-path tree: one category with one valid UC."""

    schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
    content = tmp_path / "content"
    content.mkdir()
    _make_category(
        content,
        folder="cat-01-good",
        meta={"id": 1, "name": "x", "slug": "y", "subcategories": []},
        ucs={"UC-1.1.1.json": {"id": "1.1.1", "title": "ok"}},
    )
    _patch_layout(
        monkeypatch,
        repo_root=tmp_path,
        content_dir=content,
        schema_path=schema_path,
    )
    return content


class TestMainHappyPath:
    def test_walks_content_dir_when_no_paths(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _build_full_layout(tmp_path, monkeypatch)
        rc = validate_md.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "OK" in out
        assert "cat-01-good" in out
        assert "PASS: 1 use cases validated against" in out

    def test_explicit_paths_limit_validation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        content = _build_full_layout(tmp_path, monkeypatch)
        # Add a second category that we *don't* pass on the CLI: it
        # must not be validated.
        _make_category(
            content,
            folder="cat-02-other",
            meta={"id": 2, "name": "z", "slug": "z", "subcategories": []},
            ucs={"UC-2.1.1.json": {"id": "2.1.1", "title": "ok"}},
        )
        rc = validate_md.main([str(content / "cat-01-good")])
        assert rc == 0
        out = capsys.readouterr().out
        assert "cat-01-good" in out
        assert "cat-02-other" not in out

    def test_quiet_mode_suppresses_per_category_lines(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _build_full_layout(tmp_path, monkeypatch)
        rc = validate_md.main(["--quiet"])
        assert rc == 0
        out = capsys.readouterr().out
        # In quiet success mode, NOTHING is printed (no PASS banner).
        assert out == ""


class TestMainFailureModes:
    def test_missing_content_dir_returns_1(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
        _patch_layout(
            monkeypatch,
            repo_root=tmp_path,
            content_dir=tmp_path / "does-not-exist",
            schema_path=schema_path,
        )
        rc = validate_md.main([])
        assert rc == 1
        err = capsys.readouterr().err
        assert "FATAL:" in err
        assert "does not exist" in err

    def test_non_directory_target_reports_not_a_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
        bogus_file = tmp_path / "bogus.txt"
        bogus_file.write_text("x", encoding="utf-8")
        _patch_layout(
            monkeypatch,
            repo_root=tmp_path,
            content_dir=tmp_path / "content",
            schema_path=schema_path,
        )
        rc = validate_md.main([str(bogus_file)])
        assert rc == 1
        out = capsys.readouterr().out
        assert "not a directory" in out

    def test_invalid_uc_returns_1_and_lists_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
        content = tmp_path / "content"
        content.mkdir()
        _make_category(
            content,
            folder="cat-01-bad",
            meta={"id": 1, "name": "x", "slug": "y", "subcategories": []},
            ucs={"UC-1.1.1.json": {"id": "1.1.1"}},  # missing title
        )
        _patch_layout(
            monkeypatch,
            repo_root=tmp_path,
            content_dir=content,
            schema_path=schema_path,
        )
        rc = validate_md.main([])
        assert rc == 1
        out = capsys.readouterr().out
        assert "FAILED:" in out
        # Both backends mention the property name in different
        # wording ("missing required property 'title'" — built-in;
        # "'title' is a required property" — jsonschema). The
        # quoted property name is the stable invariant.
        assert "'title'" in out and (
            "required" in out or "missing" in out
        )

    def test_quiet_failure_reports_total_only(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
        content = tmp_path / "content"
        content.mkdir()
        _make_category(
            content,
            folder="cat-01-bad",
            meta={"id": 1, "name": "x", "slug": "y", "subcategories": []},
            ucs={"UC-1.1.1.json": {"id": "1.1.1"}},
        )
        _patch_layout(
            monkeypatch,
            repo_root=tmp_path,
            content_dir=content,
            schema_path=schema_path,
        )
        rc = validate_md.main(["--quiet"])
        assert rc == 1
        out = capsys.readouterr().out
        # Quiet failure prints exactly the FAILED summary, NOT the
        # individual error list.
        assert out.startswith("FAILED:")
        assert "missing required property" not in out

    def test_max_zero_means_unlimited(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
        content = tmp_path / "content"
        content.mkdir()
        # Three categories, each with one bad UC → three errors.
        for i in (1, 2, 3):
            _make_category(
                content,
                folder=f"cat-0{i}-bad",
                meta={
                    "id": i,
                    "name": "x",
                    "slug": "y",
                    "subcategories": [],
                },
                ucs={f"UC-{i}.1.1.json": {"id": f"{i}.1.1"}},  # missing title
            )
        _patch_layout(
            monkeypatch,
            repo_root=tmp_path,
            content_dir=content,
            schema_path=schema_path,
        )
        rc = validate_md.main(["--max=0"])
        assert rc == 1
        out = capsys.readouterr().out
        # All three errors should be printed (no "plus N more"
        # footer). The substring ``'title'`` is the stable invariant
        # across both validator backends.
        assert out.count("'title'") == 3
        assert "plus" not in out

    def test_max_truncates_overflow(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        schema_path = _write_schema(tmp_path, MINIMAL_SCHEMA)
        content = tmp_path / "content"
        content.mkdir()
        for i in (1, 2, 3):
            _make_category(
                content,
                folder=f"cat-0{i}-bad",
                meta={
                    "id": i,
                    "name": "x",
                    "slug": "y",
                    "subcategories": [],
                },
                ucs={f"UC-{i}.1.1.json": {"id": f"{i}.1.1"}},
            )
        _patch_layout(
            monkeypatch,
            repo_root=tmp_path,
            content_dir=content,
            schema_path=schema_path,
        )
        rc = validate_md.main(["--max=1"])
        assert rc == 1
        out = capsys.readouterr().out
        # Exactly one error line + truncation footer mentioning the
        # remaining two errors. ``'title'`` is the cross-backend
        # stable substring (see ``test_invalid_uc_returns_1_and_lists_errors``).
        assert out.count("'title'") == 1
        assert "plus 2 more error(s)" in out


# ---------------------------------------------------------------------------
# Module entrypoint guard — end-to-end smoke test against real content/
# ---------------------------------------------------------------------------


class TestModuleEntryPoint:
    def test_invoking_as_script_validates_real_content_tree(self) -> None:
        """Invoke ``python -m tools.validate.validate_md`` in a fresh
        subprocess against the *real* repo-rooted ``content/`` tree.

        This serves two purposes:

        1. It pins the CLI entry-point contract advertised in the
           module docstring and in ``docs/migration-build-parity.md``
           — the same command that ships in the pre-build pipeline.

        2. It cross-validates that the JSON SSOT under
           ``content/cat-NN-<slug>/`` is in a state where the
           validator returns ``0``. If a future change drifts a UC
           sidecar away from ``schemas/uc.schema.json``, the
           per-file CI ``audit-uc-structure`` gate fires first; this
           test is a backup smoke check at the validator surface.

        We use a subprocess (not ``runpy``) because the module is
        already imported in this test session, and ``runpy`` warns
        about that. The subprocess runs WITHOUT ``coverage``
        instrumentation, so it does not improve ``--cov`` numbers —
        coverage of the ``if __name__`` guard itself is already
        produced by the test-collection import. This test is
        deliberately lightweight: it limits validation to a single
        category to keep wall-clock time under one second."""

        import subprocess

        repo_root = Path(validate_md.__file__).resolve().parents[2]
        content_dir = repo_root / "content"
        if not content_dir.is_dir():
            pytest.skip("content/ tree not present in this checkout")

        # Pick the lexicographically first cat-* directory so the
        # test stays deterministic across reorderings of content/.
        cat_dirs = sorted(
            p for p in content_dir.iterdir()
            if p.is_dir() and p.name.startswith("cat-")
        )
        if not cat_dirs:
            pytest.skip("no cat-*/ directories under content/")
        first_cat = cat_dirs[0]

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.validate.validate_md",
                str(first_cat),
                "--quiet",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, (
            f"validator failed against {first_cat.name}: "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
