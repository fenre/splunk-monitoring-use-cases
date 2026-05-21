"""Hermetic unit tests for ``scripts/build_es.py``.

``build_es.py`` packages the security-category UCs from ``catalog.json``
into a real Splunk Enterprise Security TA layout under
``ta/DA-ESS-monitoring-use-cases/default/`` (correlation searches,
governance, analytic stories, eventtypes, tags, nav). It is tier-2
ratchet material (named explicitly in ``coverage_budget.py``'s
``TIER2_REGEXES``).

We care about three failure surfaces:

* **Correlation-search shape** — a UC promoted to a correlation search
  whose SPL doesn't start with ``index=`` / ``| tstats`` would fire on
  every event in the searchable universe (ES default scheduler =
  guaranteed CPU spike). The ``_fits_correlation_search`` heuristic
  is the only thing between us and that. Pin the contract.
* **Cap-driven shipped count** — the default pack caps critical/high
  UCs to 400/250. Removing those caps without an ADR would silently
  blow a small ES deployment up to 1,500+ disabled searches.
* **--check exit semantics** — gate must exit 0 on parity, 1 on
  drift, with a stderr diff that names the file. Confusing those two
  states would let CI silently bless TA drift.

Everything is monkey-patched into ``tmp_path`` so the real
``catalog.json`` and ``ta/DA-ESS-monitoring-use-cases`` tree are never
touched. The ``main()`` CLI is exercised end-to-end with captured
stdout/stderr.
"""

from __future__ import annotations

import datetime
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
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_es.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_es", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_es"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def bs() -> ModuleType:
    """Return a fresh import of ``build_es``.

    ``module``-scope would let constants like ``CATALOG`` / ``APP_DIR``
    / ``DEFAULT_DIR`` leak across tests, defeating ``monkeypatch.setattr``
    isolation.
    """
    return _load_module()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _patch_paths(
    bs: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    """Re-root every hard-coded input/output path into ``tmp_path``."""
    catalog = tmp_path / "catalog.json"
    app_dir = tmp_path / "ta" / "DA-ESS-monitoring-use-cases"
    default_dir = app_dir / "default"
    repo_root = tmp_path

    monkeypatch.setattr(bs, "CATALOG", str(catalog))
    monkeypatch.setattr(bs, "APP_DIR", str(app_dir))
    monkeypatch.setattr(bs, "DEFAULT_DIR", str(default_dir))
    monkeypatch.setattr(bs, "REPO_ROOT", str(repo_root))

    return {
        "catalog": catalog,
        "app_dir": app_dir,
        "default_dir": default_dir,
        "repo_root": repo_root,
    }


def _seed_catalog(
    catalog_path: Path,
    *,
    ucs_by_cat: dict[int, list[dict[str, Any]]] | None = None,
) -> None:
    """Write a minimal catalog.json with UCs keyed by category number."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    data: list[dict[str, Any]] = []
    for cat_num, ucs in (ucs_by_cat or {}).items():
        data.append({
            "i": cat_num,
            "s": [{"i": f"{cat_num}.1", "u": list(ucs)}],
        })
    catalog_path.write_text(json.dumps({"DATA": data}), encoding="utf-8")


def _make_uc(
    uid: str,
    *,
    name: str = "Probe",
    spl: str = "index=foo | stats count",
    crit: str = "medium",
    mitre: list[str] | None = None,
    value: str | None = None,
    kfp: str | None = None,
) -> dict[str, Any]:
    """Build a UC dict that satisfies the build_es promotion heuristics."""
    uc: dict[str, Any] = {"i": uid, "n": name, "q": spl, "c": crit}
    if mitre is not None:
        uc["mitre"] = list(mitre)
    if value is not None:
        uc["v"] = value
    if kfp is not None:
        uc["kfp"] = kfp
    return uc


# ======================================================================
# 1. Module-level constants & contracts
# ======================================================================


class TestModuleConstants:
    def test_security_cats_is_the_v52_set(self, bs: ModuleType) -> None:
        # The v5.1 -> v5.2 ES promotion gates 5 categories (identity,
        # endpoint, OT, zero-trust, compliance). Adding a category here
        # without ADR review would silently expand the TA's footprint.
        assert bs.SECURITY_CATS == {9, 10, 14, 17, 22}

    def test_crit_to_es_has_all_four_levels(self, bs: ModuleType) -> None:
        # Every catalog criticality value must map to an ES tuple; the
        # missing-key fallback in ``render_savedsearches`` is a defensive
        # safety net, not a sanctioned escape hatch.
        assert set(bs.CRIT_TO_ES.keys()) == {"critical", "high", "medium", "low"}

    def test_crit_to_es_tuples_are_5_long(self, bs: ModuleType) -> None:
        # 5-tuple = (urgency:int, severity_label:str, cron:str,
        # earliest:str, latest:str). Reordering would mis-emit ES
        # severity/urgency fields silently — Notable would show wrong
        # urgency colour.
        for crit, row in bs.CRIT_TO_ES.items():
            assert isinstance(row, tuple) and len(row) == 5, crit
            urgency, label, cron, earliest, latest = row
            assert isinstance(urgency, int), crit
            assert isinstance(label, str), crit
            assert isinstance(cron, str), crit
            assert isinstance(earliest, str), crit
            assert isinstance(latest, str), crit

    def test_crit_to_es_urgency_decreases_monotonically(
        self, bs: ModuleType
    ) -> None:
        # critical(5) > high(4) > medium(3) > low(2). Lossily-rotating
        # this ladder would silently downgrade real critical UCs to
        # informational notables.
        u = {k: v[0] for k, v in bs.CRIT_TO_ES.items()}
        assert u["critical"] > u["high"] > u["medium"] > u["low"]

    def test_crit_to_es_severity_labels_are_consistent_with_urgency(
        self, bs: ModuleType
    ) -> None:
        # ``critical`` -> "high", ``high`` -> "medium",
        # ``medium``/``low`` -> "informational". Ensures the human-readable
        # label tracks the urgency rank.
        assert bs.CRIT_TO_ES["critical"][1] == "high"
        assert bs.CRIT_TO_ES["high"][1] == "medium"
        assert bs.CRIT_TO_ES["medium"][1] == "informational"
        assert bs.CRIT_TO_ES["low"][1] == "informational"

    def test_tactic_by_prefix_keys_are_technique_ids(
        self, bs: ModuleType
    ) -> None:
        # Every key MUST be a parent MITRE technique ID (``T<digits>``);
        # sub-techniques ``.NNN`` are normalised out in
        # ``render_analytic_stories`` so they MUST NOT appear as keys.
        for key in bs.TACTIC_BY_PREFIX:
            assert key.startswith("T") and key[1:].isdigit(), key
            assert "." not in key, key

    def test_tactic_by_prefix_values_are_known_tactics(
        self, bs: ModuleType
    ) -> None:
        # Limit the surface to the 14 canonical MITRE Enterprise tactics.
        # A typo here would silently route a correlation search to a
        # phantom Analytic Story stanza.
        valid = {
            "Reconnaissance", "Resource Development", "Initial Access",
            "Execution", "Persistence", "Privilege Escalation",
            "Defense Evasion", "Credential Access", "Discovery",
            "Lateral Movement", "Collection", "Command and Control",
            "Exfiltration", "Impact",
        }
        for k, v in bs.TACTIC_BY_PREFIX.items():
            assert v in valid, (k, v)

    def test_eventtypes_es_are_3_tuples(self, bs: ModuleType) -> None:
        assert isinstance(bs.EVENTTYPES_ES, list)
        for row in bs.EVENTTYPES_ES:
            assert len(row) == 3, row
            name, search, desc = row
            assert name.startswith("ess_"), name
            assert isinstance(search, str) and search, search
            assert isinstance(desc, str), desc

    def test_conf_header_includes_generated_warning(self, bs: ModuleType) -> None:
        assert "GENERATED by scripts/build_es.py" in bs.CONF_HEADER
        assert "DO NOT EDIT" in bs.CONF_HEADER

    def test_max_caps_are_documented_constants(self, bs: ModuleType) -> None:
        # The default pack ships at most MAX_CRITICAL + MAX_HIGH
        # correlation searches. Removing/inflating these would silently
        # change the default TA install size.
        assert bs.MAX_CRITICAL == 400
        assert bs.MAX_HIGH == 250

    def test_nav_xml_references_repo(self, bs: ModuleType) -> None:
        assert "<nav" in bs.NAV_XML
        assert "fenre.github.io/splunk-monitoring-use-cases" in bs.NAV_XML


# ======================================================================
# 2. load_catalog (error paths matter — CI relies on them)
# ======================================================================


class TestLoadCatalog:
    def test_returns_parsed_json(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        paths["catalog"].write_text('{"DATA": []}', encoding="utf-8")
        assert bs.load_catalog() == {"DATA": []}

    def test_missing_file_exits_with_actionable_message(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # ``catalog.json`` is the SSOT input; a stale operator who runs
        # ``build_es.py`` before ``make build`` MUST get a clear error
        # message, not a Python traceback.
        _patch_paths(bs, monkeypatch, tmp_path)
        with pytest.raises(SystemExit) as exc:
            bs.load_catalog()
        err = capsys.readouterr().err
        assert "catalog.json not found" in str(exc.value) or "catalog.json not found" in err
        assert "make build" in str(exc.value) or "make build" in err

    def test_invalid_json_exits_with_decoder_error(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        paths["catalog"].write_text("{ not json", encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            bs.load_catalog()
        err = capsys.readouterr().err
        message = str(exc.value) + err
        assert "invalid JSON" in message


# ======================================================================
# 3. iter_security_ucs
# ======================================================================


class TestIterSecurityUcs:
    def test_emits_only_ucs_from_security_categories(self, bs: ModuleType) -> None:
        catalog = {
            "DATA": [
                {"i": 9, "s": [{"i": "9.1", "u": [{"i": "9.1.1", "n": "A"}]}]},
                {"i": 5, "s": [{"i": "5.1", "u": [{"i": "5.1.1", "n": "drop"}]}]},
                {"i": 22, "s": [{"i": "22.1", "u": [{"i": "22.1.1", "n": "C"}]}]},
            ]
        }
        ucs = list(bs.iter_security_ucs(catalog))
        assert [uc["i"] for uc in ucs] == ["9.1.1", "22.1.1"]

    def test_stamps_each_uc_with_cat_number(self, bs: ModuleType) -> None:
        catalog = {
            "DATA": [
                {"i": 10, "s": [{"i": "10.1", "u": [{"i": "10.1.1", "n": "A"}]}]},
            ]
        }
        ucs = list(bs.iter_security_ucs(catalog))
        assert ucs[0]["_cat"] == 10

    def test_empty_catalog_yields_nothing(self, bs: ModuleType) -> None:
        assert list(bs.iter_security_ucs({})) == []
        assert list(bs.iter_security_ucs({"DATA": []})) == []

    def test_skips_subcategories_with_no_ucs(self, bs: ModuleType) -> None:
        catalog = {
            "DATA": [
                {"i": 9, "s": [{"i": "9.1", "u": []}, {"i": "9.2", "u": [{"i": "9.2.1"}]}]},
            ]
        }
        ucs = list(bs.iter_security_ucs(catalog))
        assert [uc["i"] for uc in ucs] == ["9.2.1"]


# ======================================================================
# 4. _fits_correlation_search
# ======================================================================


class TestFitsCorrelationSearch:
    @pytest.mark.parametrize("spl", [
        "index=foo | stats count",
        "search index=bar | dedup user",
        "| tstats count from datamodel=Authentication",
        "  index=baz | timechart count  ",  # leading whitespace
        "INDEX=FOO | STATS COUNT",  # case-insensitive
    ])
    def test_accepts_filter_first_aggregating_spl(
        self, bs: ModuleType, spl: str
    ) -> None:
        assert bs._fits_correlation_search(spl) is True

    @pytest.mark.parametrize("spl", [
        "",  # empty
        None,  # missing (callers use `uc.get("q") or ""`)
        "| eval x=1",  # missing index= / tstats prefix
        "search * | stats count",  # `search` alone is too broad
        "datamodel Authentication",  # no aggregation
        "index=foo",  # filter-first but no aggregation
    ])
    def test_rejects_non_filter_first_or_unaggregated_spl(
        self, bs: ModuleType, spl: str | None
    ) -> None:
        # The callers feed ``uc.get("q") or ""`` so None must round-trip
        # to False without a TypeError.
        if spl is None:
            assert bs._fits_correlation_search("") is False
        else:
            assert bs._fits_correlation_search(spl) is False

    def test_accepts_streamstats_as_aggregation(self, bs: ModuleType) -> None:
        # ``| streamstats`` is in the aggregation list — explicit test
        # so a future refactor doesn't accidentally drop it.
        assert bs._fits_correlation_search(
            "index=foo | streamstats current=f count"
        ) is True

    def test_accepts_where_as_aggregation(self, bs: ModuleType) -> None:
        assert bs._fits_correlation_search("index=foo | where x>0") is True


# ======================================================================
# 5. _stanza_name / _uc_value helpers
# ======================================================================


class TestStanzaName:
    def test_uses_escs_prefix(self, bs: ModuleType) -> None:
        # The "ESCS-" prefix MUST appear so analysts can grep the
        # ES UI's correlation-search list for catalogue-origin rules.
        out = bs._stanza_name({"i": "10.1.1", "n": "Foo"})
        assert out.startswith("ESCS-10.1.1")

    def test_strips_brackets_to_avoid_conf_breakage(self, bs: ModuleType) -> None:
        # Splunk .conf parsers terminate stanzas on ``]``; brackets in
        # UC titles MUST be replaced with parentheses.
        out = bs._stanza_name({"i": "10.1.1", "n": "Foo [Bar] baz"})
        assert out == "ESCS-10.1.1 - Foo (Bar) baz"

    def test_falls_back_when_id_missing(self, bs: ModuleType) -> None:
        assert bs._stanza_name({"n": "X"}).startswith("ESCS-? -")

    def test_falls_back_when_name_missing(self, bs: ModuleType) -> None:
        assert bs._stanza_name({"i": "10.1.1"}) == "ESCS-10.1.1 - Untitled"


class TestUcValueOneLine:
    def test_collapses_newlines_to_spaces(self, bs: ModuleType) -> None:
        # ``description =`` is a single-line conf key; embedded
        # ``\n`` would terminate the value early. The script swaps each
        # ``\n`` for a single space (``str.replace("\n", " ")``), so the
        # multi-line value collapses to "a b c".
        assert bs._uc_value_one_line({"v": "a\nb\nc"}) == "a b c"
        out = bs._uc_value_one_line({"v": "a\nb\nc"})
        assert "\n" not in out
        assert out.startswith("a") and out.endswith("c")

    def test_strips_leading_and_trailing_whitespace(self, bs: ModuleType) -> None:
        assert bs._uc_value_one_line({"v": "   foo   "}) == "foo"

    def test_strips_carriage_returns(self, bs: ModuleType) -> None:
        out = bs._uc_value_one_line({"v": "a\r\nb"})
        assert "\r" not in out

    def test_returns_empty_string_when_missing(self, bs: ModuleType) -> None:
        # ``description = UC-X: name.`` MUST work even when ``v`` is
        # missing — the trailing space + period is acceptable, but a
        # ``None`` slip would crash render_savedsearches.
        assert bs._uc_value_one_line({}) == ""

    def test_returns_empty_string_when_value_is_falsy(self, bs: ModuleType) -> None:
        # An empty string in ``v`` is a valid catalogue value; the
        # ``or ""`` guard must still collapse it cleanly.
        assert bs._uc_value_one_line({"v": ""}) == ""


class TestUcValueRuleDescription:
    def test_returns_first_line(self, bs: ModuleType) -> None:
        # rule_description is shown as the lead paragraph in ES Notable
        # event details; we MUST extract only the first line so we don't
        # bury the rest of the value blurb in a single-line field.
        assert bs._uc_value_rule_description({"v": "First line.\nMore detail."}) == "First line."

    def test_returns_empty_when_missing(self, bs: ModuleType) -> None:
        assert bs._uc_value_rule_description({}) == ""

    def test_returns_empty_when_whitespace_only(self, bs: ModuleType) -> None:
        # Whitespace-only ``v`` MUST collapse to "" (not " " or "\n")
        # so the conf line is ``rule_description = `` rather than
        # carrying invisible whitespace into the ES UI.
        assert bs._uc_value_rule_description({"v": "   \n   "}) == ""

    def test_strips_internal_leading_whitespace(self, bs: ModuleType) -> None:
        # ``v`` may have indented multi-line content; the FIRST stripped
        # line is what we want.
        assert bs._uc_value_rule_description({"v": "  First.\nSecond."}) == "First."


class TestEscapeConf:
    def test_single_line_is_stripped(self, bs: ModuleType) -> None:
        assert bs._escape_conf("  index=foo  ") == "index=foo"

    def test_multiline_uses_backslash_newline(self, bs: ModuleType) -> None:
        # ``search =`` MUST use ``\\\n`` continuation; a bare newline
        # would silently terminate the key.
        out = bs._escape_conf("a\nb\nc")
        assert out == "a \\\nb \\\nc"

    def test_strips_trailing_whitespace_from_continuation_lines(
        self, bs: ModuleType
    ) -> None:
        # Splunk preserves trailing whitespace before ``\\`` — strip it
        # so the SPL value is byte-stable across regenerations.
        out = bs._escape_conf("a   \nb   \nc")
        assert out == "a \\\nb \\\nc"


# ======================================================================
# 6. render_savedsearches
# ======================================================================


class TestRenderSavedsearches:
    def test_emits_header_and_terminates_with_newline(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([])
        assert out.startswith(bs.CONF_HEADER)
        assert out.endswith("\n")

    def test_emits_all_correlation_search_keys_for_one_uc(
        self, bs: ModuleType
    ) -> None:
        # Snapshot-style assertion: every load-bearing key MUST appear.
        # If a future refactor drops one (e.g. ``action.notable = 1``)
        # the resulting TA would silently stop creating notables.
        uc = _make_uc("10.1.1", name="Probe", spl="index=foo | stats count",
                      crit="critical", mitre=["T1059"], value="Stops fires",
                      kfp="see lookup")
        out = bs.render_savedsearches([uc])

        for key in [
            "description = UC-10.1.1: Probe. Stops fires",
            "search = index=foo | stats count",
            "cron_schedule = */15 * * * *",
            "dispatch.earliest_time = -30m@m",
            "dispatch.latest_time = now",
            "enableSched = 0",
            "is_scheduled = 0",
            "disabled = 1",
            "action.correlationsearch = 1",
            "action.correlationsearch.label = UC-10.1.1: Probe",
            "action.notable = 1",
            "action.notable.param.rule_title = UC-10.1.1: Probe",
            "action.notable.param.rule_description = Stops fires",
            "action.notable.param.severity = high",
            "action.notable.param.urgency = 5",
            "action.notable.param.drilldown_name = $name$",
            "action.notable.param.drilldown_search = $drilldown_search$",
            "action.risk = 0",
            "action.risk.param._risk_score = 40",
            "action.risk.param._risk_object = host",
            "action.risk.param._risk_object_type = system",
            "action.notable.param.mitre_attack_id = T1059",
            "action.notable.param.rule_ack_comment = Known false positives: see lookup",
        ]:
            assert key in out, key

    def test_unknown_criticality_falls_back_to_medium(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([
            _make_uc("10.1.1", crit="unknown")
        ])
        # medium row: urgency=3, severity=informational, cron=every 2h
        assert "action.notable.param.urgency = 3" in out
        assert "action.notable.param.severity = informational" in out
        assert "cron_schedule = 0 */2 * * *" in out

    def test_missing_criticality_falls_back_to_medium(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([
            _make_uc("10.1.1", crit="").replace if False else {
                "i": "10.1.1", "n": "X", "q": "index=*"
            }
        ])
        # The defensive ``(uc.get("c") or "medium")`` guard MUST keep the
        # stanza emit-able even when the catalogue is missing ``c``.
        assert "action.notable.param.urgency = 3" in out

    def test_uppercase_criticality_normalised(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([
            _make_uc("10.1.1", crit="HIGH")
        ])
        assert "action.notable.param.urgency = 4" in out
        assert "action.notable.param.severity = medium" in out

    def test_skips_mitre_line_when_field_missing(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([_make_uc("10.1.1")])
        assert "action.notable.param.mitre_attack_id" not in out

    def test_skips_mitre_line_when_empty_list(self, bs: ModuleType) -> None:
        # Empty list is falsy; emitting ``mitre_attack_id = `` would be
        # a silent ES schema break.
        out = bs.render_savedsearches([_make_uc("10.1.1", mitre=[])])
        assert "action.notable.param.mitre_attack_id" not in out

    def test_joins_multiple_mitre_techniques_with_comma(self, bs: ModuleType) -> None:
        # ES Notable parses this field by comma; whitespace-padded values
        # would silently mismatch ATT&CK lookups.
        out = bs.render_savedsearches([
            _make_uc("10.1.1", mitre=["T1059", "T1078"])
        ])
        assert "action.notable.param.mitre_attack_id = T1059,T1078" in out

    def test_skips_kfp_when_absent(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([_make_uc("10.1.1")])
        assert "rule_ack_comment" not in out

    def test_skips_kfp_when_empty_string(self, bs: ModuleType) -> None:
        # An empty ``kfp`` is falsy — same as missing — to avoid the
        # empty ``rule_ack_comment = Known false positives:`` shape that
        # would silently leak into the ES UI.
        out = bs.render_savedsearches([_make_uc("10.1.1", kfp="")])
        assert "rule_ack_comment" not in out

    def test_upstream_reference_is_anchored_to_uc_id(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([_make_uc("10.1.1")])
        assert "#use-case-10.1.1" in out
        # The reference MUST live in a comment line so .conf parsers
        # ignore it.
        for line in out.splitlines():
            if "use-case-10.1.1" in line:
                assert line.startswith("#")
                break
        else:  # pragma: no cover - sanity guard
            pytest.fail("upstream reference comment not found in output")

    def test_multiline_spl_is_continuation_escaped(self, bs: ModuleType) -> None:
        out = bs.render_savedsearches([
            _make_uc("10.1.1", spl="index=foo\n| stats count")
        ])
        assert "search = index=foo \\\n| stats count" in out

    def test_handles_missing_uc_name_in_label_keys(self, bs: ModuleType) -> None:
        # ``action.correlationsearch.label`` references ``uc.get("n", "")``
        # — when missing it falls back to an empty string, NOT to a
        # ``None`` crash.
        out = bs.render_savedsearches([{"i": "10.1.1", "q": "index=*"}])
        assert "action.correlationsearch.label = UC-10.1.1: " in out


# ======================================================================
# 7. render_governance
# ======================================================================


class TestRenderGovernance:
    def test_emits_header_and_terminates_with_newline(self, bs: ModuleType) -> None:
        out = bs.render_governance([])
        assert out.startswith(bs.CONF_HEADER)
        assert out.endswith("\n")

    def test_skips_ucs_without_mitre(self, bs: ModuleType) -> None:
        out = bs.render_governance([_make_uc("10.1.1")])
        # No stanza body — only the header and trailing newline.
        assert "ESCS-10.1.1" not in out

    def test_emits_governance_block_per_tagged_uc(self, bs: ModuleType) -> None:
        out = bs.render_governance([_make_uc("10.1.1", mitre=["T1059"])])
        assert "[ESCS-10.1.1 - Probe]" in out
        assert "governance = mitre_attack" in out
        assert "mitre_attack = T1059" in out

    def test_derives_tactics_from_technique_prefixes(self, bs: ModuleType) -> None:
        # T1059 -> Execution, T1078 -> Initial Access. Sorted output for
        # deterministic .conf.
        out = bs.render_governance([
            _make_uc("10.1.1", mitre=["T1078", "T1059"])
        ])
        assert "mitre_attack_tactics = Execution,Initial Access" in out

    def test_normalises_subtechniques_to_parent(self, bs: ModuleType) -> None:
        # ``T1059.001`` (PowerShell sub-technique) MUST resolve to the
        # parent's tactic (Execution); if the script tries to look up
        # the full sub-technique string in TACTIC_BY_PREFIX it would
        # silently drop the mapping.
        out = bs.render_governance([
            _make_uc("10.1.1", mitre=["T1059.001"])
        ])
        assert "mitre_attack_tactics = Execution" in out

    def test_omits_tactic_line_when_no_known_techniques(self, bs: ModuleType) -> None:
        # ``T9999`` is unknown — the tactic line MUST be omitted rather
        # than emitting ``mitre_attack_tactics = `` (which ES would
        # silently parse as "no tactics").
        out = bs.render_governance([
            _make_uc("10.1.1", mitre=["T9999"])
        ])
        assert "mitre_attack = T9999" in out
        assert "mitre_attack_tactics" not in out


# ======================================================================
# 8. render_analytic_stories
# ======================================================================


class TestRenderAnalyticStories:
    def test_emits_header_and_terminates_with_newline(self, bs: ModuleType) -> None:
        out = bs.render_analytic_stories([])
        assert out.startswith(bs.CONF_HEADER)
        assert out.endswith("\n")

    def test_groups_searches_by_first_known_tactic(self, bs: ModuleType) -> None:
        # T1059 -> Execution; both UCs land in the same Analytic Story.
        out = bs.render_analytic_stories([
            _make_uc("10.1.1", mitre=["T1059"]),
            _make_uc("10.1.2", mitre=["T1059", "T1078"]),
        ])
        assert "[analytic_story://mu_execution]" in out
        # Both detections appear in the comma-separated list.
        assert "ESCS-10.1.1 - Probe" in out
        assert "ESCS-10.1.2 - Probe" in out

    def test_stanza_name_lowercases_and_underscores_tactic(
        self, bs: ModuleType
    ) -> None:
        # "Lateral Movement" -> "lateral_movement"; spaces are illegal
        # in stanza paths, uppercase would break stanza lookups.
        out = bs.render_analytic_stories([
            _make_uc("10.1.1", mitre=["T1021"]),
        ])
        assert "[analytic_story://mu_lateral_movement]" in out

    def test_emits_required_analytic_story_fields(self, bs: ModuleType) -> None:
        out = bs.render_analytic_stories([
            _make_uc("10.1.1", mitre=["T1059"]),
        ])
        # Required schema fields: category, description, narrative,
        # last_updated, version, detections.
        assert "category = " in out
        assert "description = " in out
        assert "narrative = " in out
        assert "last_updated = " in out
        assert "version = 1" in out
        assert "detections = " in out

    def test_last_updated_uses_iso_date(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pin ``date.today()`` so the test is stable across UTC midnight.
        class FakeDate(datetime.date):
            @classmethod
            def today(cls) -> datetime.date:
                return datetime.date(2026, 5, 20)

        monkeypatch.setattr(bs.datetime, "date", FakeDate)
        out = bs.render_analytic_stories([
            _make_uc("10.1.1", mitre=["T1059"]),
        ])
        assert "last_updated = 2026-05-20" in out

    def test_skips_ucs_without_known_mitre_tactic(self, bs: ModuleType) -> None:
        # A UC tagged with only an unknown technique MUST NOT contribute
        # to any Analytic Story.
        out = bs.render_analytic_stories([
            _make_uc("10.1.1", mitre=["T9999"]),
        ])
        # No analytic_story stanza beyond the header.
        assert "analytic_story://" not in out

    def test_uses_first_known_technique_to_decide_tactic(
        self, bs: ModuleType
    ) -> None:
        # The ``for ... break`` loop attaches each UC to the FIRST
        # known-technique tactic. So ``[T9999, T1059]`` lands in
        # Execution (T1059's tactic), NOT some phantom T9999 group.
        out = bs.render_analytic_stories([
            _make_uc("10.1.1", mitre=["T9999", "T1059"]),
        ])
        assert "[analytic_story://mu_execution]" in out

    def test_detections_field_is_deduped(self, bs: ModuleType) -> None:
        # Two UCs with the same stanza name (synthetic) should appear
        # once. (We can't easily produce duplicate stanza names from
        # real catalogue data — the dedup is a defensive guard.)
        out = bs.render_analytic_stories([
            _make_uc("10.1.1", mitre=["T1059"]),
            # Same id+name -> same stanza name.
            _make_uc("10.1.1", mitre=["T1059"]),
        ])
        # ``ESCS-10.1.1 - Probe`` appears at most once in the detections
        # list (could be 0 if dedup elides it, but MUST not appear 2x).
        execution_block = out.split("[analytic_story://mu_execution]")[1]
        assert execution_block.count("ESCS-10.1.1 - Probe") == 1

    def test_skips_ucs_without_mitre_field(self, bs: ModuleType) -> None:
        out = bs.render_analytic_stories([_make_uc("10.1.1")])
        assert "analytic_story://" not in out


# ======================================================================
# 9. render_eventtypes / render_tags
# ======================================================================


class TestRenderEventtypes:
    def test_emits_every_entry_from_EVENTTYPES_ES(self, bs: ModuleType) -> None:
        out = bs.render_eventtypes()
        for name, _, _ in bs.EVENTTYPES_ES:
            assert f"[{name}]" in out

    def test_search_lines_are_emitted(self, bs: ModuleType) -> None:
        out = bs.render_eventtypes()
        for _, search, _ in bs.EVENTTYPES_ES:
            assert f"search = {search}" in out

    def test_description_lines_are_commented(self, bs: ModuleType) -> None:
        # ``description`` is NOT a valid eventtypes.conf key; emitting
        # it uncommented would fail AppInspect.
        out = bs.render_eventtypes()
        for _, _, desc in bs.EVENTTYPES_ES:
            assert f"#description = {desc}" in out


class TestRenderTags:
    def test_emits_one_stanza_per_eventtype(self, bs: ModuleType) -> None:
        out = bs.render_tags()
        for name, _, _ in bs.EVENTTYPES_ES:
            assert f"[eventtype={name}]" in out

    def test_groups_multi_tag_stanzas_under_single_header(
        self, bs: ModuleType
    ) -> None:
        # ``ess_auth_fail`` has both ``authentication`` AND ``failure``
        # tags — they MUST live under a single stanza header (Splunk
        # silently keeps only the last copy if duplicated).
        out = bs.render_tags()
        assert out.count("[eventtype=ess_auth_fail]") == 1
        block = out.split("[eventtype=ess_auth_fail]", 1)[1].split("[", 1)[0]
        assert "authentication = enabled" in block
        assert "failure = enabled" in block

    def test_emits_header(self, bs: ModuleType) -> None:
        assert bs.render_tags().startswith(bs.CONF_HEADER)


# ======================================================================
# 10. pick_ucs and the MAX_CRITICAL/MAX_HIGH caps
# ======================================================================


class TestPickUcs:
    def test_filters_to_security_categories(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], ucs_by_cat={
            # Promote to critical so the default-mode cap path keeps them.
            9: [_make_uc("9.1.1", crit="critical")],
            5: [_make_uc("5.1.1", crit="critical")],  # not in SECURITY_CATS
        })
        picked = bs.pick_ucs()
        assert {uc["i"] for uc in picked} == {"9.1.1"}

    def test_skips_ucs_that_dont_fit_correlation_search(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], ucs_by_cat={
            9: [
                _make_uc("9.1.1", spl="index=foo | stats count", crit="critical"),
                # No aggregation -> rejected by _fits_correlation_search.
                _make_uc("9.1.2", spl="index=foo", crit="critical"),
                # Empty SPL -> rejected.
                _make_uc("9.1.3", spl="", crit="critical"),
            ],
        })
        picked = bs.pick_ucs()
        assert [uc["i"] for uc in picked] == ["9.1.1"]

    def test_default_mode_caps_critical_and_high(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Lower the caps so the test runs fast but exercises the same
        # branch as production.
        monkeypatch.setattr(bs, "MAX_CRITICAL", 2)
        monkeypatch.setattr(bs, "MAX_HIGH", 1)
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        ucs: list[dict[str, Any]] = []
        for i in range(5):
            ucs.append(_make_uc(f"9.1.{i + 1}", crit="critical"))
        for i in range(3):
            ucs.append(_make_uc(f"9.1.{100 + i}", crit="high"))
        for i in range(2):
            ucs.append(_make_uc(f"9.1.{200 + i}", crit="medium"))
        _seed_catalog(paths["catalog"], ucs_by_cat={9: ucs})

        picked = bs.pick_ucs()
        # Default mode: 2 critical + 1 high = 3 total; medium dropped.
        assert len(picked) == 3
        crit_ids = [u["i"] for u in picked if u.get("c") == "critical"]
        high_ids = [u["i"] for u in picked if u.get("c") == "high"]
        med_ids = [u["i"] for u in picked if u.get("c") == "medium"]
        assert len(crit_ids) == 2
        assert len(high_ids) == 1
        assert med_ids == []

    def test_include_all_returns_every_passing_uc(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Lower caps to a synthetic value so the test would clearly fail
        # if include_all secretly applied them.
        monkeypatch.setattr(bs, "MAX_CRITICAL", 1)
        monkeypatch.setattr(bs, "MAX_HIGH", 1)
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        ucs = [
            _make_uc("9.1.1", crit="critical"),
            _make_uc("9.1.2", crit="critical"),
            _make_uc("9.1.3", crit="high"),
            _make_uc("9.1.4", crit="medium"),
            _make_uc("9.1.5", crit="low"),
        ]
        _seed_catalog(paths["catalog"], ucs_by_cat={9: ucs})

        picked = bs.pick_ucs(include_all=True)
        assert {uc["i"] for uc in picked} == {
            "9.1.1", "9.1.2", "9.1.3", "9.1.4", "9.1.5",
        }

    def test_empty_catalog_returns_empty_list(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"])
        assert bs.pick_ucs() == []
        assert bs.pick_ucs(include_all=True) == []


# ======================================================================
# 11. _build_file_map / _write_default_dir
# ======================================================================


class TestBuildFileMap:
    def test_emits_six_expected_files(self, bs: ModuleType) -> None:
        out = bs._build_file_map([_make_uc("10.1.1")])
        assert set(out.keys()) == {
            "savedsearches.conf",
            "governance.conf",
            "analytic_stories.conf",
            "eventtypes.conf",
            "tags.conf",
            "data/ui/nav/default.xml",
        }

    def test_nav_xml_value_matches_constant(self, bs: ModuleType) -> None:
        out = bs._build_file_map([])
        assert out["data/ui/nav/default.xml"] == bs.NAV_XML


class TestWriteDefaultDir:
    def test_writes_each_file_with_correct_content(
        self, bs: ModuleType, tmp_path: Path
    ) -> None:
        files = {
            "savedsearches.conf": "[X]\n",
            "data/ui/nav/default.xml": "<nav/>\n",
        }
        default_dir = tmp_path / "es_default"
        bs._write_default_dir(str(default_dir), files, verbose=False)
        assert (default_dir / "savedsearches.conf").read_text() == "[X]\n"
        assert (default_dir / "data" / "ui" / "nav" / "default.xml").read_text() == "<nav/>\n"

    def test_verbose_prints_one_line_per_file(
        self, bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # Re-root REPO_ROOT so the printed relpath is predictable.
        monkeypatch.setattr(bs, "REPO_ROOT", str(tmp_path))
        files = {"savedsearches.conf": "[Y]\n"}
        default_dir = tmp_path / "es_default"
        bs._write_default_dir(str(default_dir), files, verbose=True)
        out = capsys.readouterr().out
        assert "wrote es_default/savedsearches.conf" in out
        assert "(4 chars)" in out  # len("[Y]\n") == 4

    def test_creates_nav_dir_even_for_empty_filemap(
        self, bs: ModuleType, tmp_path: Path
    ) -> None:
        # The nav directory is created up-front so the first run is
        # always able to write data/ui/nav/default.xml without a
        # second pre-creation pass.
        default_dir = tmp_path / "es_default"
        bs._write_default_dir(str(default_dir), {}, verbose=False)
        assert (default_dir / "data" / "ui" / "nav").is_dir()


# ======================================================================
# 12. main() — write mode
# ======================================================================


class TestMainWriteMode:
    def _seed_full_repo(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        ucs_by_cat: dict[int, list[dict[str, Any]]],
    ) -> dict[str, Path]:
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], ucs_by_cat=ucs_by_cat)
        return paths

    def test_returns_zero_and_writes_all_six_files(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = self._seed_full_repo(
            bs, monkeypatch, tmp_path,
            # Promote to critical so it survives the MAX_CRITICAL/MAX_HIGH
            # cap inside ``pick_ucs`` (medium UCs are dropped in default mode).
            ucs_by_cat={9: [_make_uc("9.1.1", crit="critical")]},
        )

        monkeypatch.setattr(sys, "argv", ["build_es"])
        rc = bs.main()

        assert rc == 0
        for rel in [
            "savedsearches.conf",
            "governance.conf",
            "analytic_stories.conf",
            "eventtypes.conf",
            "tags.conf",
            "data/ui/nav/default.xml",
        ]:
            assert (paths["default_dir"] / rel).exists(), rel

        out = capsys.readouterr().out
        assert "correlation searches: 1" in out

    def test_prints_zero_when_no_security_ucs(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        self._seed_full_repo(
            bs, monkeypatch, tmp_path,
            ucs_by_cat={5: [_make_uc("5.1.1")]},  # non-security cat
        )
        monkeypatch.setattr(sys, "argv", ["build_es"])
        rc = bs.main()
        assert rc == 0
        assert "correlation searches: 0" in capsys.readouterr().out

    def test_include_all_flag_increases_uc_count(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # Lower caps so we can clearly observe the gap between default
        # and --include-all without seeding hundreds of UCs.
        monkeypatch.setattr(bs, "MAX_CRITICAL", 1)
        monkeypatch.setattr(bs, "MAX_HIGH", 1)

        self._seed_full_repo(
            bs, monkeypatch, tmp_path,
            ucs_by_cat={9: [
                _make_uc("9.1.1", crit="critical"),
                _make_uc("9.1.2", crit="critical"),
                _make_uc("9.1.3", crit="medium"),
            ]},
        )
        monkeypatch.setattr(sys, "argv", ["build_es", "--include-all"])
        rc = bs.main()
        assert rc == 0
        assert "correlation searches: 3" in capsys.readouterr().out


# ======================================================================
# 13. main() — --check mode
# ======================================================================


class TestMainCheckMode:
    def _wire_check(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        ucs_by_cat: dict[int, list[dict[str, Any]]],
        seed_default: bool = True,
    ) -> dict[str, Path]:
        paths = _patch_paths(bs, monkeypatch, tmp_path)
        _seed_catalog(paths["catalog"], ucs_by_cat=ucs_by_cat)
        if seed_default:
            ucs = bs.pick_ucs()
            files = bs._build_file_map(ucs)
            bs._write_default_dir(str(paths["default_dir"]), files, verbose=False)
        return paths

    def test_returns_zero_when_default_matches_freshly_generated(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        self._wire_check(
            bs, monkeypatch, tmp_path,
            ucs_by_cat={9: [_make_uc("9.1.1")]},
        )
        monkeypatch.setattr(sys, "argv", ["build_es", "--check"])
        rc = bs.main()
        assert rc == 0
        out = capsys.readouterr().out
        assert "build_es output is up to date." in out

    def test_returns_one_and_writes_diff_to_stderr_on_drift(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        paths = self._wire_check(
            bs, monkeypatch, tmp_path,
            ucs_by_cat={9: [_make_uc("9.1.1")]},
        )
        # Tamper with the on-disk savedsearches.conf to force a diff.
        (paths["default_dir"] / "savedsearches.conf").write_text(
            "OUT OF DATE\n", encoding="utf-8"
        )
        monkeypatch.setattr(sys, "argv", ["build_es", "--check"])
        rc = bs.main()
        err = capsys.readouterr().err
        assert rc == 1
        assert "drift detected" in err
        assert "savedsearches.conf" in err

    def test_returns_one_when_default_dir_missing_files(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # Mirror of build_ta's "uninstalled TA" test — a freshly cloned
        # repo where ``ta/DA-ESS-monitoring-use-cases/default`` was never
        # regenerated MUST be caught.
        paths = self._wire_check(
            bs, monkeypatch, tmp_path,
            ucs_by_cat={9: [_make_uc("9.1.1")]},
        )
        (paths["default_dir"] / "savedsearches.conf").unlink()
        monkeypatch.setattr(sys, "argv", ["build_es", "--check"])
        rc = bs.main()
        assert rc == 1
        assert "drift detected" in capsys.readouterr().err

    def test_check_does_not_touch_real_default_dir(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        # The gate writes into a TemporaryDirectory and diffs only — if
        # it ever wrote to the real default/ dir, ``--check`` would
        # silently overwrite drift.
        paths = self._wire_check(
            bs, monkeypatch, tmp_path,
            ucs_by_cat={9: [_make_uc("9.1.1")]},
        )
        before = (paths["default_dir"] / "savedsearches.conf").stat().st_mtime_ns
        monkeypatch.setattr(sys, "argv", ["build_es", "--check"])
        bs.main()
        after = (paths["default_dir"] / "savedsearches.conf").stat().st_mtime_ns
        assert before == after

    def test_check_returns_one_when_diff_stdout_and_stderr_are_empty(
        self,
        bs: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture,
    ) -> None:
        # Defensive branch: ``diff`` exits non-zero but emits nothing on
        # stdout/stderr. The script falls back to a manual hint with the
        # two directory paths.
        self._wire_check(
            bs, monkeypatch, tmp_path,
            ucs_by_cat={9: [_make_uc("9.1.1")]},
        )

        class FakeCompleted:
            returncode = 2
            stdout = ""
            stderr = ""

        monkeypatch.setattr(
            bs.subprocess,
            "run",
            lambda *_a, **_kw: FakeCompleted(),
        )
        monkeypatch.setattr(sys, "argv", ["build_es", "--check"])
        rc = bs.main()
        assert rc == 1
        err = capsys.readouterr().err
        assert "drift detected" in err
        assert "diff exited non-zero" in err


# ======================================================================
# 14. CLI surface
# ======================================================================


class TestCliSurface:
    def test_help_flag_exits_zero(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["build_es", "--help"])
        with pytest.raises(SystemExit) as exc:
            bs.main()
        assert exc.value.code == 0

    def test_unknown_flag_exits_two(
        self, bs: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "argv", ["build_es", "--no-such-flag"])
        with pytest.raises(SystemExit) as exc:
            bs.main()
        assert exc.value.code == 2
