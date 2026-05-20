"""Hermetic coverage suite for ``splunk_uc.migrations.migrate_compliance_phase4``.

Brings the Phase 4 story-layer backfill driver from 7.7% to 100%
statement and branch coverage. Every test redirects ``REPO_ROOT``,
``CONTENT_DIR``, ``REGULATIONS_PATH`` and ``PHASE4_MANIFEST`` into a
``tmp_path`` so no live sidecar is ever touched.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from splunk_uc.migrations import migrate_compliance_phase4 as mp

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_regulations_doc() -> dict[str, Any]:
    """Minimal but realistic regulations.json shape used by the index."""
    return {
        "aliasIndex": {"NIST 800-53": "nist-800-53"},
        "frameworks": [
            {
                "id": "gdpr",
                "shortName": "GDPR",
                "tier": 1,
                "versions": [
                    {
                        "version": "2016/679",
                        "commonClauses": [
                            {
                                "clause": "Art.32",
                                "topic": "Security of processing",
                                "priorityWeight": 9.5,
                                "obligationText": "Has text",
                            },
                            {
                                "clause": "Art.33",
                                "topic": "Breach notification",
                                "priorityWeight": 8.0,
                            },
                        ],
                    }
                ],
            },
            {
                "id": "nist-800-53",
                "shortName": "NIST",
                "tier": 1,
                "versions": [
                    {
                        "version": "5",
                        "commonClauses": [
                            {
                                "clause": "AU-2",
                                "topic": "Event Logging",
                                "priorityWeight": 7.0,
                            }
                        ],
                    }
                ],
            },
            {
                "id": "iso-27001",
                "shortName": "ISO27001",
                "tier": 2,
                "versions": [
                    {
                        "version": "2022",
                        "commonClauses": [
                            {
                                "clause": "A.5.1",
                                "topic": "Policies",
                                "priorityWeight": 5.0,
                            }
                        ],
                    }
                ],
            },
            {
                # Empty framework — exercises the "tier_done==0 and no rows"
                # skip branch in build_obligation_manifest.
                "id": "empty-fw",
                "shortName": "EMP",
                "tier": 3,
                "versions": [],
            },
        ],
    }


def _make_sidecar(
    uc_id: str = "22.1.1",
    title: str = "GDPR audit logging",
    data_sources: Any = None,
    *,
    compliance: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if compliance is None:
        compliance = [
            {
                "regulation": "GDPR",
                "version": "2016/679",
                "clause": "Art.32",
                "mode": "satisfies",
            }
        ]
    return {
        "$schema": "../../schemas/uc.schema.json",
        "id": uc_id,
        "title": title,
        "criticality": "high",
        "difficulty": "medium",
        "dataSources": data_sources if data_sources is not None else "index=audit",
        "spl": "index=audit | stats count",
        "description": "desc",
        "value": "value",
        "compliance": compliance,
    }


@pytest.fixture
def fake_repo(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Tiny synthetic repo: content/cat-22/ + data/regulations.json."""
    content_dir = tmp_path / "content"
    cat22 = content_dir / "cat-22-compliance"
    cat22.mkdir(parents=True)
    data_dir = tmp_path / "data" / "per-regulation"
    data_dir.mkdir(parents=True)
    reg_path = tmp_path / "data" / "regulations.json"
    manifest_path = data_dir / "phase4-obligation-backfill.md"

    monkeypatch.setattr(mp, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mp, "CONTENT_DIR", content_dir)
    monkeypatch.setattr(mp, "REGULATIONS_PATH", reg_path)
    monkeypatch.setattr(mp, "PHASE4_MANIFEST", manifest_path)
    return tmp_path


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


class TestIOHelpers:
    def test_read_and_dump_round_trip(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "x.json"
        payload = {"k": "v"}
        mp._dump_json(path, payload)
        assert path.read_text(encoding="utf-8").endswith("\n")
        assert mp._read_json(path) == payload


class TestCanonicalOrdering:
    def test_canonical_sidecar_orders_known_fields_first(self) -> None:
        # Mix known + unknown keys; canonical order should put $schema, id,
        # title first then trailing unknowns at the end in original order.
        out = mp._canonical_sidecar(
            {"value": "v", "id": "1", "extra": True, "$schema": "s", "title": "t"}
        )
        keys = list(out.keys())
        assert keys[0] == "$schema"
        assert keys[1] == "id"
        assert keys[2] == "title"
        assert keys[3] == "value"
        assert "extra" in out

    def test_canonical_entry_orders_known_fields_first(self) -> None:
        out = mp._canonical_entry(
            {
                "evidenceArtifact": "ea",
                "regulation": "GDPR",
                "extra": 1,
                "clause": "Art.32",
            }
        )
        keys = list(out.keys())
        assert keys[0] == "regulation"
        assert "extra" in out


# ---------------------------------------------------------------------------
# RegulationsIndex
# ---------------------------------------------------------------------------


class TestRegulationsIndex:
    def test_resolves_by_canonical_id_short_name_alias_and_fallback(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        assert idx.resolve_id("GDPR") == "gdpr"  # by short name
        assert idx.resolve_id("gdpr") == "gdpr"  # by id
        assert idx.resolve_id("NIST 800-53") == "nist-800-53"  # alias
        # Fallback regex normalisation: "NIST/800-53" -> "nist-800-53"
        assert idx.resolve_id("NIST/800-53") == "nist-800-53"
        assert idx.resolve_id("") is None  # empty
        assert idx.resolve_id("Unknown reg") is None

    def test_resolves_when_short_name_lookup_id_is_blank(self) -> None:
        # Hit the "short_id.lower() or None" False branch: a framework
        # short-named so by_short is populated, but the resolved framework
        # has no canonical id at all.
        doc = {
            "frameworks": [
                {"id": "", "shortName": "Anon"},
            ]
        }
        idx = mp.RegulationsIndex(doc)
        assert idx.resolve_id("Anon") is None

    def test_index_handles_framework_with_id_but_no_short_name(self) -> None:
        # Pins the ``if short:`` False loop iteration branch in
        # ``__init__`` — id is present, shortName is missing.
        doc = {"frameworks": [{"id": "no-short"}]}
        idx = mp.RegulationsIndex(doc)
        assert idx.framework("no-short") is not None
        # No shortName means resolve-by-short does nothing.
        assert idx.resolve_id("") is None

    def test_clause_meta_returns_entry_when_triple_matches(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        meta = idx.clause_meta("gdpr", "2016/679", "Art.32")
        assert meta is not None and meta["topic"] == "Security of processing"

    def test_clause_meta_returns_none_when_framework_missing(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        assert idx.clause_meta("nope", "any", "any") is None

    def test_clause_meta_returns_none_when_version_or_clause_missing(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        assert idx.clause_meta("gdpr", "1999", "Art.32") is None
        assert idx.clause_meta("gdpr", "2016/679", "Art.99") is None

    def test_framework_returns_doc_or_none(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        assert idx.framework("gdpr")["shortName"] == "GDPR"
        assert idx.framework("nope") is None


# ---------------------------------------------------------------------------
# Text-helper utilities
# ---------------------------------------------------------------------------


class TestStringHelpers:
    def test_first_sentence_splits_on_first_terminator(self) -> None:
        assert mp._first_sentence("Hello. World.") == "Hello."

    def test_first_sentence_returns_fallback_when_empty(self) -> None:
        assert mp._first_sentence("", "default") == "default"
        # Falsy `fallback` returns ""
        assert mp._first_sentence("") == ""

    def test_shorten_truncates_with_ellipsis(self) -> None:
        long = "word " * 200  # ~1000 chars
        out = mp._shorten(long, 50)
        assert out.endswith("\u2026")
        assert len(out) <= 50

    def test_shorten_keeps_string_under_limit(self) -> None:
        assert mp._shorten("short", 50) == "short"

    def test_shorten_handles_word_boundary_under_40(self) -> None:
        # If last space is at index <= 40, do NOT trim at boundary; just
        # strip trailing punctuation and append ellipsis.
        out = mp._shorten("a" * 100, 30)  # no spaces anywhere
        assert out.endswith("\u2026")
        # No spaces in input → clip + ellipsis path (sp == -1).
        assert " " not in out.rstrip("\u2026")

    def test_pad_to_min_pads_below_minimum_with_space_separator(self) -> None:
        # Tail does NOT start with "." → ``" " + tail`` branch fires.
        out = mp._pad_to_min("hi", 10, "more here please")
        assert out.startswith("hi ")
        assert "more here please" in out

    def test_pad_to_min_appends_dot_tail_correctly(self) -> None:
        # Tail starts with "." → uses ``+ tail`` branch.
        out = mp._pad_to_min("hello", 50, ".trailing")
        assert ".trailing" in out

    def test_pad_to_min_returns_unchanged_when_long_enough(self) -> None:
        out = mp._pad_to_min("a" * 30, 10, ". x")
        assert out == "a" * 30

    def test_topic_phrase_uses_clause_meta_when_available(self) -> None:
        assert (
            mp._topic_phrase({"topic": "Logging"}, "AU-2") == "Logging"
        )

    def test_topic_phrase_falls_back_to_clause_then_default(self) -> None:
        assert mp._topic_phrase(None, "AU-2") == "AU-2"
        assert mp._topic_phrase(None, "") == "this requirement"


# ---------------------------------------------------------------------------
# synthesise_control_objective
# ---------------------------------------------------------------------------


class TestSynthesiseControlObjective:
    def test_satisfies_mode_emits_enforced_header(self) -> None:
        sentence = mp.synthesise_control_objective(
            uc={"id": "22.1.1", "title": "Audit"},
            entry={
                "regulation": "GDPR",
                "version": "2016/679",
                "clause": "Art.32",
                "mode": "satisfies",
            },
            clause_meta={"topic": "Security of processing"},
        )
        assert "GDPR Art.32" in sentence
        assert "(Security of processing)" in sentence
        assert "is enforced" in sentence
        assert "Splunk UC-22.1.1: Audit" in sentence

    def test_detects_violation_mode_does_not_append_is_enforced(self) -> None:
        sentence = mp.synthesise_control_objective(
            uc={"id": "22.1.1", "title": "Audit"},
            entry={
                "regulation": "GDPR",
                "version": "2016/679",
                "clause": "Art.32",
                "mode": "detects-violation-of",
            },
            clause_meta=None,
        )
        assert "Detects violations of" in sentence
        assert "is enforced" not in sentence

    def test_redundant_topic_is_dropped(self) -> None:
        # Topic identical to the clause code → suffix is suppressed.
        sentence = mp.synthesise_control_objective(
            uc={"id": "22.1.1", "title": "T"},
            entry={
                "regulation": "GDPR",
                "version": "v",
                "clause": "AU-2",
                "mode": "satisfies",
            },
            clause_meta={"topic": "AU-2"},
        )
        assert "(AU-2)" not in sentence

    def test_uses_fallback_regulator_label_when_regulation_blank(self) -> None:
        sentence = mp.synthesise_control_objective(
            uc={"id": "x", "title": "Audit"},
            entry={"regulation": "", "clause": "X", "mode": "satisfies"},
            clause_meta=None,
        )
        assert "regulator X" in sentence

    def test_uc_id_with_prefix_is_not_double_prefixed(self) -> None:
        sentence = mp.synthesise_control_objective(
            uc={"id": "UC-1.2.3", "title": "X"},
            entry={"regulation": "G", "clause": "C", "mode": "satisfies"},
            clause_meta=None,
        )
        assert "UC-UC-" not in sentence
        assert "UC-1.2.3" in sentence

    def test_unknown_mode_falls_back_to_contributes_prefix(self) -> None:
        sentence = mp.synthesise_control_objective(
            uc={"id": "1.1.1", "title": "T"},
            entry={"regulation": "G", "clause": "C", "mode": "unknown-mode"},
            clause_meta=None,
        )
        assert sentence.startswith("Contributes to ")

    def test_no_title_uses_uc_id_only(self) -> None:
        sentence = mp.synthesise_control_objective(
            uc={"id": "1.2.3"},
            entry={"regulation": "G", "clause": "C", "mode": "satisfies"},
            clause_meta=None,
        )
        # Trailer is "Splunk UC-1.2.3" (no colon/title).
        assert "Splunk UC-1.2.3" in sentence and ":" not in sentence.split("Splunk")[1]

    def test_pad_to_min_kicks_in_when_sentence_too_short(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Push _CO_MIN above what the template can produce; padding fires.
        monkeypatch.setattr(mp, "_CO_MIN", 800)
        sentence = mp.synthesise_control_objective(
            uc={"id": "1", "title": "T"},
            entry={"regulation": "G", "clause": "C", "mode": "satisfies"},
            clause_meta=None,
        )
        assert "SME review required" in sentence


# ---------------------------------------------------------------------------
# _summarise_sources
# ---------------------------------------------------------------------------


class TestSummariseSources:
    def test_list_input_is_joined_with_semicolons(self) -> None:
        out = mp._summarise_sources(["a", "b", "c"])
        assert out == "a; b; c"

    def test_blank_input_returns_default_label(self) -> None:
        assert mp._summarise_sources("") == "catalogue-defined data sources"
        assert mp._summarise_sources(None) == "catalogue-defined data sources"
        assert mp._summarise_sources([""]) == "catalogue-defined data sources"

    def test_idiomatic_placeholder_is_normalised(self) -> None:
        out = mp._summarise_sources("See subcategory preamble.")
        assert "see UC detailedImplementation" in out

    def test_short_clean_string_passes_through(self) -> None:
        out = mp._summarise_sources("`index=foo`")
        assert out == "index=foo"

    def test_sourcetype_anchor_used_when_long(self) -> None:
        long_string = "index=foo sourcetype=mybar:typename " + ("noise " * 50)
        out = mp._summarise_sources(long_string)
        assert "sourcetype mybar:typename" in out

    def test_index_anchor_used_when_sourcetype_absent(self) -> None:
        long_string = "index=audit_evidence " + ("filler " * 50)
        out = mp._summarise_sources(long_string)
        assert out.startswith("index audit_evidence")

    def test_topic_anchor_used_when_only_topic_present(self) -> None:
        long_string = "topic=sensors/cell01 " + ("filler " * 50)
        out = mp._summarise_sources(long_string)
        assert out.startswith("MQTT topic sensors/cell01")

    def test_no_anchor_falls_back_to_generic_phrase(self) -> None:
        long_string = "x" * 500  # no recognisable anchor
        out = mp._summarise_sources(long_string)
        assert out.startswith("catalogue-defined data sources")


# ---------------------------------------------------------------------------
# synthesise_evidence_artifact
# ---------------------------------------------------------------------------


class TestSynthesiseEvidenceArtifact:
    def test_full_template_renders(self) -> None:
        out = mp.synthesise_evidence_artifact(
            uc={"id": "1.1.1", "dataSources": "index=a"},
            entry={},
        )
        assert "Saved search 'UC-1.1.1' running on index=a" in out
        assert "audit_evidence index" in out

    def test_pad_to_min_kicks_in_when_too_short(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force the minimum above natural template length to hit padding.
        monkeypatch.setattr(mp, "_EA_MIN", 1000)
        out = mp.synthesise_evidence_artifact(
            uc={"id": "1.1.1", "dataSources": "index=a"},
            entry={},
        )
        assert "SME review required" in out


# ---------------------------------------------------------------------------
# derive_obligation_ref
# ---------------------------------------------------------------------------


class TestDeriveObligationRef:
    def test_returns_canonical_form_when_triple_resolves(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        ref = mp.derive_obligation_ref(
            {"regulation": "GDPR", "version": "2016/679", "clause": "Art.32"},
            idx,
        )
        assert ref == "gdpr@2016/679#Art.32"

    def test_returns_none_when_triple_incomplete(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        assert (
            mp.derive_obligation_ref(
                {"regulation": "GDPR", "version": "", "clause": "X"}, idx
            )
            is None
        )

    def test_returns_none_when_regulation_unresolvable(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        assert (
            mp.derive_obligation_ref(
                {"regulation": "UNKNOWN", "version": "1", "clause": "X"}, idx
            )
            is None
        )

    def test_returns_none_when_regex_validation_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force ``resolve_id`` to return a value that fails the regex
        # (uppercase letters disallowed under ``^[a-z0-9-]+``).
        class _FakeIndex:
            def resolve_id(self, name: str) -> str | None:
                return "BAD_ID"

        idx = _FakeIndex()
        assert (
            mp.derive_obligation_ref(
                {"regulation": "x", "version": "1", "clause": "C"},
                idx,  # type: ignore[arg-type]
            )
            is None
        )


# ---------------------------------------------------------------------------
# _is_blank + backfill_entry
# ---------------------------------------------------------------------------


class TestIsBlank:
    def test_blank_detection(self) -> None:
        assert mp._is_blank(None) is True
        assert mp._is_blank("") is True
        assert mp._is_blank("   ") is True
        assert mp._is_blank("x") is False
        assert mp._is_blank(0) is False  # numbers are not blank


class TestBackfillEntry:
    def test_populates_blank_story_fields_and_stamps_flag(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        uc = _make_sidecar()
        new, changed = mp.backfill_entry(uc, uc["compliance"][0], idx, False)
        assert changed is True
        assert new["controlObjective"]
        assert new["evidenceArtifact"]
        assert new["requires_sme_review"] is True
        assert new["obligationRef"] == "gdpr@2016/679#Art.32"

    def test_leaves_vetted_entries_alone_under_no_overwrite(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        uc = _make_sidecar()
        entry = uc["compliance"][0]
        entry["controlObjective"] = "Vetted CO."
        entry["evidenceArtifact"] = "Vetted EA."
        # Pre-populate obligationRef too, otherwise the unconditional
        # obligationRef-derivation block will still flip ``changed``.
        entry["obligationRef"] = "gdpr@2016/679#Art.32"
        entry["requires_sme_review"] = False
        _, changed = mp.backfill_entry(uc, entry, idx, False)
        assert changed is False

    def test_overwrite_auto_only_touches_machine_drafted(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        uc = _make_sidecar()
        entry = uc["compliance"][0]
        entry["controlObjective"] = "Auto-CO."
        entry["evidenceArtifact"] = "Auto-EA."
        entry["requires_sme_review"] = True
        new, changed = mp.backfill_entry(uc, entry, idx, True)
        assert changed is True
        assert new["controlObjective"] != "Auto-CO."

    def test_keeps_existing_obligation_ref(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        uc = _make_sidecar()
        entry = uc["compliance"][0]
        entry["obligationRef"] = "preset@v#c"
        new, _changed = mp.backfill_entry(uc, entry, idx, False)
        assert new["obligationRef"] == "preset@v#c"

    def test_no_change_when_synthesised_ea_matches_current(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force the EA synthesiser to return the same empty string as the
        # current value, exercising the ``if new_ea != ea_current`` False
        # branch (line 554->560).
        idx = mp.RegulationsIndex(_make_regulations_doc())
        uc = _make_sidecar()
        entry = uc["compliance"][0]
        entry["controlObjective"] = "Vetted CO"
        entry["evidenceArtifact"] = ""
        entry["obligationRef"] = "gdpr@2016/679#Art.32"  # short-circuit ref derive
        entry["requires_sme_review"] = False
        monkeypatch.setattr(mp, "synthesise_evidence_artifact", lambda *a, **k: "")
        _new, changed = mp.backfill_entry(uc, entry, idx, False)
        assert changed is False

    def test_obligation_ref_falls_through_when_derivation_returns_none(
        self,
    ) -> None:
        # Pin branch 562->566: obligationRef blank but derive returns None
        # because the regulation cannot be resolved.
        idx = mp.RegulationsIndex(_make_regulations_doc())
        entry = {
            "regulation": "Unknown reg",
            "version": "1",
            "clause": "X",
            "controlObjective": "Pre",
            "evidenceArtifact": "Pre",
            "requires_sme_review": False,
        }
        new, changed = mp.backfill_entry({"id": "1.1.1"}, entry, idx, False)
        # Nothing else changed; obligationRef stays absent.
        assert changed is False
        assert "obligationRef" not in new

    def test_no_change_when_synthesised_co_matches_current(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force synthesise_control_objective to return the *same* string
        # that already exists. The conditional ``if new_co != co_current``
        # then takes the False branch.
        idx = mp.RegulationsIndex(_make_regulations_doc())
        uc = _make_sidecar()
        entry = uc["compliance"][0]
        entry["controlObjective"] = ""  # blank → would normally backfill
        entry["evidenceArtifact"] = "Already EA"
        entry["obligationRef"] = "gdpr@2016/679#Art.32"  # avoid ref derivation
        entry["requires_sme_review"] = False
        monkeypatch.setattr(mp, "synthesise_control_objective", lambda *a, **k: "")
        new, changed = mp.backfill_entry(uc, entry, idx, False)
        # CO stayed blank (no diff); EA was vetted; no change.
        assert changed is False
        assert new.get("controlObjective", "") == ""


# ---------------------------------------------------------------------------
# iter_sidecars + _ensure_inside_repo
# ---------------------------------------------------------------------------


class TestIterSidecars:
    def test_returns_sorted_uc_paths(self, fake_repo: pathlib.Path) -> None:
        a = fake_repo / "content" / "cat-22-compliance" / "UC-22.2.1.json"
        b = fake_repo / "content" / "cat-22-compliance" / "UC-22.1.1.json"
        a.write_text("{}", encoding="utf-8")
        b.write_text("{}", encoding="utf-8")
        out = mp.iter_sidecars()
        assert out == [b, a]  # sorted alphabetically

    def test_returns_empty_list_when_content_missing(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(mp, "CONTENT_DIR", tmp_path / "nope")
        assert mp.iter_sidecars() == []


class TestEnsureInsideRepo:
    def test_accepts_path_inside_repo(self, fake_repo: pathlib.Path) -> None:
        # Smoke check — should not raise.
        mp._ensure_inside_repo(fake_repo / "content" / "x.json")

    def test_rejects_path_outside_repo(
        self, fake_repo: pathlib.Path, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        outside = tmp_path_factory.mktemp("other")
        with pytest.raises(SystemExit, match="refusing to write"):
            mp._ensure_inside_repo(outside / "x.json")


# ---------------------------------------------------------------------------
# process_sidecar
# ---------------------------------------------------------------------------


class TestProcessSidecar:
    def test_returns_false_when_compliance_is_not_a_list(
        self, fake_repo: pathlib.Path
    ) -> None:
        path = fake_repo / "content" / "cat-22-compliance" / "UC-22.1.1.json"
        mp._dump_json(path, {"compliance": {"not": "a list"}})
        idx = mp.RegulationsIndex(_make_regulations_doc())
        changed, stats = mp.process_sidecar(path, idx, False)
        assert changed is False
        assert stats == {"entries": 0, "touched": 0}

    def test_skips_non_dict_entries_in_compliance_list(
        self, fake_repo: pathlib.Path
    ) -> None:
        path = fake_repo / "content" / "cat-22-compliance" / "UC-22.1.1.json"
        # All-non-dict list: each entry hits the ``not isinstance(entry, dict)``
        # skip branch; no entry triggers a write, so the duplicate-detection
        # loop is bypassed (it only runs when ``touched`` > 0).
        sidecar = _make_sidecar(compliance=["s1", "s2", 42])
        mp._dump_json(path, sidecar)
        idx = mp.RegulationsIndex(_make_regulations_doc())
        changed, stats = mp.process_sidecar(path, idx, False)
        assert changed is False
        assert stats == {"entries": 3, "touched": 0}

    def test_returns_false_when_nothing_touched(
        self, fake_repo: pathlib.Path
    ) -> None:
        path = fake_repo / "content" / "cat-22-compliance" / "UC-22.1.1.json"
        sidecar = _make_sidecar(
            compliance=[
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "mode": "satisfies",
                    "controlObjective": "Vetted.",
                    "evidenceArtifact": "Vetted.",
                    "obligationRef": "gdpr@2016/679#Art.32",
                    "requires_sme_review": False,
                }
            ]
        )
        mp._dump_json(path, sidecar)
        idx = mp.RegulationsIndex(_make_regulations_doc())
        changed, stats = mp.process_sidecar(path, idx, False)
        assert changed is False
        assert stats["touched"] == 0

    def test_raises_on_duplicate_compliance_triple(
        self, fake_repo: pathlib.Path
    ) -> None:
        path = fake_repo / "content" / "cat-22-compliance" / "UC-22.1.1.json"
        entry = {
            "regulation": "GDPR",
            "version": "2016/679",
            "clause": "Art.32",
            "mode": "satisfies",
        }
        sidecar = _make_sidecar(compliance=[dict(entry), dict(entry)])
        mp._dump_json(path, sidecar)
        idx = mp.RegulationsIndex(_make_regulations_doc())
        with pytest.raises(SystemExit, match="duplicate compliance triple"):
            mp.process_sidecar(path, idx, False)


# ---------------------------------------------------------------------------
# build_obligation_manifest
# ---------------------------------------------------------------------------


class TestBuildObligationManifest:
    def test_lists_missing_clauses_under_tier_headings(self) -> None:
        idx = mp.RegulationsIndex(_make_regulations_doc())
        out = mp.build_obligation_manifest(idx)
        # GDPR Art.33 lacks obligationText → row present.
        assert "Art.33" in out
        # GDPR Art.32 has obligationText → not in the missing rows table.
        assert "| Art.32 |" not in out
        # Summary block.
        assert "## Summary" in out
        # Tier headings.
        assert "## Tier 1" in out
        # Tier 3 has empty framework + no clauses; ensure no tier-3 row table.
        assert "## Tier 3" not in out

    def test_handles_clause_with_non_numeric_priority(self) -> None:
        # When priorityWeight is None or unset, the ``pw_str`` formatter
        # writes the em-dash fallback. Exercise that branch.
        doc = {
            "frameworks": [
                {
                    "id": "fw",
                    "shortName": "FW",
                    "tier": 1,
                    "versions": [
                        {
                            "version": "1",
                            "commonClauses": [{"clause": "X", "topic": "T"}],
                        }
                    ],
                }
            ]
        }
        idx = mp.RegulationsIndex(doc)
        out = mp.build_obligation_manifest(idx)
        assert "—" in out  # em-dash priority fallback

    def test_tier_with_only_completed_clauses_still_renders_section(self) -> None:
        # Pin branch 704->661: tier_rows is empty (no missing clauses) but
        # tier_done > 0 → the ``if not tier_rows and tier_done == 0`` skip
        # branch is False so we emit the tier section header WITHOUT a
        # table.
        doc = {
            "frameworks": [
                {
                    "id": "complete-fw",
                    "shortName": "DONE",
                    "tier": 2,
                    "versions": [
                        {
                            "version": "1",
                            "commonClauses": [
                                {"clause": "X", "obligationText": "Has text"}
                            ],
                        }
                    ],
                }
            ]
        }
        idx = mp.RegulationsIndex(doc)
        out = mp.build_obligation_manifest(idx)
        assert "## Tier 2" in out
        # No table emitted because there are no missing rows for this tier.
        # The body line is the "done · missing" status string.
        assert "still need authoritative obligation text" in out


# ---------------------------------------------------------------------------
# run + _write_sidecar
# ---------------------------------------------------------------------------


class TestRun:
    def test_returns_2_when_regulations_missing(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # No regulations.json written.
        assert mp.run(check_only=False, dry_run=False, overwrite_auto=False) == 2
        assert "missing" in capsys.readouterr().err

    def test_stats_only_summarises_coverage(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Write regulations + two sidecars (one vetted, one bare).
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        mp._dump_json(
            cat / "UC-22.1.1.json",
            _make_sidecar(
                compliance=[
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.32",
                        "controlObjective": "Vetted CO",
                        "evidenceArtifact": "Vetted EA",
                        "requires_sme_review": False,
                    },
                ]
            ),
        )
        mp._dump_json(
            cat / "UC-22.1.2.json",
            _make_sidecar(
                compliance=[
                    {
                        "regulation": "GDPR",
                        "version": "2016/679",
                        "clause": "Art.33",
                        "requires_sme_review": True,
                    }
                ]
            ),
        )
        rc = mp.run(
            check_only=False,
            dry_run=False,
            overwrite_auto=False,
            stats_only=True,
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "compliance entries scanned" in out

    def test_stats_only_skips_unreadable_sidecars_gracefully(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        (cat / "UC-22.1.1.json").write_text("not valid json", encoding="utf-8")
        # The bare ``except Exception: continue`` swallows the parse error.
        assert (
            mp.run(
                check_only=False,
                dry_run=False,
                overwrite_auto=False,
                stats_only=True,
            )
            == 0
        )

    def test_stats_only_skips_non_dict_compliance_entries(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        mp._dump_json(
            cat / "UC-22.1.1.json",
            _make_sidecar(compliance=["non-dict-row"]),
        )
        assert (
            mp.run(
                check_only=False,
                dry_run=False,
                overwrite_auto=False,
                stats_only=True,
            )
            == 0
        )

    def test_only_filter_restricts_sidecar_set(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        mp._dump_json(cat / "UC-22.1.1.json", _make_sidecar(uc_id="22.1.1"))
        mp._dump_json(cat / "UC-22.1.2.json", _make_sidecar(uc_id="22.1.2"))
        # Only UC-22.1.1 is in scope; UC-22.1.2 is left untouched.
        rc = mp.run(
            check_only=False,
            dry_run=False,
            overwrite_auto=False,
            only=["UC-22.1.1, 22.1.1 ", "  , "],  # exercise comma-/space-split + empty
        )
        assert rc == 0
        body_2 = json.loads((cat / "UC-22.1.2.json").read_text(encoding="utf-8"))
        # UC-22.1.2 untouched ⇒ no controlObjective.
        assert "controlObjective" not in body_2["compliance"][0]

    def test_full_write_run_emits_manifest_and_modifies_sidecar(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        mp._dump_json(cat / "UC-22.1.1.json", _make_sidecar())
        rc = mp.run(check_only=False, dry_run=False, overwrite_auto=False)
        assert rc == 0
        body = json.loads((cat / "UC-22.1.1.json").read_text(encoding="utf-8"))
        assert body["compliance"][0]["controlObjective"]
        # Manifest was written.
        assert mp.PHASE4_MANIFEST.exists()

    def test_check_mode_returns_1_on_drift(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        mp._dump_json(cat / "UC-22.1.1.json", _make_sidecar())
        rc = mp.run(check_only=True, dry_run=False, overwrite_auto=False)
        assert rc == 1
        assert "Phase 4 backfill drift" in capsys.readouterr().err

    def test_dry_run_does_not_write_sidecar(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        path = cat / "UC-22.1.1.json"
        mp._dump_json(path, _make_sidecar())
        original_text = path.read_text(encoding="utf-8")
        rc = mp.run(check_only=False, dry_run=True, overwrite_auto=False)
        assert rc == 0
        assert path.read_text(encoding="utf-8") == original_text

    def test_only_filter_ignores_entirely_empty_uid_tokens(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # Pin branch 753->749: ``piece = "UC-"`` → after strip becomes "",
        # so ``if uid:`` is False and the inner loop continues.
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        mp._dump_json(cat / "UC-22.1.1.json", _make_sidecar())
        rc = mp.run(
            check_only=False,
            dry_run=False,
            overwrite_auto=False,
            only=["UC-"],  # strips to empty → only_set stays empty
        )
        # Empty only_set filters every sidecar out → no work, no error.
        assert rc == 0

    def test_skips_sidecars_that_need_no_changes(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # Pin branch 800 (``continue`` when process_sidecar reports no
        # change). The sidecar is pre-vetted so backfill leaves it alone.
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        vetted = _make_sidecar(
            compliance=[
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "controlObjective": "Vetted",
                    "evidenceArtifact": "Vetted",
                    "obligationRef": "gdpr@2016/679#Art.32",
                    "requires_sme_review": False,
                }
            ]
        )
        mp._dump_json(cat / "UC-22.1.1.json", vetted)
        rc = mp.run(check_only=False, dry_run=False, overwrite_auto=False)
        assert rc == 0

    def test_rewrites_manifest_when_existing_content_drifted(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # Pin branch 817 (``manifest_current != manifest_text → True``).
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        mp._dump_json(cat / "UC-22.1.1.json", _make_sidecar())
        mp.PHASE4_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        mp.PHASE4_MANIFEST.write_text("STALE manifest body\n", encoding="utf-8")
        rc = mp.run(check_only=False, dry_run=False, overwrite_auto=False)
        assert rc == 0
        # Manifest was rewritten to the freshly-built content.
        assert "STALE manifest body" not in mp.PHASE4_MANIFEST.read_text(
            encoding="utf-8"
        )

    def test_manifest_not_rewritten_when_content_matches(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # Pre-write the manifest so the "manifest_current == manifest_text"
        # branch is exercised.
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        sidecar_path = cat / "UC-22.1.1.json"
        mp._dump_json(sidecar_path, _make_sidecar())
        idx = mp.RegulationsIndex(_make_regulations_doc())
        manifest = mp.build_obligation_manifest(idx)
        mp.PHASE4_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        mp.PHASE4_MANIFEST.write_text(manifest, encoding="utf-8")
        rc = mp.run(check_only=False, dry_run=False, overwrite_auto=False)
        assert rc == 0

    def test_returns_2_when_process_sidecar_raises(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mp._dump_json(mp.REGULATIONS_PATH, _make_regulations_doc())
        cat = fake_repo / "content" / "cat-22-compliance"
        path = cat / "UC-22.1.1.json"
        mp._dump_json(path, _make_sidecar())

        def boom(*_a: Any, **_kw: Any) -> Any:
            raise RuntimeError("boom")

        monkeypatch.setattr(mp, "process_sidecar", boom)
        assert mp.run(check_only=False, dry_run=False, overwrite_auto=False) == 2
        assert "boom" in capsys.readouterr().err


class TestWriteSidecar:
    def test_passes_through_when_compliance_not_a_list(
        self, fake_repo: pathlib.Path
    ) -> None:
        path = fake_repo / "content" / "cat-22-compliance" / "UC-22.1.1.json"
        sidecar = {"id": "1", "compliance": {"shape": "wrong"}}
        mp._dump_json(path, sidecar)
        idx = mp.RegulationsIndex(_make_regulations_doc())
        # Should return early without writing differently.
        mp._write_sidecar(path, idx, False)
        reread = json.loads(path.read_text(encoding="utf-8"))
        assert reread["compliance"] == {"shape": "wrong"}

    def test_preserves_non_dict_entries(self, fake_repo: pathlib.Path) -> None:
        path = fake_repo / "content" / "cat-22-compliance" / "UC-22.1.1.json"
        sidecar = _make_sidecar(
            compliance=[
                "non-dict-row",
                {
                    "regulation": "GDPR",
                    "version": "2016/679",
                    "clause": "Art.32",
                    "mode": "satisfies",
                },
            ]
        )
        mp._dump_json(path, sidecar)
        idx = mp.RegulationsIndex(_make_regulations_doc())
        mp._write_sidecar(path, idx, False)
        reread = json.loads(path.read_text(encoding="utf-8"))
        # Non-dict row is preserved verbatim.
        assert reread["compliance"][0] == "non-dict-row"
        # Dict row is backfilled.
        assert reread["compliance"][1]["controlObjective"]


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_dispatches_to_run_with_parsed_args(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, Any] = {}

        def fake_run(**kwargs: Any) -> int:
            captured.update(kwargs)
            return 0

        monkeypatch.setattr(mp, "run", fake_run)
        assert (
            mp.main(
                [
                    "--check",
                    "--dry-run",
                    "--overwrite-auto",
                    "--only",
                    "UC-1.1.1",
                    "--stats-only",
                ]
            )
            == 0
        )
        assert captured == {
            "check_only": True,
            "dry_run": True,
            "overwrite_auto": True,
            "only": ["UC-1.1.1"],
            "stats_only": True,
        }

    def test_defaults_when_no_args_passed(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(mp, "run", lambda **kwargs: 0)
        assert mp.main([]) == 0
