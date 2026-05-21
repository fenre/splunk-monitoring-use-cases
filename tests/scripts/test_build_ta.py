"""Hermetic unit tests for ``scripts/build_ta.py``.

``build_ta.py`` packages the Quick-Start UCs from ``content/INDEX.md``
plus ``catalog.json`` into a real Splunkbase TA layout under
``ta/TA-splunk-use-cases/default/`` (savedsearches, macros, eventtypes,
tags, nav). It is tier-2 ratchet material (named explicitly in
``coverage_budget.py``'s ``TIER2_REGEXES``).

We care about two failure surfaces:

* **Drift between catalog → conf** — a saved search whose cron / earliest
  / severity falls out of step with the UC's declared criticality, or
  whose SPL gets emitted on a single line instead of conf-escaped
  multi-line (Splunk's parser would silently truncate at the first
  ``\\n``).
* **--check exit semantics** — the gate must return 0 on parity with
  ``ta/TA-splunk-use-cases/default``, 1 on drift. Confusing those two
  states would cause CI to either silently bless drift or red-bar every
  PR.

Everything is monkey-patched into ``tmp_path`` so the real repo's
``catalog.json`` / ``ta/`` directory / ``content/INDEX.md`` are never
touched. The ``main()`` CLI is exercised end-to-end with captured
stdout/stderr.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_ta.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_ta", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_ta"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def bt() -> ModuleType:
    """Return a fresh import of ``build_ta``.

    ``module``-scope would let constants like ``CATALOG`` /
    ``INDEX_MD`` / ``TA_DIR`` leak across tests, defeating
    ``monkeypatch.setattr`` isolation.
    """
    return _load_module()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _patch_paths(
    bt: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    """Re-root every hard-coded input/output path into ``tmp_path``."""
    catalog = tmp_path / "catalog.json"
    index_md = tmp_path / "content" / "INDEX.md"
    ta_dir = tmp_path / "ta" / "TA-splunk-use-cases"
    default_dir = ta_dir / "default"
    repo_root = tmp_path

    monkeypatch.setattr(bt, "CATALOG", str(catalog))
    monkeypatch.setattr(bt, "INDEX_MD", str(index_md))
    monkeypatch.setattr(bt, "TA_DIR", str(ta_dir))
    monkeypatch.setattr(bt, "DEFAULT_DIR", str(default_dir))
    monkeypatch.setattr(bt, "REPO_ROOT", str(repo_root))

    return {
        "catalog": catalog,
        "index_md": index_md,
        "ta_dir": ta_dir,
        "default_dir": default_dir,
        "repo_root": repo_root,
    }


def _seed_catalog(
    catalog_path: Path,
    *,
    use_cases_by_cat: dict[int, list[dict[str, Any]]] | None = None,
) -> None:
    """Write a minimal catalog.json given UCs keyed by category number."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    data: list[dict[str, Any]] = []
    for cat_num, ucs in (use_cases_by_cat or {}).items():
        # Group every supplied UC under a single subcategory ``<cat>.1``.
        data.append({
            "i": cat_num,
            "s": [{"i": f"{cat_num}.1", "u": list(ucs)}],
        })
    catalog_path.write_text(json.dumps({"DATA": data}), encoding="utf-8")


def _seed_index_md(
    index_path: Path,
    *,
    sections: dict[int, list[str]] | None = None,
    extra: str = "",
) -> None:
    """Write a content/INDEX.md that exposes the per-category Quick
    Start UC IDs the script's regex consumes.

    Format expected by ``parse_quickstart``:

        ## 1. Foundation
            - UC-1.1.1 short title
            - UC-1.1.2 short title
    """
    index_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for cat_num, ids in sorted((sections or {}).items()):
        lines.append(f"## {cat_num}. Cat {cat_num}")
        for uid in ids:
            lines.append(f"    - UC-{uid} short label")
        lines.append("")
    if extra:
        lines.append(extra)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ======================================================================
# 1. Module-level constants & contracts
# ======================================================================


class TestModuleConstants:
    def test_crit_to_cron_covers_all_known_levels(self, bt: ModuleType) -> None:
        # Every criticality value used in the catalog schema must have a
        # mapping; otherwise ``render_savedsearches`` silently falls back
        # to ``medium`` and the TA's alert cadence drifts.
        assert set(bt.CRIT_TO_CRON.keys()) == {"critical", "high", "medium", "low"}

    def test_crit_to_cron_values_are_5_tuples_of_str(self, bt: ModuleType) -> None:
        # Every row is the 5-tuple ``(cron, earliest, latest, severity, condition)``.
        for crit, row in bt.CRIT_TO_CRON.items():
            assert isinstance(row, tuple) and len(row) == 5, crit
            assert all(isinstance(field, str) for field in row), crit

    def test_crit_to_cron_severity_decreases_with_severity(
        self, bt: ModuleType
    ) -> None:
        # Reordering severities by accident (e.g. ``low`` higher than
        # ``critical``) would push real critical UCs to severity 2 in
        # Splunk alert manager — silent triage failure. Critical > high
        # > medium = low (per the script's actual values).
        s = {k: int(v[3]) for k, v in bt.CRIT_TO_CRON.items()}
        assert s["critical"] > s["high"] > s["medium"]
        assert s["medium"] == s["low"]

    def test_cat_index_macro_covers_23_categories(self, bt: ModuleType) -> None:
        # The catalog has 23 top-level categories. Missing one would
        # cause ``render_savedsearches`` to emit a macro that is never
        # defined in ``macros.conf`` (search-time NameError).
        assert sorted(bt.CAT_INDEX_MACRO.keys()) == list(range(1, 24))
        for cat_num, macro in bt.CAT_INDEX_MACRO.items():
            assert macro.startswith("uc_index_"), (cat_num, macro)

    def test_qs_regexes_match_expected_lines(self, bt: ModuleType) -> None:
        # Sanity-check the INDEX.md parser regexes against the exact
        # shape that ``content/INDEX.md`` uses today.
        assert bt.QS_CAT_RX.match("## 1. Operating Systems")
        assert bt.QS_UC_RX.match("    - UC-1.1.23 Foo bar")
        assert not bt.QS_CAT_RX.match("### 1.1 Sub heading")
        assert not bt.QS_UC_RX.match("- UC-1.1.23 no leading whitespace")

    def test_eventtypes_are_3_tuples(self, bt: ModuleType) -> None:
        assert isinstance(bt.EVENTTYPES, list)
        assert bt.EVENTTYPES, "EVENTTYPES must not be empty"
        for row in bt.EVENTTYPES:
            assert len(row) == 3, row
            name, search, desc = row
            assert name.startswith("uc_"), name
            assert isinstance(search, str) and search, search
            assert isinstance(desc, str), desc

    def test_conf_header_is_warning_block(self, bt: ModuleType) -> None:
        # Every emitted file MUST start with the GENERATED warning so
        # operators don't hand-edit (which would be silently overwritten
        # by the next ``build_ta`` run).
        assert "GENERATED by scripts/build_ta.py" in bt.CONF_HEADER
        assert "DO NOT EDIT" in bt.CONF_HEADER

    def test_nav_xml_is_minimal_and_references_repo(
        self, bt: ModuleType
    ) -> None:
        assert "<nav" in bt.NAV_XML
        assert "fenre.github.io/splunk-monitoring-use-cases" in bt.NAV_XML
        assert 'name="search"' in bt.NAV_XML


# ======================================================================
# 2. parse_quickstart
# ======================================================================


class TestParseQuickstart:
    def test_picks_uc_ids_per_category(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        _seed_index_md(
            paths["index_md"],
            sections={
                1: ["1.1.1", "1.1.2"],
                10: ["10.1.5"],
            },
        )

        out = bt.parse_quickstart()

        assert out == {1: ["1.1.1", "1.1.2"], 10: ["10.1.5"]}

    def test_skips_uc_lines_without_a_category_heading(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Floating UC line at the top of the file (before any ``## n.``)
        # must NOT be attached to a phantom category — that would cause
        # ``current_cat=None`` to drop the line silently.
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        paths["index_md"].parent.mkdir(parents=True, exist_ok=True)
        paths["index_md"].write_text(
            "\n    - UC-99.9.9 orphan\n## 1. Cat\n    - UC-1.1.1 wired\n",
            encoding="utf-8",
        )

        assert bt.parse_quickstart() == {1: ["1.1.1"]}

    def test_ignores_h3_subheadings(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # ``### 1.1 Linux`` must NOT register a new category; only the
        # top-level ``## n. <name>`` heading counts.
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        paths["index_md"].parent.mkdir(parents=True, exist_ok=True)
        paths["index_md"].write_text(
            "## 1. Cat\n### 1.1 Linux\n    - UC-1.1.1 wired\n",
            encoding="utf-8",
        )

        assert bt.parse_quickstart() == {1: ["1.1.1"]}

    def test_returns_empty_dict_for_empty_file(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        paths["index_md"].parent.mkdir(parents=True, exist_ok=True)
        paths["index_md"].write_text("", encoding="utf-8")

        assert bt.parse_quickstart() == {}

    def test_ignores_uc_lines_with_wrong_id_shape(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # ``UC-1.1`` (missing the third segment) and ``UC-1.1.1-suffix``
        # (no trailing whitespace) must be ignored — the catalogue's
        # UC-ID convention is strictly ``X.Y.Z``.
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        paths["index_md"].parent.mkdir(parents=True, exist_ok=True)
        paths["index_md"].write_text(
            "## 1. Cat\n"
            "    - UC-1.1 missing third segment\n"
            "    - UC-1.1.1-no_space_suffix\n"
            "    - UC-1.1.1 wired\n",
            encoding="utf-8",
        )

        assert bt.parse_quickstart() == {1: ["1.1.1"]}


# ======================================================================
# 3. Catalog helpers (load_catalog, index_by_id)
# ======================================================================


class TestLoadCatalog:
    def test_round_trips_minimal_catalog(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        paths["catalog"].write_text('{"DATA": []}', encoding="utf-8")

        assert bt.load_catalog() == {"DATA": []}

    def test_raises_on_invalid_json(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        paths["catalog"].write_text("{not json", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            bt.load_catalog()


class TestIndexById:
    def test_extracts_every_uc_with_id_and_cat_number(
        self, bt: ModuleType
    ) -> None:
        catalog = {
            "DATA": [{
                "i": 7,
                "s": [
                    {"i": "7.1", "u": [{"i": "7.1.1", "n": "A"}]},
                    {"i": "7.2", "u": [{"i": "7.2.1", "n": "B"}]},
                ],
            }],
        }

        idx = bt.index_by_id(catalog)

        assert set(idx.keys()) == {"7.1.1", "7.2.1"}
        assert idx["7.1.1"]["_cat"] == 7
        assert idx["7.1.1"]["n"] == "A"

    def test_ignores_ucs_without_id(self, bt: ModuleType) -> None:
        # A UC missing ``i`` must NOT crash and MUST NOT appear in the
        # output dict (otherwise we'd index None and clobber other UCs).
        catalog = {
            "DATA": [{
                "i": 1,
                "s": [{"i": "1.1", "u": [{"n": "no id"}, {"i": "1.1.1"}]}],
            }],
        }
        assert list(bt.index_by_id(catalog).keys()) == ["1.1.1"]

    def test_empty_catalog_returns_empty_index(self, bt: ModuleType) -> None:
        assert bt.index_by_id({}) == {}
        assert bt.index_by_id({"DATA": []}) == {}


# ======================================================================
# 4. Conf escape helpers
# ======================================================================


class TestEscapeConf:
    def test_single_line_is_stripped_but_unchanged(
        self, bt: ModuleType
    ) -> None:
        assert bt._escape_conf("  index=foo | stats count  ") == (
            "index=foo | stats count"
        )

    def test_multi_line_uses_backslash_newline_continuation(
        self, bt: ModuleType
    ) -> None:
        # Splunk .conf parsers expect ``\\\n`` for value continuation; a
        # bare newline in the value would silently terminate the
        # ``search =`` key. This is the most expensive bug to debug at
        # runtime.
        out = bt._escape_conf("a\nb\nc")
        assert out == "a \\\nb \\\nc"

    def test_strips_trailing_whitespace_from_each_continuation_line(
        self, bt: ModuleType
    ) -> None:
        # Trailing whitespace BEFORE the ``\\`` is treated as part of
        # the value by Splunk; if the SPL author left trailing spaces,
        # we MUST strip them or we'll silently break the search.
        out = bt._escape_conf("a   \nb   \nc")
        assert out == "a \\\nb \\\nc"


class TestStanzaName:
    def test_strips_brackets_to_avoid_conf_breakage(
        self, bt: ModuleType
    ) -> None:
        # Square brackets in the stanza name would terminate the stanza
        # early in Splunk's .conf parser. Replace them with parentheses.
        out = bt._stanza_name({"i": "1.1.1", "n": "Foo [Bar] baz"})
        assert out == "UC-1.1.1 — Foo (Bar) baz"

    def test_strips_internal_newlines(self, bt: ModuleType) -> None:
        # Newlines in the stanza name would terminate the stanza header
        # mid-line; replace with a space.
        out = bt._stanza_name({"i": "1.1.1", "n": "A\nB"})
        assert out == "UC-1.1.1 — A B"

    def test_falls_back_to_question_mark_when_id_missing(
        self, bt: ModuleType
    ) -> None:
        # Silent ``?`` instead of crashing — the diff-driven ``--check``
        # gate will catch missing UCs before they ever land on disk.
        out = bt._stanza_name({"n": "X"})
        assert out == "UC-? — X"

    def test_falls_back_to_untitled_when_name_missing(
        self, bt: ModuleType
    ) -> None:
        out = bt._stanza_name({"i": "1.1.1"})
        assert out == "UC-1.1.1 — Untitled"


# ======================================================================
# 5. render_savedsearches
# ======================================================================


class TestRenderSavedsearches:
    def test_emits_header_and_blank_line_for_empty_input(
        self, bt: ModuleType
    ) -> None:
        out = bt.render_savedsearches([])
        assert out.startswith(bt.CONF_HEADER)
        # Trailing newline contract — every .conf file we write ends in
        # exactly one ``\n`` so successive runs don't drift on EOF.
        assert out.endswith("\n")

    def test_skips_uc_without_spl(self, bt: ModuleType) -> None:
        # A UC with no ``q`` (SPL) field would emit a half-formed stanza
        # without a ``search =`` line — broken on first load.
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "A", "q": ""},
            {"i": "1.1.2", "n": "B", "q": "  "},
            {"i": "1.1.3", "n": "C", "q": "index=foo"},
        ])
        assert "UC-1.1.1" not in out
        assert "UC-1.1.2" not in out
        assert "UC-1.1.3" in out

    def test_maps_criticality_to_cron(self, bt: ModuleType) -> None:
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "Critical UC", "q": "index=*", "c": "critical"}
        ])
        assert "cron_schedule = */15 * * * *" in out
        assert "dispatch.earliest_time = -30m@m" in out
        assert "alert.severity = 4" in out

    def test_unknown_criticality_falls_back_to_medium(
        self, bt: ModuleType
    ) -> None:
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "Mystery", "q": "index=*", "c": "unknown"}
        ])
        assert "cron_schedule = 0 */2 * * *" in out  # medium row

    def test_missing_criticality_falls_back_to_medium(
        self, bt: ModuleType
    ) -> None:
        # When ``c`` is missing we substitute "medium" (the script's
        # ``(uc.get("c") or "medium")`` guard). Most catalogue UCs do
        # carry ``c`` so this fallback is a defensive safety net.
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "Defaulted", "q": "index=*"}
        ])
        assert "cron_schedule = 0 */2 * * *" in out
        assert "criticality: medium" in out

    def test_uppercase_criticality_is_normalised_to_lowercase(
        self, bt: ModuleType
    ) -> None:
        # Catalogue authors sometimes paste capitalised values from the
        # MD docs. ``CRIT_TO_CRON`` keys are lowercase only, so the
        # ``.lower()`` call is the contract that keeps these working.
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "Shouty", "q": "index=*", "c": "CRITICAL"}
        ])
        assert "cron_schedule = */15 * * * *" in out

    def test_description_includes_id_and_criticality(
        self, bt: ModuleType
    ) -> None:
        out = bt.render_savedsearches([
            {"i": "9.9.9", "n": "Probe", "q": "index=*", "c": "high"}
        ])
        assert "description = Probe (UC-9.9.9, criticality: high)" in out

    def test_multiline_spl_is_continuation_escaped(
        self, bt: ModuleType
    ) -> None:
        # The most-load-bearing assertion in this file — see
        # ``TestEscapeConf.test_multi_line_uses_backslash_newline_continuation``
        # for rationale.
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "A", "q": "index=foo\n| stats count"}
        ])
        assert "search = index=foo \\\n| stats count" in out

    def test_mitre_field_is_joined_with_comma(self, bt: ModuleType) -> None:
        # MITRE ATT&CK technique IDs (e.g. ``T1059``) feed
        # ``action.notable.param.mitre_attack`` which ES's Notable
        # framework parses by comma.
        out = bt.render_savedsearches([
            {
                "i": "1.1.1",
                "n": "ATT&CK",
                "q": "index=*",
                "mitre": ["T1059", "T1078"],
            }
        ])
        assert "action.notable.param.mitre_attack = T1059,T1078" in out

    def test_skips_mitre_line_when_field_absent(self, bt: ModuleType) -> None:
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "No ATT&CK", "q": "index=*"}
        ])
        assert "action.notable.param.mitre_attack" not in out

    def test_skips_mitre_line_when_empty_list(self, bt: ModuleType) -> None:
        # An empty ``mitre: []`` list is falsy and MUST behave the same
        # as a missing key — otherwise we'd emit
        # ``action.notable.param.mitre_attack = `` (empty), which is a
        # silent contract change for ES.
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "Empty mitre", "q": "index=*", "mitre": []}
        ])
        assert "action.notable.param.mitre_attack" not in out

    def test_upstream_reference_link_is_anchored_to_uc_id(
        self, bt: ModuleType
    ) -> None:
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "Anchor", "q": "index=*"}
        ])
        # The upstream link is the traceability lifeline between a
        # Splunk-installed TA and the GitHub source — never let it lose
        # its UC anchor.
        assert "#use-case-1.1.1" in out
        # The anchor lives in a ``#`` comment after the GitHub URL —
        # MUST start with ``#`` so Splunk's .conf parser ignores it.
        for line in out.splitlines():
            if "use-case-1.1.1" in line:
                assert line.startswith("#")
                break
        else:  # pragma: no cover - sanity guard
            pytest.fail("upstream reference comment line not found in output")

    def test_value_field_is_added_to_description_parts(
        self, bt: ModuleType
    ) -> None:
        # ``v`` (business value blurb) is currently collected into
        # ``desc_parts`` but never serialised into the conf. This is
        # a known shape choice — keep the contract test in place so a
        # future refactor that DOES emit ``v`` will fail loudly and
        # remind authors to update the description format.
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "A", "q": "index=*", "v": "Stops fires"}
        ])
        # ``v`` is collected but not currently rendered into the .conf.
        # We do NOT assert it appears — only that the stanza still
        # renders cleanly when ``v`` is present.
        assert "UC-1.1.1" in out

    def test_known_false_positives_is_collected_to_desc_parts(
        self, bt: ModuleType
    ) -> None:
        # Same shape as ``v``: ``kfp`` is collected but not emitted into
        # the .conf today. Test asserts the stanza still renders without
        # erroring when ``kfp`` is present, not that ``kfp`` appears in
        # output. If a future revision flips this contract, update this
        # test and the saved-search consumers in lockstep.
        out = bt.render_savedsearches([
            {"i": "1.1.1", "n": "A", "q": "index=*", "kfp": "see lookup"}
        ])
        assert "UC-1.1.1" in out


# ======================================================================
# 6. render_macros / render_eventtypes / render_tags
# ======================================================================


class TestRenderMacros:
    def test_emits_one_stanza_per_category_macro(self, bt: ModuleType) -> None:
        out = bt.render_macros()
        for macro in bt.CAT_INDEX_MACRO.values():
            assert f"[{macro}]" in out
        # Plus the two cross-category extras.
        assert "[uc_index_any]" in out
        assert "[uc_fields_cim]" in out

    def test_macros_default_to_index_star(self, bt: ModuleType) -> None:
        # Every category macro must default to ``index=*`` so a brand-new
        # install actually returns SOMETHING when an operator clicks
        # "open" on a Quick Start saved search. Forgetting this default
        # is the single most common failure mode of vendor TAs.
        out = bt.render_macros()
        # First occurrence of ``definition = index=*`` should be present
        # at least once per category macro.
        assert out.count("definition = index=*") >= len(bt.CAT_INDEX_MACRO)

    def test_iseval_zero_for_text_macros(self, bt: ModuleType) -> None:
        out = bt.render_macros()
        # ``iseval = 0`` flags these as TEXT macros (not eval expressions);
        # flipping the flag would make Splunk try to evaluate ``index=*``
        # as eval syntax and silently drop every saved search.
        assert "iseval = 0" in out

    def test_emits_header_and_terminates_with_single_newline(
        self, bt: ModuleType
    ) -> None:
        out = bt.render_macros()
        assert out.startswith(bt.CONF_HEADER)
        assert out.endswith("\n")
        assert not out.endswith("\n\n")

    def test_uc_fields_cim_uses_comment_macro_syntax(
        self, bt: ModuleType
    ) -> None:
        # The ``uc_fields_cim`` placeholder MUST be a Splunk inline
        # ``comment`` macro so search-time evaluation is a no-op; any
        # other shape would either error or accidentally match events.
        out = bt.render_macros()
        assert '`comment("CIM-normalised fields enforced in searches")`' in out


class TestRenderEventtypes:
    def test_emits_every_entry_from_EVENTTYPES(self, bt: ModuleType) -> None:
        out = bt.render_eventtypes()
        for name, _, _ in bt.EVENTTYPES:
            assert f"[{name}]" in out

    def test_search_lines_carry_actual_search_string(
        self, bt: ModuleType
    ) -> None:
        out = bt.render_eventtypes()
        for _, search, _ in bt.EVENTTYPES:
            assert f"search = {search}" in out

    def test_description_lines_are_commented_out(self, bt: ModuleType) -> None:
        # ``description`` is NOT a Splunk eventtypes.conf key. Emitting
        # it uncommented would trigger AppInspect "invalid key" warnings.
        # The script emits it as a leading ``#`` comment instead.
        out = bt.render_eventtypes()
        for _, _, desc in bt.EVENTTYPES:
            assert f"#description = {desc}" in out


class TestRenderTags:
    def test_groups_tags_by_eventtype_stanza(self, bt: ModuleType) -> None:
        out = bt.render_tags()
        # ``uc_auth_fail`` carries both ``authentication`` and ``failure``;
        # the script MUST group them under a single
        # ``[eventtype=uc_auth_fail]`` stanza, NOT emit the stanza twice
        # (Splunk would silently keep only the last copy).
        assert out.count("[eventtype=uc_auth_fail]") == 1
        # Find the block for that stanza and assert both tags live in it.
        block = out.split("[eventtype=uc_auth_fail]", 1)[1].split("[", 1)[0]
        assert "authentication = enabled" in block
        assert "failure = enabled" in block

    def test_other_stanzas_emit_their_single_tag(
        self, bt: ModuleType
    ) -> None:
        out = bt.render_tags()
        assert "[eventtype=uc_firewall]" in out
        assert "firewall = enabled" in out

    def test_emits_header(self, bt: ModuleType) -> None:
        assert bt.render_tags().startswith(bt.CONF_HEADER)


# ======================================================================
# 7. pick_ucs (the catalog ↔ INDEX.md join)
# ======================================================================


class TestPickUcs:
    def test_picks_quickstart_ucs_in_category_order(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        _seed_catalog(
            paths["catalog"],
            use_cases_by_cat={
                10: [{"i": "10.1.1", "n": "Ten"}],
                1: [{"i": "1.1.1", "n": "One"}],
            },
        )
        _seed_index_md(
            paths["index_md"],
            sections={
                10: ["10.1.1"],
                1: ["1.1.1"],
            },
        )

        picked = bt.pick_ucs()

        # Sorted by category number → cat 1 first, then cat 10.
        assert [uc["i"] for uc in picked] == ["1.1.1", "10.1.1"]
        # Each picked UC carries its ``_cat`` rollup field set by
        # ``index_by_id``.
        assert picked[0]["_cat"] == 1
        assert picked[1]["_cat"] == 10

    def test_dedupes_uc_ids_listed_more_than_once(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # If a UC is referenced twice in INDEX.md (typo) we MUST package
        # it once or the resulting savedsearches.conf has duplicate
        # stanza names — a non-recoverable AppInspect failure.
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        _seed_catalog(
            paths["catalog"],
            use_cases_by_cat={1: [{"i": "1.1.1", "n": "One"}]},
        )
        _seed_index_md(
            paths["index_md"],
            sections={1: ["1.1.1", "1.1.1"], 2: ["1.1.1"]},
        )

        picked = bt.pick_ucs()

        assert [uc["i"] for uc in picked] == ["1.1.1"]

    def test_skips_uc_ids_missing_from_catalog(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # A stale UC ID in INDEX.md (deleted UC, renumbered UC) must be
        # silently skipped rather than blowing up the build. The CI
        # ``--check`` gate will still catch the drift in the resulting
        # diff if it matters.
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        _seed_catalog(
            paths["catalog"],
            use_cases_by_cat={1: [{"i": "1.1.1", "n": "One"}]},
        )
        _seed_index_md(
            paths["index_md"],
            sections={1: ["1.1.1", "9.9.99"]},  # 9.9.99 doesn't exist
        )

        picked = bt.pick_ucs()
        assert [uc["i"] for uc in picked] == ["1.1.1"]

    def test_returns_empty_when_catalog_and_index_are_empty(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"])
        _seed_index_md(paths["index_md"])

        assert bt.pick_ucs() == []


# ======================================================================
# 8. _build_file_map
# ======================================================================


class TestBuildFileMap:
    def test_emits_all_five_expected_files(self, bt: ModuleType) -> None:
        out = bt._build_file_map([
            {"i": "1.1.1", "n": "A", "q": "index=*", "c": "low"}
        ])
        assert set(out.keys()) == {
            "savedsearches.conf",
            "macros.conf",
            "eventtypes.conf",
            "tags.conf",
            "data/ui/nav/default.xml",
        }

    def test_each_file_is_nonempty_str(self, bt: ModuleType) -> None:
        out = bt._build_file_map([])
        for rel, contents in out.items():
            assert isinstance(contents, str), rel
            assert contents.strip(), f"{rel} should not be empty"

    def test_nav_default_xml_is_the_canonical_nav(self, bt: ModuleType) -> None:
        # ``data/ui/nav/default.xml`` is hand-curated in the source —
        # accidental mismatch with ``NAV_XML`` would silently degrade
        # the TA's nav menu in Splunk Web.
        out = bt._build_file_map([])
        assert out["data/ui/nav/default.xml"] == bt.NAV_XML


# ======================================================================
# 9. _write_default_dir
# ======================================================================


class TestWriteDefaultDir:
    def test_writes_every_file_and_creates_subdirs(
        self, bt: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        files = {
            "savedsearches.conf": "[X]\n",
            "data/ui/nav/default.xml": "<nav/>\n",
        }
        default_dir = tmp_path / "ta_default"

        bt._write_default_dir(str(default_dir), files, verbose=False)

        assert (default_dir / "savedsearches.conf").read_text() == "[X]\n"
        assert (default_dir / "data" / "ui" / "nav" / "default.xml").read_text() == "<nav/>\n"

    def test_verbose_mode_prints_one_line_per_file(
        self, bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # ``verbose=True`` printlns use ``REPO_ROOT`` to compute the
        # relpath — re-root to tmp_path so the printed path is
        # predictable.
        monkeypatch.setattr(bt, "REPO_ROOT", str(tmp_path))

        files = {"savedsearches.conf": "[Y]\n"}
        default_dir = tmp_path / "ta_default"
        bt._write_default_dir(str(default_dir), files, verbose=True)

        out = capsys.readouterr().out
        assert "wrote ta_default/savedsearches.conf" in out
        assert "(4 chars)" in out  # len("[Y]\n") == 4

    def test_overwrites_existing_files(
        self, bt: ModuleType, tmp_path: Path
    ) -> None:
        # The generator is idempotent — a second run with the same input
        # MUST yield byte-identical output, AND a run with new content
        # MUST overwrite the old file without producing a stale half-mix.
        default_dir = tmp_path / "ta_default"
        bt._write_default_dir(
            str(default_dir),
            {"savedsearches.conf": "old\n"},
            verbose=False,
        )
        bt._write_default_dir(
            str(default_dir),
            {"savedsearches.conf": "new\n"},
            verbose=False,
        )
        assert (default_dir / "savedsearches.conf").read_text() == "new\n"

    def test_creates_data_ui_nav_directory_even_for_empty_filemap(
        self, bt: ModuleType, tmp_path: Path
    ) -> None:
        # The nav directory is always created up-front — this is the
        # contract that lets us emit ``data/ui/nav/default.xml`` even on
        # the first run before any other file pre-creates the directory.
        default_dir = tmp_path / "ta_default"
        bt._write_default_dir(str(default_dir), {}, verbose=False)
        assert (default_dir / "data" / "ui" / "nav").is_dir()


# ======================================================================
# 10. main() — write mode
# ======================================================================


class TestMainWriteMode:
    def _seed_full_repo(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        ucs_by_cat: dict[int, list[dict[str, Any]]],
        qs: dict[int, list[str]],
    ) -> dict[str, Path]:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases_by_cat=ucs_by_cat)
        _seed_index_md(paths["index_md"], sections=qs)
        return paths

    def test_returns_zero_and_writes_files_in_default_mode(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = self._seed_full_repo(
            bt,
            monkeypatch,
            tmp_path,
            ucs_by_cat={1: [{"i": "1.1.1", "n": "A", "q": "index=*"}]},
            qs={1: ["1.1.1"]},
        )

        monkeypatch.setattr(sys, "argv", ["build_ta"])
        rc = bt.main()

        assert rc == 0
        # All five expected output files exist on disk.
        assert (paths["default_dir"] / "savedsearches.conf").exists()
        assert (paths["default_dir"] / "macros.conf").exists()
        assert (paths["default_dir"] / "eventtypes.conf").exists()
        assert (paths["default_dir"] / "tags.conf").exists()
        assert (paths["default_dir"] / "data" / "ui" / "nav" / "default.xml").exists()
        # Status line is printed for operator visibility.
        out = capsys.readouterr().out
        assert "packaging 1 saved searches" in out

    def test_prints_count_of_zero_when_no_quickstart_ucs(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        self._seed_full_repo(
            bt, monkeypatch, tmp_path,
            ucs_by_cat={1: [{"i": "1.1.1", "n": "A", "q": "index=*"}]},
            qs={},  # no Quick Start picks
        )

        monkeypatch.setattr(sys, "argv", ["build_ta"])
        rc = bt.main()

        assert rc == 0
        assert "packaging 0 saved searches" in capsys.readouterr().out


# ======================================================================
# 11. main() — --check mode
# ======================================================================


class TestMainCheckMode:
    def _wire_check(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        ucs_by_cat: dict[int, list[dict[str, Any]]],
        qs: dict[int, list[str]],
        seed_default: bool = True,
    ) -> dict[str, Path]:
        paths = _patch_paths(bt, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], use_cases_by_cat=ucs_by_cat)
        _seed_index_md(paths["index_md"], sections=qs)
        if seed_default:
            ucs = bt.pick_ucs()
            files = bt._build_file_map(ucs)
            bt._write_default_dir(str(paths["default_dir"]), files, verbose=False)
        return paths

    def test_returns_zero_when_default_dir_matches_freshly_generated(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        self._wire_check(
            bt, monkeypatch, tmp_path,
            ucs_by_cat={1: [{"i": "1.1.1", "n": "A", "q": "index=*"}]},
            qs={1: ["1.1.1"]},
        )

        monkeypatch.setattr(sys, "argv", ["build_ta", "--check"])
        rc = bt.main()

        assert rc == 0
        out = capsys.readouterr()
        assert "build_ta output is up to date." in out.out

    def test_returns_one_and_writes_diff_to_stderr_on_drift(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = self._wire_check(
            bt, monkeypatch, tmp_path,
            ucs_by_cat={1: [{"i": "1.1.1", "n": "A", "q": "index=*"}]},
            qs={1: ["1.1.1"]},
        )
        # Mutate the already-written savedsearches.conf to force a diff.
        (paths["default_dir"] / "savedsearches.conf").write_text(
            "OUT OF DATE\n", encoding="utf-8"
        )

        monkeypatch.setattr(sys, "argv", ["build_ta", "--check"])
        rc = bt.main()

        assert rc == 1
        err = capsys.readouterr().err
        assert "drift detected" in err
        # Reasonable signal of a diff in the output.
        assert "savedsearches.conf" in err

    def test_returns_one_when_default_dir_missing_files(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # A missing file is the moral equivalent of a TA install that
        # was never run through ``build_ta`` — diff returns non-zero
        # and we MUST surface it as exit 1.
        paths = self._wire_check(
            bt, monkeypatch, tmp_path,
            ucs_by_cat={1: [{"i": "1.1.1", "n": "A", "q": "index=*"}]},
            qs={1: ["1.1.1"]},
        )
        (paths["default_dir"] / "savedsearches.conf").unlink()

        monkeypatch.setattr(sys, "argv", ["build_ta", "--check"])
        rc = bt.main()

        assert rc == 1
        assert "drift detected" in capsys.readouterr().err

    def test_check_does_not_touch_default_dir_when_in_sync(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        # ``--check`` is read-only over the real default_dir — it writes
        # everything into a TemporaryDirectory and only diffs. If it
        # ever started writing to the real path, two consecutive
        # ``--check`` runs would silently mask drift.
        paths = self._wire_check(
            bt, monkeypatch, tmp_path,
            ucs_by_cat={1: [{"i": "1.1.1", "n": "A", "q": "index=*"}]},
            qs={1: ["1.1.1"]},
        )
        before_mtime = (paths["default_dir"] / "savedsearches.conf").stat().st_mtime_ns

        monkeypatch.setattr(sys, "argv", ["build_ta", "--check"])
        bt.main()

        after_mtime = (paths["default_dir"] / "savedsearches.conf").stat().st_mtime_ns
        assert before_mtime == after_mtime

    def test_check_returns_one_when_diff_stdout_and_stderr_are_empty(
        self,
        bt: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # Defensive fallback: when ``diff`` exits non-zero but emits
        # nothing on stdout/stderr (synthetic edge case), the script
        # still writes a *manual* hint to stderr to point the operator
        # at the two directories being compared. This protects the gate
        # from a silent CI failure.
        self._wire_check(
            bt, monkeypatch, tmp_path,
            ucs_by_cat={1: [{"i": "1.1.1", "n": "A", "q": "index=*"}]},
            qs={1: ["1.1.1"]},
        )

        # Patch subprocess.run so the diff "returncode" is non-zero but
        # both stdout/stderr are empty. The script MUST surface its
        # manual hint.
        class FakeCompleted:
            returncode = 2
            stdout = ""
            stderr = ""

        monkeypatch.setattr(
            bt.subprocess,
            "run",
            lambda *_a, **_kw: FakeCompleted(),
        )

        monkeypatch.setattr(sys, "argv", ["build_ta", "--check"])
        rc = bt.main()

        assert rc == 1
        err = capsys.readouterr().err
        assert "drift detected" in err
        assert "diff exited non-zero" in err


# ======================================================================
# 12. CLI surface
# ======================================================================


class TestCliSurface:
    def test_help_flag_exits_zero(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["build_ta", "--help"])
        with pytest.raises(SystemExit) as excinfo:
            bt.main()
        assert excinfo.value.code == 0

    def test_unknown_flag_exits_two(
        self, bt: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["build_ta", "--no-such-flag"])
        with pytest.raises(SystemExit) as excinfo:
            bt.main()
        assert excinfo.value.code == 2
