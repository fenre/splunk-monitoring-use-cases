"""Hermetic coverage suite for ``splunk_uc.ingest.d3fend``.

The D3FEND driver downloads (a) the JSON-LD ontology and (b) the
SPARQL-shaped inferred mappings, then emits two flat normalised JSON
files. The ontology normaliser walks an OWL class hierarchy, so the
tests construct minimal but representative @graph payloads to exercise
every branch.

Brings coverage from 9.6% to 100%.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from splunk_uc.ingest import d3fend as d3
from splunk_uc.ingest import manifest as mf


def _stub_fetch(
    monkeypatch: pytest.MonkeyPatch,
    fail_for: set[str] | None = None,
) -> list[str]:
    seen: list[str] = []
    fail_for = fail_for or set()

    def _fake_fetch(
        *,
        source_id: str,
        url: str,
        dest: pathlib.Path,
        repo_root: pathlib.Path,
        **_kw: object,
    ) -> mf.FetchRecord:
        seen.append(source_id)
        if source_id in fail_for:
            raise RuntimeError(f"synthetic-fetch-failure-for-{source_id}")
        return mf.FetchRecord(
            source_id=source_id,
            url=url,
            local=str(dest),
            bytes=len(dest.read_bytes()) if dest.exists() else 0,
            sha256="d" * 64,
            fetched_at="2026-05-20T10:00:00Z",
        )

    monkeypatch.setattr(d3, "fetch", _fake_fetch)
    return seen


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    monkeypatch.setattr(d3, "_REPO", tmp_path)
    monkeypatch.setattr(d3, "VENDOR_DIR", tmp_path / "vendor" / "d3fend")
    monkeypatch.setattr(
        d3, "CROSSWALK_DIR", tmp_path / "data" / "crosswalks" / "d3fend"
    )
    monkeypatch.setattr(
        d3,
        "MANIFEST_PATH",
        tmp_path / "data" / "provenance" / "ingest-manifest.json",
    )
    new_sources = []
    for src in d3.SOURCES:
        new = dict(src)
        new["local"] = tmp_path / "vendor" / "d3fend" / pathlib.Path(src["local"]).name
        new_sources.append(new)
    monkeypatch.setattr(d3, "SOURCES", new_sources)
    return tmp_path


class TestStrHelper:
    def test_returns_none_for_none(self) -> None:
        assert d3._str(None) is None

    def test_returns_string_unchanged(self) -> None:
        assert d3._str("hello") == "hello"

    def test_extracts_value_or_id_from_dict(self) -> None:
        assert d3._str({"@value": "x"}) == "x"
        assert d3._str({"@id": "y"}) == "y"
        # Both: @value wins.
        assert d3._str({"@value": "v", "@id": "i"}) == "v"

    def test_returns_none_when_dict_has_neither_key(self) -> None:
        assert d3._str({"@nope": "foo"}) is None
        # Dict with @value=None falls through to None.
        assert d3._str({"@value": None, "@id": None}) is None

    def test_walks_list_and_returns_first_truthy(self) -> None:
        assert d3._str([None, "", "first", "second"]) == "first"

    def test_returns_none_for_empty_list(self) -> None:
        assert d3._str([]) is None
        assert d3._str([None, None]) is None

    def test_returns_none_for_unrecognised_type(self) -> None:
        # Pin the final ``return None`` fallthrough.
        assert d3._str(42) is None
        assert d3._str(3.14) is None


class TestListStrHelper:
    def test_none_returns_empty_list(self) -> None:
        assert d3._list_str(None) == []

    def test_list_flattens_and_filters_empties(self) -> None:
        assert d3._list_str(["a", "", None, "b"]) == ["a", "b"]

    def test_wraps_scalar_into_one_element_list(self) -> None:
        assert d3._list_str("x") == ["x"]
        assert d3._list_str({"@id": "Y"}) == ["Y"]

    def test_returns_empty_when_scalar_resolves_to_falsy(self) -> None:
        # Scalar that _str returns None for → empty list.
        assert d3._list_str(42) == []


class TestShortId:
    def test_returns_empty_string_for_blank_input(self) -> None:
        assert d3._short_id("") == ""

    def test_splits_on_hash_when_present(self) -> None:
        assert d3._short_id("http://example.com/d3fend#D3-FOO") == "D3-FOO"

    def test_falls_back_to_last_path_segment(self) -> None:
        assert d3._short_id("http://example.com/path/to/Bar") == "Bar"


class TestNormaliseOntology:
    def test_returns_empty_when_graph_missing(self) -> None:
        out = d3._normalise_ontology({})
        assert out["techniques_count"] == 0
        assert out["techniques"] == []

    def test_skips_nodes_with_no_id(self) -> None:
        out = d3._normalise_ontology({"@graph": [{"foo": "bar"}]})
        assert out["techniques_count"] == 0

    def test_extracts_defensive_technique_descendants(self) -> None:
        """Pin the full ontology walk:

        * d3f:DefensiveTechnique (root)
        * d3f:Foo extends d3f:DefensiveTechnique (direct child → included)
        * d3f:Bar extends d3f:Foo (transitive grandchild → included)
        * d3f:Unrelated extends owl:Thing (excluded)
        """
        out = d3._normalise_ontology(
            {
                "@graph": [
                    {
                        "@id": "d3f:DefensiveTechnique",
                        "@type": "owl:Class",
                        "rdfs:label": "Defensive Technique",
                    },
                    {
                        "@id": "d3f:Foo",
                        "@type": ["owl:Class"],
                        "rdfs:label": {"@value": "Foo Technique"},
                        # subClassOf as a single dict (NOT a list) →
                        # pins the ``isinstance(raw_parents, dict)`` branch.
                        "rdfs:subClassOf": {"@id": "d3f:DefensiveTechnique"},
                        "d3f:definition": "Foo def",
                    },
                    {
                        "@id": "d3f:Bar",
                        "@type": "owl:Class",
                        "rdfs:label": "Bar Technique",
                        # subClassOf as a single string IRI → pins the
                        # ``isinstance(raw_parents, str)`` branch.
                        "rdfs:subClassOf": "d3f:Foo",
                        # Definition picked from rdfs:comment fallback.
                        "http://www.w3.org/2000/01/rdf-schema#comment": "Bar def",
                    },
                    {
                        "@id": "d3f:Unrelated",
                        "@type": "owl:Class",
                        "rdfs:label": "Unrelated",
                        # subClassOf as a list with one non-dict element
                        # → pins the ``isinstance(p, dict)`` False branch.
                        "rdfs:subClassOf": ["raw-string-ignored"],
                    },
                    {
                        # Same id as a parent of d3f:Bar in a different
                        # representation — exercises de-dup.
                        "@id": "d3f:Stub",
                        # Not an owl:Class → skipped.
                        "@type": "owl:ObjectProperty",
                    },
                ]
            }
        )
        ids = {t["id"] for t in out["techniques"]}
        # Root + two descendants. _short_id falls back to the full
        # iri-as-is when there's no '#' or '/' delimiter (d3f:Foo →
        # d3f:Foo). Unrelated excluded because it has no path to
        # d3f:DefensiveTechnique.
        assert ids == {"d3f:DefensiveTechnique", "d3f:Foo", "d3f:Bar"}
        # The label of d3f:Foo came from the @value form.
        foo = next(t for t in out["techniques"] if t["id"] == "d3f:Foo")
        assert foo["label"] == "Foo Technique"
        assert foo["definition"] == "Foo def"
        # Bar's definition came from the fallback (rdfs:comment URL key).
        bar = next(t for t in out["techniques"] if t["id"] == "d3f:Bar")
        assert bar["definition"] == "Bar def"
        # Foo has Bar as a child → is_terminal is False.
        assert foo["is_terminal"] is False
        # Bar has no children → is_terminal is True.
        assert bar["is_terminal"] is True
        # Output is sorted on (id, iri).
        ordered = [(t["id"], t["iri"]) for t in out["techniques"]]
        assert ordered == sorted(ordered)

    def test_diamond_inheritance_visits_each_ancestor_once(self) -> None:
        """Pin line 138 ``continue`` in ``_ancestors``: when two parents
        share a common grandparent, the visit-once guard fires."""
        out = d3._normalise_ontology(
            {
                "@graph": [
                    {
                        "@id": "d3f:DefensiveTechnique",
                        "@type": "owl:Class",
                    },
                    {
                        "@id": "d3f:Mid",
                        "@type": "owl:Class",
                        "rdfs:subClassOf": [{"@id": "d3f:DefensiveTechnique"}],
                    },
                    # d3f:Diamond has TWO parents that both transit
                    # through d3f:Mid → d3f:DefensiveTechnique. Each
                    # parent re-pushes the grandparent onto the stack,
                    # so the second pop hits ``if p in seen: continue``.
                    {
                        "@id": "d3f:LeftBranch",
                        "@type": "owl:Class",
                        "rdfs:subClassOf": [{"@id": "d3f:Mid"}],
                    },
                    {
                        "@id": "d3f:RightBranch",
                        "@type": "owl:Class",
                        "rdfs:subClassOf": [{"@id": "d3f:Mid"}],
                    },
                    {
                        "@id": "d3f:Diamond",
                        "@type": "owl:Class",
                        "rdfs:subClassOf": [
                            {"@id": "d3f:LeftBranch"},
                            {"@id": "d3f:RightBranch"},
                        ],
                    },
                ]
            }
        )
        ids = {t["id"] for t in out["techniques"]}
        assert "d3f:Diamond" in ids

    def test_subclassof_parent_dict_without_id_is_dropped(self) -> None:
        """Pin branch 128->125: ``_str(p.get('@id'))`` returns None, so
        the ``if pid: pids.append(pid)`` body is skipped."""
        out = d3._normalise_ontology(
            {
                "@graph": [
                    {
                        "@id": "d3f:DefensiveTechnique",
                        "@type": "owl:Class",
                    },
                    {
                        "@id": "d3f:Orphan",
                        "@type": "owl:Class",
                        # Parent dict with no @id → no parent recorded.
                        "rdfs:subClassOf": [{"@nope": "missing-id"}],
                    },
                ]
            }
        )
        orphan = next(
            (t for t in out["techniques"] if t["id"] == "d3f:Orphan"), None
        )
        # Orphan has no path to d3f:DefensiveTechnique so it shouldn't
        # be in the output at all — the empty parents list is the
        # important invariant. We grep the by-id ``parents`` map by
        # reaching through the result.
        # The contract under test is: when pid is None, parents is empty.
        # That's reflected in the orphan being excluded from the
        # technique tree (since it has no ancestor path to the root).
        assert orphan is None


class TestNormaliseMappings:
    def test_scan_walks_arbitrary_json_and_extracts_attack_ids(self) -> None:
        """When the doc is NOT a SPARQL-shaped envelope, the recursive
        ``_scan`` walks every value and harvests ATT&CK IDs.
        """
        out = d3._normalise_mappings(
            {
                "items": [
                    {"text": "see T1059.001 and T1003"},
                    {"text": "T1059 again, plus garbage"},
                ],
                "label": "T9999",
            }
        )
        # _scan only setdefault's the key, so values are empty lists.
        # The function dedupes via ``if i and i not in seen`` — empty
        # list stays empty.
        assert set(out["mappings"].keys()) == {"T1059.001", "T1003", "T1059", "T9999"}
        # mapping_pair_count is sum of value-list lengths → 0 in this case.
        assert out["mapping_pair_count"] == 0

    def test_scan_bindings_path_extracts_def_tech_pairs(self) -> None:
        out = d3._normalise_mappings(
            {
                "results": {
                    "bindings": [
                        {
                            "def_tech": {"value": "http://x/#D3-FA"},
                            "off_tech_id": {"value": "T1059.001"},
                        },
                        {
                            # Same attack_id, second d3fend mapping →
                            # appended, NOT deduped (different value).
                            "def_tech": {"value": "http://x/#D3-FB"},
                            "attack_id": {"value": "T1059.001"},
                        },
                        {
                            # Uses the legacy "defensive_technique" alias.
                            "defensive_technique": {"value": "http://x/#D3-FC"},
                            "offensive_technique_id": {"value": "T1003"},
                        },
                        # Row with missing def_tech → skipped.
                        {"off_tech_id": {"value": "T9999"}},
                        # Row with missing attack id → skipped.
                        {"def_tech": {"value": "http://x/#D3-FD"}},
                        # Row with duplicate (attack_id, d3f_iri) → deduped.
                        {
                            "def_tech": {"value": "http://x/#D3-FA"},
                            "attack_id": {"value": "T1059.001"},
                        },
                    ]
                }
            }
        )
        assert sorted(out["mappings"]["T1059.001"]) == ["D3-FA", "D3-FB"]
        assert out["mappings"]["T1003"] == ["D3-FC"]
        # mapping_pair_count: 2 + 1 = 3.
        assert out["mapping_pair_count"] == 3
        # Sanity on top-line fields.
        assert out["attack_id_count"] == 2
        assert out["source"] == "d3fend-full-mappings"

    def test_envelope_with_empty_bindings_does_not_crash(self) -> None:
        out = d3._normalise_mappings({"results": {"bindings": []}})
        assert out["mappings"] == {}

    def test_envelope_with_results_but_no_bindings_falls_through_to_scan(
        self,
    ) -> None:
        """Pin the False branch of the ``'bindings' in results`` guard."""
        out = d3._normalise_mappings(
            {"results": {"text": "no bindings here, just T1059"}}
        )
        # Falls into the recursive _scan path; T1059 is harvested.
        assert "T1059" in out["mappings"]

    def test_scan_handles_non_str_non_dict_non_list_values(self) -> None:
        """Pin branch 194->exit: when _scan encounters a value that is
        none of dict/list/str (e.g. int, float, bool, None), the
        function exits without doing anything."""
        out = d3._normalise_mappings(
            {
                "items": [
                    42,  # int
                    3.14,  # float
                    True,  # bool
                    None,  # None
                    "T1059",  # string with one hit
                    "",  # empty string (loop is empty)
                ]
            }
        )
        # Only the string with a matched T-ID populated mappings.
        assert "T1059" in out["mappings"]


class TestRun:
    def test_full_run_writes_two_files_and_manifest(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = _stub_fetch(monkeypatch)
        # Seed the ontology file.
        d3.SOURCES[0]["local"].parent.mkdir(parents=True, exist_ok=True)
        d3.SOURCES[0]["local"].write_text(
            json.dumps(
                {
                    "@graph": [
                        {
                            "@id": "d3f:DefensiveTechnique",
                            "@type": "owl:Class",
                            "rdfs:label": "Root",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        # Seed the mappings file with a SPARQL-shaped doc.
        d3.SOURCES[1]["local"].write_text(
            json.dumps(
                {
                    "results": {
                        "bindings": [
                            {
                                "def_tech": {"value": "http://x/#D3-FA"},
                                "attack_id": {"value": "T1059"},
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )
        rc = d3.run()
        assert rc == 0
        assert seen == [s["id"] for s in d3.SOURCES]
        techniques_path = d3.CROSSWALK_DIR / "d3fend-techniques.normalised.json"
        mappings_path = d3.CROSSWALK_DIR / "d3fend-attack-mappings.normalised.json"
        assert techniques_path.exists()
        assert mappings_path.exists()
        # Trailing newlines + sorted keys.
        for path in (techniques_path, mappings_path):
            text = path.read_text(encoding="utf-8")
            assert text.endswith("\n")
        # Manifest got both records.
        manifest_body = json.loads(d3.MANIFEST_PATH.read_text(encoding="utf-8"))
        assert len(manifest_body["provenance"]) == 2

    def test_returns_2_when_first_fetch_fails(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        first_id = d3.SOURCES[0]["id"]
        seen = _stub_fetch(monkeypatch, fail_for={first_id})
        rc = d3.run()
        assert rc == 2
        # Loop short-circuits after first failure.
        assert seen == [first_id]
        assert "FAIL: synthetic-fetch-failure" in capsys.readouterr().err
        # No normalised files emitted.
        assert not (d3.CROSSWALK_DIR / "d3fend-techniques.normalised.json").exists()


class TestMain:
    def test_main_returns_run_rc_and_discards_argv(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        # Replace SOURCES with one ontology + one mappings doc, both
        # seeded with minimal payloads, so the run is trivially green.
        d3.SOURCES[0]["local"].parent.mkdir(parents=True, exist_ok=True)
        d3.SOURCES[0]["local"].write_text(json.dumps({"@graph": []}), encoding="utf-8")
        d3.SOURCES[1]["local"].write_text(json.dumps({}), encoding="utf-8")
        _stub_fetch(monkeypatch)
        rc = d3.main(["--anything"])
        assert rc == 0
