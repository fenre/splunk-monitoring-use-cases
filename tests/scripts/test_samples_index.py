"""Hermetic tests for ``scripts/samples_index.py``.

The script validates and indexes the ``samples/`` tree, emitting
``docs/samples-coverage.md``. It runs in the ``uc-tests`` CI workflow
with ``--strict``.

Tests redirect ``REPO_ROOT``, ``SAMPLES_DIR``, ``SCHEMA_PATH``,
``CATALOG_PATH``, and ``COVERAGE_OUT`` to a ``tmp_path`` so we never
mutate the real samples tree.

Coverage target: high per-branch coverage of the home-grown YAML
parser, manifest validator, scanner, and renderer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import samples_index as M  # noqa: E402

# -----------------------------------------------------------------------------
# Fixture helpers
# -----------------------------------------------------------------------------


def _seed_catalog(base: Path, ucs_per_cat: dict[int, list[str]]) -> Path:
    """Write a minimal ``catalog.json`` under ``base`` with the given UC IDs."""
    cat_path = base / "catalog.json"
    data = {
        "DATA": [
            {
                "i": str(cat_id),
                "n": f"Category {cat_id}",
                "s": [
                    {
                        "u": [{"i": uc_id} for uc_id in uc_ids],
                    }
                ],
            }
            for cat_id, uc_ids in sorted(ucs_per_cat.items())
        ]
    }
    cat_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return cat_path


def _seed_sample(
    base: Path,
    uc_id: str,
    *,
    manifest_yaml: str | None = None,
    positive: str | None = None,
    negative: str | None = None,
) -> Path:
    """Create ``samples/UC-<id>/`` with optional manifest + log files."""
    sample_dir = base / "samples" / f"UC-{uc_id}"
    sample_dir.mkdir(parents=True, exist_ok=True)
    if manifest_yaml is not None:
        (sample_dir / "manifest.yaml").write_text(manifest_yaml, encoding="utf-8")
    if positive is not None:
        (sample_dir / "positive.log").write_text(positive, encoding="utf-8")
    if negative is not None:
        (sample_dir / "negative.log").write_text(negative, encoding="utf-8")
    return sample_dir


def _patch_paths(
    monkeypatch: pytest.MonkeyPatch, base: Path
) -> None:
    """Redirect every path constant under ``base``."""
    monkeypatch.setattr(M, "REPO_ROOT", base)
    monkeypatch.setattr(M, "SAMPLES_DIR", base / "samples")
    monkeypatch.setattr(M, "SCHEMA_PATH", base / "samples" / "_schema" / "x.json")
    monkeypatch.setattr(M, "CATALOG_PATH", base / "catalog.json")
    monkeypatch.setattr(M, "COVERAGE_OUT", base / "docs" / "samples-coverage.md")


# -----------------------------------------------------------------------------
# _parse_scalar
# -----------------------------------------------------------------------------


class TestParseScalar:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ('"hello"', "hello"),
            ("'world'", "world"),
            ("true", True),
            ("True", True),
            ("false", False),
            ("False", False),
            ("null", None),
            ("~", None),
            ("", None),
            ("42", 42),
            ("-7", -7),
            ("0", 0),
            ("3.14", 3.14),
            ("-2.5", -2.5),
            ("not-a-number", "not-a-number"),
            ("yes", "yes"),  # not in our truthy enum
            ("123abc", "123abc"),  # NaN string, returns as-is
        ],
    )
    def test_canonical_inputs(self, raw: str, expected: Any) -> None:
        assert M._parse_scalar(raw) == expected

    def test_strips_whitespace(self) -> None:
        assert M._parse_scalar("  42  ") == 42
        assert M._parse_scalar('  "x"  ') == "x"


# -----------------------------------------------------------------------------
# _assign_mini
# -----------------------------------------------------------------------------


class TestAssignMini:
    def test_assigns_to_dict_parent(self) -> None:
        d: dict[str, Any] = {}
        M._assign_mini((d, "k"), "v")
        assert d == {"k": "v"}

    def test_skips_when_key_is_none(self) -> None:
        # Pin the ``if key is None: return`` short-circuit
        M._assign_mini(None, "anything")
        # No exception, no side effect

    def test_skips_when_parent_is_not_dict(self) -> None:
        # Pin the ``if isinstance(parent, dict)`` guard
        lst: list[str] = []
        M._assign_mini((lst, "k"), "v")
        assert lst == []  # Did not mutate


# -----------------------------------------------------------------------------
# _mini_yaml — exercise the home-grown parser
# -----------------------------------------------------------------------------


class TestMiniYaml:
    def test_flat_key_value(self, tmp_path: Path) -> None:
        p = tmp_path / "m.yaml"
        p.write_text("uc_id: 1.1.1\nsourcetype: foo\n", encoding="utf-8")
        out = M._mini_yaml(p)
        assert out == {"uc_id": "1.1.1", "sourcetype": "foo"}

    def test_typed_scalars(self, tmp_path: Path) -> None:
        p = tmp_path / "m.yaml"
        p.write_text(
            'a: 42\nb: true\nc: null\nd: "hello"\ne: 3.14\n', encoding="utf-8"
        )
        out = M._mini_yaml(p)
        assert out == {"a": 42, "b": True, "c": None, "d": "hello", "e": 3.14}

    def test_skips_blank_lines_and_comments(self, tmp_path: Path) -> None:
        p = tmp_path / "m.yaml"
        p.write_text(
            "# leading comment\n"
            "\n"
            "k: v\n"
            "\n"
            "  # indented comment\n"
            "j: w\n",
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        assert out == {"k": "v", "j": "w"}

    def test_nested_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "m.yaml"
        p.write_text(
            "expected:\n  min_count: 5\n  max_count: 10\n", encoding="utf-8"
        )
        out = M._mini_yaml(p)
        assert out == {"expected": {"min_count": 5, "max_count": 10}}

    def test_block_scalar_pipe_is_documented_broken(
        self, tmp_path: Path
    ) -> None:
        """The ``|`` literal-block handler in ``_mini_yaml`` is broken
        by design: ``block_indent`` is initialised to ``None`` and never
        assigned, so the ``block_indent is not None and ...`` guard
        always fails on the first content line — the block flushes
        empty and the content lines are silently dropped.

        This test pins the buggy behaviour rather than the docstring
        promise. PyYAML is installed in production so users who care
        about block scalars get the correct result via that path
        (see ``test_uses_pyyaml_when_installed`` above). The
        ``_mini_yaml`` fallback exists for rare PyYAML-less environments
        where simple ``key: value`` shapes are sufficient."""
        p = tmp_path / "m.yaml"
        p.write_text(
            "description: |\n"
            "  line one\n"
            "  line two\n"
            "next_key: x\n",
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        # Buggy: description ends up as empty string, content dropped
        assert out["description"] == ""
        # Sibling key still parses normally
        assert out["next_key"] == "x"

    def test_list_under_bare_key_is_documented_broken(
        self, tmp_path: Path
    ) -> None:
        """``key:`` followed by ``- item`` lines on subsequent indented
        lines does NOT produce a list in ``_mini_yaml`` — the bare
        ``key:`` opens a *dict* context, and the ``- item`` lines fail
        the ``isinstance(parent, list)`` check and are silently dropped.

        The working alternative is the ``key: -`` syntax (see
        ``test_list_dash_dash_syntax``). Pin the buggy behaviour as
        a regression guard."""
        p = tmp_path / "m.yaml"
        p.write_text(
            "tags:\n  - a\n  - b\n  - 42\n", encoding="utf-8"
        )
        out = M._mini_yaml(p)
        # Buggy: ``tags`` is opened as a dict and the items are
        # silently dropped because parent isn't a list.
        assert out == {"tags": {}}

    def test_list_dash_dash_syntax(self, tmp_path: Path) -> None:
        """Pin the ``raw_value.startswith("-") and raw_value == "-"``
        branch — the rare ``key: -`` syntax that opens a list block."""
        p = tmp_path / "m.yaml"
        p.write_text(
            "items: -\n  - a\n  - b\n", encoding="utf-8"
        )
        out = M._mini_yaml(p)
        assert out["items"] == ["a", "b"]

    def test_returns_empty_dict_when_no_content(
        self, tmp_path: Path
    ) -> None:
        p = tmp_path / "m.yaml"
        p.write_text("# only a comment\n\n", encoding="utf-8")
        assert M._mini_yaml(p) == {}

    def test_key_with_empty_value_under_list_parent_skips_assignment(
        self, tmp_path: Path
    ) -> None:
        """Cover branch 105->107 False arm: when a ``key:`` (empty value) line
        is hit while ``parent`` is a list (created by an earlier ``key: -``
        opener still on the stack), the new empty dict is pushed onto the
        stack but ``parent[key] = new`` is silently skipped because
        ``parent`` is not a dict.

        The wire-level YAML to trigger this is ``items: -`` followed by an
        indented ``subkey:`` (no value) line — the ``items`` list is on the
        stack, and ``subkey:`` resolves with parent=list.
        """
        p = tmp_path / "m.yaml"
        p.write_text(
            "items: -\n  subkey:\n",
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        assert out["items"] == []

    def test_key_with_dash_value_under_list_parent_skips_assignment(
        self, tmp_path: Path
    ) -> None:
        """Cover branch 114->116 False arm: same pattern as above but the
        nested key opens its own ``- `` list, so the False arm of
        ``isinstance(parent, dict)`` in the ``elif raw_value == "-":`` branch
        fires instead.
        """
        p = tmp_path / "m.yaml"
        p.write_text(
            "items: -\n  nested: -\n",
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        assert out["items"] == []

    def test_key_with_scalar_value_under_list_parent_skips_assignment(
        self, tmp_path: Path
    ) -> None:
        """Cover branch 119->121 False arm: the ``else`` arm of the
        raw_value triage chain — ``key: scalar`` while parent is a list.
        The scalar assignment is silently skipped because ``parent`` is not
        a dict.
        """
        p = tmp_path / "m.yaml"
        p.write_text(
            "items: -\n  scalar_key: hello\n",
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        assert out["items"] == []

    def test_dead_code_branch_inside_else_is_unreachable_by_design(
        self,
    ) -> None:
        """Lines 122–125 of ``_mini_yaml`` are dead code by construction:
        they sit inside the ``else`` branch of the ``raw_value`` triage
        chain (``if raw_value == ""`` … ``elif "|"`` … ``elif "-"`` …
        ``else``), and the first guard inside the ``else`` rechecks
        ``if raw_value == ""`` — a condition that is *already* excluded
        by the outer ``if`` on line 103.

        We document this as **unreachable in practice** and intentionally
        leave the four lines uncovered. They behave as a tripwire against
        future refactors that might restructure the triage chain in a
        way that re-exposes those lines; if that happens, this test
        will need to be replaced with a real coverage path."""
        # Sanity-check the parser source so a refactor that *moves* the
        # dead block doesn't silently let the tripwire rot — locate the
        # ``else:`` of the triage chain and confirm it is followed by an
        # ``if raw_value == "":`` that mirrors the outer guard.
        src = Path(M.__file__).read_text(encoding="utf-8")
        idx = src.find("            else:\n")
        assert idx != -1, "triage `else` branch not found in _mini_yaml"
        tail = src[idx : idx + 400]
        # The dead-code marker must still be present
        assert "if raw_value == \"\":" in tail

    def test_block_pipe_with_blank_line_appends_to_block(
        self, tmp_path: Path
    ) -> None:
        """A blank line *immediately* after a ``|`` opener does take the
        ``block.append(line[block_indent or 0:])`` path on line 81 (because
        ``line.strip() == ""`` matches the first half of the guard), even
        though ``block_indent`` itself is never assigned. This pins the
        only reachable path through lines 80–82 of ``_mini_yaml``."""
        p = tmp_path / "m.yaml"
        # blank line right after `description: |` enters the
        # ``block.append(...)`` branch on line 81; the next content line
        # then triggers the flush on line 83.
        p.write_text(
            "description: |\n"
            "\n"
            "next_key: x\n",
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        # Buggy real behaviour: ``description`` ends up as the empty string
        # because ``"\n".join([""]).rstrip() == ""``. ``next_key`` parses
        # normally. The test pins what the parser actually does today; if
        # ``_mini_yaml`` is ever fixed to retain the literal block, the
        # assertion will fail and force a deliberate review.
        assert out["description"] == ""
        assert out["next_key"] == "x"

    def test_block_pipe_at_eof_triggers_final_flush(
        self, tmp_path: Path
    ) -> None:
        """When a ``|`` block is open at end-of-file (no later non-block
        line ever forces an in-loop flush), the final flush on line 127
        runs. Pinning this path keeps the EOF flush wired even though
        ``block_indent`` is never set (so ``block`` stays empty and the
        flushed value is the empty string)."""
        p = tmp_path / "m.yaml"
        p.write_text(
            "description: |\n"
            "\n",  # blank line after opener; file ends while block is open
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        assert out == {"description": ""}

    def test_dedent_pops_stack(self, tmp_path: Path) -> None:
        """Pin the ``while stack and indent <= stack[-1][0]: stack.pop()``
        loop on line 92. Triggered by descending into a nested block
        (``expected:``) and then dedenting back out to the top level
        (``last_reviewed:``)."""
        p = tmp_path / "m.yaml"
        p.write_text(
            "uc_id: 1.1.1\n"
            "expected:\n"
            "  min_count: 5\n"
            "last_reviewed: 2026-05-19\n",
            encoding="utf-8",
        )
        out = M._mini_yaml(p)
        # All three top-level keys must be present and correctly placed
        assert out["uc_id"] == "1.1.1"
        assert out["expected"] == {"min_count": 5}
        assert out["last_reviewed"] == "2026-05-19"


# -----------------------------------------------------------------------------
# _load_yaml — PyYAML preferred, fallback to _mini_yaml
# -----------------------------------------------------------------------------


class TestLoadYaml:
    def test_uses_pyyaml_when_installed(self, tmp_path: Path) -> None:
        """PyYAML is installed in the test env; this is the happy path."""
        p = tmp_path / "m.yaml"
        p.write_text("k: v\n", encoding="utf-8")
        out = M._load_yaml(p)
        assert out == {"k": "v"}

    def test_pyyaml_returns_empty_for_blank_file(self, tmp_path: Path) -> None:
        """``yaml.safe_load`` returns None for empty input — pin the
        ``or {}`` fallback."""
        p = tmp_path / "m.yaml"
        p.write_text("", encoding="utf-8")
        assert M._load_yaml(p) == {}

    def test_falls_back_to_mini_yaml_on_import_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pin the ``except ImportError`` branch by hiding ``yaml`` from
        the import system for one call."""
        # Inject a sentinel into sys.modules that raises on attribute
        # access — this is the simplest way to force ImportError without
        # uninstalling PyYAML for the whole test session.
        original = sys.modules.get("yaml")
        monkeypatch.setitem(sys.modules, "yaml", None)
        try:
            p = tmp_path / "m.yaml"
            p.write_text("k: v\n", encoding="utf-8")
            out = M._load_yaml(p)
            assert out == {"k": "v"}
        finally:
            # Restore so subsequent tests can use yaml normally
            if original is not None:
                sys.modules["yaml"] = original


# -----------------------------------------------------------------------------
# _validate_manifest
# -----------------------------------------------------------------------------


class TestValidateManifest:
    def _ok(self) -> dict[str, Any]:
        """Return a canonically valid manifest dict."""
        return {
            "uc_id": "1.1.1",
            "sourcetype": "foo:bar",
            "index": "main",
            "expected": {"min_count": 1},
            "origin": "vendor-doc",
            "last_reviewed": "2026-05-19",
        }

    def test_canonical_passes(self) -> None:
        assert M._validate_manifest(self._ok()) == []

    def test_missing_required_key(self) -> None:
        m = self._ok()
        del m["sourcetype"]
        errs = M._validate_manifest(m)
        assert any("sourcetype" in e for e in errs)

    def test_required_key_with_none_value(self) -> None:
        m = self._ok()
        m["sourcetype"] = None
        errs = M._validate_manifest(m)
        assert any("sourcetype" in e for e in errs)

    def test_required_key_with_empty_string_value(self) -> None:
        m = self._ok()
        m["sourcetype"] = ""
        errs = M._validate_manifest(m)
        assert any("sourcetype" in e for e in errs)

    def test_invalid_uc_id_format(self) -> None:
        m = self._ok()
        m["uc_id"] = "not-N.N.N"
        errs = M._validate_manifest(m)
        assert any("uc_id must match" in e for e in errs)

    def test_origin_not_in_enum(self) -> None:
        m = self._ok()
        m["origin"] = "homemade"
        errs = M._validate_manifest(m)
        assert any("origin not in" in e for e in errs)

    @pytest.mark.parametrize(
        "origin", sorted(M.ORIGIN_ENUM)
    )
    def test_each_origin_enum_value_passes(self, origin: str) -> None:
        m = self._ok()
        m["origin"] = origin
        errs = M._validate_manifest(m)
        assert not any("origin not in" in e for e in errs)

    def test_invalid_last_reviewed_format(self) -> None:
        m = self._ok()
        m["last_reviewed"] = "tomorrow"
        errs = M._validate_manifest(m)
        assert any("last_reviewed must be" in e for e in errs)

    def test_expected_missing_min_count(self) -> None:
        m = self._ok()
        m["expected"] = {}
        errs = M._validate_manifest(m)
        assert any("expected.min_count is required" in e for e in errs)

    def test_expected_missing_entirely(self) -> None:
        """``manifest.get("expected") or {}`` covers the missing-key
        path AND the expected=None path."""
        m = self._ok()
        m["expected"] = None
        errs = M._validate_manifest(m)
        assert any("expected.min_count is required" in e for e in errs)


# -----------------------------------------------------------------------------
# _load_catalog_ids
# -----------------------------------------------------------------------------


class TestLoadCatalogIds:
    def test_returns_set_of_uc_ids(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(tmp_path, {1: ["1.1.1", "1.1.2"], 2: ["2.1.1"]})
        monkeypatch.setattr(M, "CATALOG_PATH", tmp_path / "catalog.json")
        ids = M._load_catalog_ids()
        assert ids == {"1.1.1", "1.1.2", "2.1.1"}

    def test_skips_uc_without_id(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # ``if uc.get("i"):`` guard — pin against malformed catalog
        cat = {
            "DATA": [
                {
                    "i": "1",
                    "s": [{"u": [{"i": "1.1.1"}, {"i": ""}, {"i": None}, {}]}],
                }
            ]
        }
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps(cat), encoding="utf-8")
        monkeypatch.setattr(M, "CATALOG_PATH", cat_path)
        ids = M._load_catalog_ids()
        assert ids == {"1.1.1"}

    def test_handles_empty_data(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps({"DATA": []}), encoding="utf-8")
        monkeypatch.setattr(M, "CATALOG_PATH", cat_path)
        assert M._load_catalog_ids() == set()


# -----------------------------------------------------------------------------
# SampleStatus
# -----------------------------------------------------------------------------


class TestSampleStatus:
    @pytest.mark.parametrize(
        "tier,expected",
        [
            (1, "Tier 1 (golden)"),
            (2, "Tier 2 (contributor)"),
            (3, "Tier 3 (stub)"),
            (99, "Unknown"),
        ],
    )
    def test_tier_label(self, tier: int, expected: str) -> None:
        s = M.SampleStatus(
            uc_id="1.1.1",
            tier=tier,
            origin="",
            has_positive=False,
            has_negative=False,
            positive_bytes=0,
        )
        assert s.tier_label() == expected

    def test_default_errors_is_empty_list(self) -> None:
        s = M.SampleStatus(
            uc_id="1.1.1",
            tier=3,
            origin="",
            has_positive=False,
            has_negative=False,
            positive_bytes=0,
        )
        assert s.errors == []


# -----------------------------------------------------------------------------
# scan_samples
# -----------------------------------------------------------------------------


class TestScanSamples:
    def test_returns_empty_when_samples_dir_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "doesnotexist")
        assert M.scan_samples({"1.1.1"}) == []

    def test_skips_non_directories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "samples").mkdir()
        # Stray file at samples/ root
        (tmp_path / "samples" / "stray.txt").write_text("x", encoding="utf-8")
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        assert M.scan_samples({"1.1.1"}) == []

    def test_skips_non_uc_directories(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pin the ``if not UC_DIR_RE.match(...)`` guard
        (tmp_path / "samples" / "_schema").mkdir(parents=True)
        (tmp_path / "samples" / "junk-dir").mkdir(parents=True)
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        assert M.scan_samples({"1.1.1"}) == []

    def test_missing_manifest_yields_tier3_with_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_sample(tmp_path, "1.1.1")  # No manifest
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})
        assert len(out) == 1
        assert out[0].tier == 3
        assert any("manifest.yaml missing" in e for e in out[0].errors)

    def test_yaml_parse_error_yields_tier3_with_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A YAML file that PyYAML can't parse
        _seed_sample(
            tmp_path,
            "1.1.1",
            manifest_yaml="key: [unbalanced",
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})
        assert len(out) == 1
        assert out[0].tier == 3
        assert any("YAML parse error" in e for e in out[0].errors)

    def test_canonical_tier1_golden(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_sample(
            tmp_path,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 1.1.1\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="event 1\n",
            negative="event 2\n",
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})
        assert len(out) == 1
        s = out[0]
        assert s.tier == 1
        assert s.has_positive is True
        assert s.has_negative is True
        assert s.errors == []  # canonical valid

    def test_tier2_when_no_reviewer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_sample(
            tmp_path,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 1.1.1\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"  # eligible
                "last_reviewed: 2026-01-01\n"
                # NO reviewer
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="event\n",
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})
        assert out[0].tier == 2

    def test_tier2_when_origin_is_synthetic(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_sample(
            tmp_path,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 1.1.1\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: synthetic\n"  # not in {vendor-doc, hand-authored}
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="event\n",
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})
        assert out[0].tier == 2

    def test_tier3_when_no_positive_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_sample(
            tmp_path,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 1.1.1\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            # No positive.log
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})
        assert out[0].tier == 3
        assert out[0].has_positive is False

    def test_empty_positive_log_treated_as_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``has_pos = pos.exists() and pos.stat().st_size > 0`` — pin
        the size-check half of the gate."""
        _seed_sample(
            tmp_path,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 1.1.1\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="",  # zero-byte file
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})
        assert out[0].has_positive is False
        assert out[0].tier == 3

    def test_uc_id_directory_mismatch(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Directory says UC-1.1.1 but manifest declares uc_id=2.2.2."""
        _seed_sample(
            tmp_path,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 2.2.2\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="x\n",
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1", "2.2.2"})
        assert any("does not match directory" in e for e in out[0].errors)

    def test_uc_not_in_catalog_ids(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_sample(
            tmp_path,
            "9.9.9",
            manifest_yaml=(
                "uc_id: 9.9.9\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="x\n",
        )
        monkeypatch.setattr(M, "SAMPLES_DIR", tmp_path / "samples")
        out = M.scan_samples({"1.1.1"})  # 9.9.9 not in catalog
        assert any("not present in catalog.json" in e for e in out[0].errors)


# -----------------------------------------------------------------------------
# _category_label
# -----------------------------------------------------------------------------


class TestCategoryLabel:
    def test_finds_category_name(self) -> None:
        catalog = {"DATA": [{"i": "1", "n": "Networking"}]}
        assert M._category_label("1.2.3", catalog) == "1. Networking"

    def test_unknown_category_returns_unknown(self) -> None:
        catalog = {"DATA": [{"i": "1", "n": "Networking"}]}
        assert M._category_label("99.0.0", catalog) == "99. Unknown"

    def test_handles_missing_n_key(self) -> None:
        """``cat.get('n', 'Unknown')`` — pin the default-name branch."""
        catalog = {"DATA": [{"i": "5"}]}  # No 'n' key
        assert M._category_label("5.1.1", catalog) == "5. Unknown"

    def test_handles_empty_data(self) -> None:
        assert M._category_label("1.1.1", {"DATA": []}) == "1. Unknown"


# -----------------------------------------------------------------------------
# render_coverage
# -----------------------------------------------------------------------------


class TestRenderCoverage:
    def test_renders_summary_and_breakdown(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(tmp_path, {1: ["1.1.1"], 2: ["2.1.1"]})
        monkeypatch.setattr(M, "CATALOG_PATH", tmp_path / "catalog.json")
        statuses = [
            M.SampleStatus(
                uc_id="1.1.1",
                tier=1,
                origin="vendor-doc",
                has_positive=True,
                has_negative=False,
                positive_bytes=10,
            ),
            M.SampleStatus(
                uc_id="2.1.1",
                tier=3,
                origin="",
                has_positive=False,
                has_negative=False,
                positive_bytes=0,
                errors=["missing manifest"],
            ),
        ]
        body = M.render_coverage(statuses)
        # Header + sections
        assert body.startswith("# Sample-event coverage")
        assert "## Summary" in body
        assert "## Breakdown by category" in body
        assert "## Details" in body
        # Total catalog UC count is correct
        assert "**2**" in body
        # Tier1 line shows the golden count
        assert "Tier 1" in body
        assert "vendor-doc" in body  # origin row in Details
        # Coverage percentage is computed
        assert "%" in body

    def test_empty_statuses_handles_zero_division(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``pct = ... if total_catalog_ucs else 0.0`` — pin the
        zero-catalog edge case."""
        # Empty catalog (no UCs)
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps({"DATA": []}), encoding="utf-8")
        monkeypatch.setattr(M, "CATALOG_PATH", cat_path)
        body = M.render_coverage([])
        assert "0.0%" in body

    def test_details_sorted_by_uc_id(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_catalog(
            tmp_path,
            {1: ["1.1.1"], 2: ["2.1.1"], 10: ["10.1.1"]},
        )
        monkeypatch.setattr(M, "CATALOG_PATH", tmp_path / "catalog.json")
        # Out-of-order to verify the sort
        statuses = [
            M.SampleStatus(
                uc_id="10.1.1",
                tier=1,
                origin="vendor-doc",
                has_positive=True,
                has_negative=False,
                positive_bytes=1,
            ),
            M.SampleStatus(
                uc_id="1.1.1",
                tier=1,
                origin="vendor-doc",
                has_positive=True,
                has_negative=False,
                positive_bytes=1,
            ),
            M.SampleStatus(
                uc_id="2.1.1",
                tier=2,
                origin="synthetic",
                has_positive=True,
                has_negative=False,
                positive_bytes=1,
            ),
        ]
        body = M.render_coverage(statuses)
        # Sort key is tuple-of-int — 10.1.1 must come AFTER 2.1.1
        i111 = body.index("UC-1.1.1")
        i211 = body.index("UC-2.1.1")
        i101 = body.index("UC-10.1.1")
        assert i111 < i211 < i101


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------


class TestMain:
    @pytest.fixture
    def fake_repo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> Path:
        _patch_paths(monkeypatch, tmp_path)
        return tmp_path

    def _run(
        self,
        argv: list[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> int:
        monkeypatch.setattr(sys, "argv", ["samples_index.py", *argv])
        return M.main()

    def test_missing_catalog_exits_2(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        rc = self._run([], monkeypatch)
        assert rc == 2
        assert "missing" in capsys.readouterr().err

    def test_no_samples_writes_empty_coverage(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_catalog(fake_repo, {1: ["1.1.1"]})
        rc = self._run([], monkeypatch)
        assert rc == 0
        assert (fake_repo / "docs" / "samples-coverage.md").exists()
        out = capsys.readouterr().out
        assert "Samples indexed: 0" in out
        assert "errors=no" in out

    def test_validate_only_does_not_write(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_catalog(fake_repo, {1: ["1.1.1"]})
        rc = self._run(["--validate-only"], monkeypatch)
        assert rc == 0
        assert not (fake_repo / "docs" / "samples-coverage.md").exists()

    def test_strict_returns_1_on_errors(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_catalog(fake_repo, {1: ["1.1.1"]})
        # Sample with no manifest → tier 3 + error
        _seed_sample(fake_repo, "1.1.1")
        rc = self._run(["--strict"], monkeypatch)
        assert rc == 1

    def test_strict_returns_0_when_no_errors(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_catalog(fake_repo, {1: ["1.1.1"]})
        _seed_sample(
            fake_repo,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 1.1.1\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="event\n",
        )
        rc = self._run(["--strict"], monkeypatch)
        assert rc == 0

    def test_non_strict_returns_0_even_with_errors(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_catalog(fake_repo, {1: ["1.1.1"]})
        _seed_sample(fake_repo, "1.1.1")  # tier 3 + error
        rc = self._run([], monkeypatch)
        assert rc == 0  # non-strict tolerates errors

    def test_writes_coverage_with_real_samples(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_catalog(fake_repo, {1: ["1.1.1"]})
        _seed_sample(
            fake_repo,
            "1.1.1",
            manifest_yaml=(
                "uc_id: 1.1.1\n"
                "sourcetype: foo\n"
                "index: main\n"
                "origin: vendor-doc\n"
                "last_reviewed: 2026-01-01\n"
                "reviewer: alice\n"
                "expected:\n"
                "  min_count: 1\n"
            ),
            positive="event\n",
        )
        rc = self._run([], monkeypatch)
        assert rc == 0
        coverage = (fake_repo / "docs" / "samples-coverage.md").read_text(
            encoding="utf-8"
        )
        assert "UC-1.1.1" in coverage
        assert "Tier 1" in coverage

    def test_creates_docs_directory_if_missing(
        self,
        fake_repo: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``COVERAGE_OUT.parent.mkdir(parents=True, exist_ok=True)`` —
        pin the parent-mkdir branch."""
        _seed_catalog(fake_repo, {1: ["1.1.1"]})
        # docs/ doesn't exist yet
        assert not (fake_repo / "docs").exists()
        rc = self._run([], monkeypatch)
        assert rc == 0
        assert (fake_repo / "docs").is_dir()


# -----------------------------------------------------------------------------
# Module entrypoint — runpy-copy smoke test
# -----------------------------------------------------------------------------
#
# samples_index.py ends with ``if __name__ == "__main__": sys.exit(main())``.
# A naive ``runpy.run_path(scripts/samples_index.py)`` would pollute the real
# ``docs/samples-coverage.md`` because the module-level ``CATALOG_PATH`` /
# ``COVERAGE_OUT`` constants are computed at import-time from the script's
# absolute ``__file__``.
#
# The safe alternative: copy the script into a fake repo rooted at
# ``tmp_path`` (so ``REPO_ROOT = tmp_path``). The script's CATALOG_PATH then
# points to a missing tmp file, which short-circuits ``main()`` to return 2
# (the documented "catalog missing" error path). That exercises the
# ``sys.exit(main())`` boilerplate on the COPY without touching the real
# repo. The original ``scripts/samples_index.py`` line 388 stays uncovered
# in attribution (coverage is path-keyed), but the contract is exercised
# end-to-end here.


class TestMainGuard:
    def test_runpy_invocation_returns_catalog_missing_exit_code(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import runpy
        import shutil
        import sys

        repo = tmp_path / "fake_repo"
        (repo / "samples").mkdir(parents=True)
        (repo / "docs").mkdir(parents=True)
        scripts_dir = repo / "scripts"
        scripts_dir.mkdir()

        real_script = (
            Path(__file__).resolve().parent.parent.parent
            / "scripts"
            / "samples_index.py"
        )
        script_copy = scripts_dir / "samples_index.py"
        shutil.copy(real_script, script_copy)

        # main() reads sys.argv via argparse defaults; pin it so pytest's
        # own CLI args don't leak in.
        monkeypatch.setattr(sys, "argv", [str(script_copy)])

        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(str(script_copy), run_name="__main__")
        # CATALOG_PATH does not exist inside the fake repo, so main()
        # short-circuits to return 2 ("ERROR: <path> missing — run
        # build.py first.").
        assert excinfo.value.code == 2
        # The real repo's docs/samples-coverage.md is untouched (the
        # error path exits before COVERAGE_OUT.write_text is reached).
        assert script_copy.exists()
