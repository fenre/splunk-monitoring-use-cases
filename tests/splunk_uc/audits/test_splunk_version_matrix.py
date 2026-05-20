"""Unit tests for ``audit-splunk-version-matrix``.

The audit owns three contracts:

1. Loading the canonical ``data/splunk-version-vocabulary.json`` file
   surfaces a clean dict keyed by token id.
2. Walking ``content/cat-*/UC-*.json`` produces ``SidecarVersionEntry``
   records *only* for sidecars that declare a non-empty
   ``splunkVersions`` array; malformed shapes land in
   ``parse_errors`` rather than crashing.
3. ``build_matrix`` rolls entries up correctly across the
   token/track/kind axes and flags unknown tokens with a
   ``did_you_mean`` suggestion via :func:`difflib.get_close_matches`.

We hand-craft a temp ``content/`` tree per test so the unit tests stay
hermetic. A separate corpus-level integration test (lives next to the
:class:`UseCase` corpus test) asserts the live vocabulary on disk has
no unknown tokens \u2014 that's the CI gate; this file pins the audit's
*shape*.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits.splunk_version_matrix import (
    Matrix,
    SidecarVersionEntry,
    UnknownTokenFinding,
    VocabToken,
    _matrix_to_json,
    _render_markdown,
    build_matrix,
    collect_entries,
    load_vocabulary,
    main,
)

# ----------------------------------------------------------------------
# Vocabulary loader
# ----------------------------------------------------------------------


def test_load_vocabulary_reads_the_canonical_file() -> None:
    """The committed vocabulary parses cleanly into a dict of VocabTokens."""
    vocab = load_vocabulary()
    assert "Cloud" in vocab


def test_vocabulary_matches_uc_schema_enum() -> None:
    """``schemas/uc.schema.json`` ``splunkVersions.items.enum`` must list
    *exactly* the same tokens as ``data/splunk-version-vocabulary.json``.

    Pinning this parity is the whole point of the v1.7.1 enum
    tightening: a stale schema can never silently accept a typo, and
    a stale vocabulary can never silently reject a token the schema
    permits. Drift in either direction is a CI failure here, *before*
    the per-PR audit catches it at sidecar-validation time.
    """
    vocab = load_vocabulary()
    vocab_tokens = sorted(vocab.keys())

    schema_path = (
        Path(__file__).resolve().parents[3] / "schemas" / "uc.schema.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    items = schema["properties"]["splunkVersions"]["items"]
    schema_enum = sorted(items["enum"])

    assert schema_enum == vocab_tokens, (
        f"Schema enum and vocabulary tokens drifted: "
        f"schema={schema_enum!r}, vocab={vocab_tokens!r}. "
        "Update both surfaces together (see "
        "schemas/changelogs/uc.md entry 1.7.1)."
    )
    assert "9.2+" in vocab
    cloud = vocab["Cloud"]
    assert isinstance(cloud, VocabToken)
    assert cloud.kind == "cloud"
    assert cloud.track == "cloud"


def test_load_vocabulary_missing_file_raises(tmp_path: Path) -> None:
    """A missing vocabulary file raises FileNotFoundError, not crashing."""
    with pytest.raises(FileNotFoundError):
        load_vocabulary(tmp_path / "absent.json")


def test_load_vocabulary_rejects_malformed_root(tmp_path: Path) -> None:
    """Top-level non-object input must be rejected."""
    p = tmp_path / "vocab.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_vocabulary(p)


def test_load_vocabulary_rejects_duplicate_ids(tmp_path: Path) -> None:
    """Two entries with the same id is a data integrity error."""
    p = tmp_path / "vocab.json"
    p.write_text(
        json.dumps(
            {
                "tokens": [
                    {
                        "id": "Cloud",
                        "kind": "cloud",
                        "track": "cloud",
                        "support_phase": "ga",
                        "description": "primary",
                    },
                    {
                        "id": "Cloud",
                        "kind": "cloud",
                        "track": "cloud",
                        "support_phase": "ga",
                        "description": "duplicate",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate token id 'Cloud'"):
        load_vocabulary(p)


def test_load_vocabulary_rejects_missing_field(tmp_path: Path) -> None:
    """Each token must carry id/kind/track/support_phase/description."""
    p = tmp_path / "vocab.json"
    p.write_text(
        json.dumps({"tokens": [{"id": "Cloud", "kind": "cloud"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="missing required field"):
        load_vocabulary(p)


# ----------------------------------------------------------------------
# Sidecar walk
# ----------------------------------------------------------------------


def _write_sidecar(
    root: Path, cat_dir: str, uc_id: str, **extras: object
) -> Path:
    """Write a minimal valid sidecar under *root* and return its path."""
    cat = root / cat_dir
    cat.mkdir(parents=True, exist_ok=True)
    body: dict[str, object] = {
        "id": uc_id,
        "title": f"Stub UC {uc_id}",
    }
    body.update(extras)
    p = cat / f"UC-{uc_id}.json"
    p.write_text(json.dumps(body), encoding="utf-8")
    return p


def test_collect_entries_skips_sidecars_without_splunk_versions(tmp_path: Path) -> None:
    """A sidecar with no ``splunkVersions`` does not appear in entries."""
    content = tmp_path / "content"
    _write_sidecar(content, "cat-01-server-compute", "1.1.1")
    _write_sidecar(
        content,
        "cat-01-server-compute",
        "1.1.2",
        splunkVersions=["Cloud", "9.2+"],
    )
    entries, errors = collect_entries(content)
    assert errors == []
    assert len(entries) == 1
    assert entries[0].uc_id == "1.1.2"
    assert entries[0].versions == ("Cloud", "9.2+")
    assert entries[0].category == 1


def test_collect_entries_skips_explicitly_empty_arrays(tmp_path: Path) -> None:
    """``splunkVersions: []`` is semantically equivalent to absent."""
    content = tmp_path / "content"
    _write_sidecar(content, "cat-02-virtualization", "2.1.1", splunkVersions=[])
    entries, errors = collect_entries(content)
    assert entries == []
    assert errors == []


def test_collect_entries_flags_non_list_splunk_versions(tmp_path: Path) -> None:
    """A scalar ``splunkVersions`` lands in parse_errors, not entries."""
    content = tmp_path / "content"
    _write_sidecar(
        content, "cat-03-storage", "3.1.1", splunkVersions="Cloud"
    )
    entries, errors = collect_entries(content)
    assert entries == []
    assert len(errors) == 1
    assert "must be an array" in errors[0]


def test_collect_entries_flags_non_string_elements(tmp_path: Path) -> None:
    """Non-string entries are dropped + reported, but valid ones pass through."""
    content = tmp_path / "content"
    _write_sidecar(
        content,
        "cat-04-network",
        "4.1.1",
        splunkVersions=["Cloud", 42, "9.2+"],
    )
    entries, errors = collect_entries(content)
    assert len(entries) == 1
    assert entries[0].versions == ("Cloud", "9.2+")  # the int is filtered out
    assert any("is not a string" in e for e in errors)


def test_collect_entries_flags_bad_uc_id(tmp_path: Path) -> None:
    """A sidecar with a malformed ``id`` becomes a parse error."""
    content = tmp_path / "content"
    cat = content / "cat-05-security"
    cat.mkdir(parents=True)
    (cat / "UC-bogus.json").write_text(
        json.dumps({"id": "not-an-id", "title": "x"}),
        encoding="utf-8",
    )
    entries, errors = collect_entries(content)
    assert entries == []
    assert any("invalid UC id" in e for e in errors)


def test_collect_entries_flags_top_level_array(tmp_path: Path) -> None:
    """A sidecar whose top level is an array is a parse error."""
    content = tmp_path / "content"
    cat = content / "cat-06-storage-backup"
    cat.mkdir(parents=True)
    (cat / "UC-6.1.1.json").write_text("[]", encoding="utf-8")
    entries, errors = collect_entries(content)
    assert entries == []
    assert any("top-level is not an object" in e for e in errors)


def test_collect_entries_flags_malformed_json(tmp_path: Path) -> None:
    """Broken JSON is a parse error, not a crash."""
    content = tmp_path / "content"
    cat = content / "cat-07-database-data-platforms"
    cat.mkdir(parents=True)
    (cat / "UC-7.1.1.json").write_text("{ not json", encoding="utf-8")
    entries, errors = collect_entries(content)
    assert entries == []
    assert any("malformed JSON" in e for e in errors)


# ----------------------------------------------------------------------
# Matrix construction
# ----------------------------------------------------------------------


def _toy_vocab() -> dict[str, VocabToken]:
    return {
        "Cloud": VocabToken(
            id="Cloud",
            kind="cloud",
            track="cloud",
            support_phase="supported",
            description="",
        ),
        "9.2+": VocabToken(
            id="9.2+",
            kind="on-prem",
            track="9.x",
            support_phase="supported",
            description="",
        ),
    }


def test_build_matrix_counts_known_tokens_and_axes() -> None:
    """Known tokens roll up by token / track / kind / category."""
    entries = [
        SidecarVersionEntry(uc_id="1.1.1", category=1, versions=("Cloud", "9.2+")),
        SidecarVersionEntry(uc_id="1.1.2", category=1, versions=("9.2+",)),
        SidecarVersionEntry(uc_id="2.1.1", category=2, versions=("Cloud",)),
    ]
    matrix = build_matrix(entries, [], _toy_vocab(), total_sidecars=10)
    assert matrix.total_sidecars == 10
    assert matrix.sidecars_with_versions == 3
    assert matrix.per_token_counts == {"Cloud": 2, "9.2+": 2}
    assert matrix.per_track_counts == {"cloud": 2, "9.x": 2}
    assert matrix.per_kind_counts == {"cloud": 2, "on-prem": 2}
    assert matrix.per_category == {1: {"Cloud": 1, "9.2+": 2}, 2: {"Cloud": 1}}
    assert matrix.unknown_findings == []


def test_build_matrix_flags_unknown_token_with_suggestion() -> None:
    """An unknown token surfaces in ``unknown_findings`` with did-you-mean."""
    entries = [
        SidecarVersionEntry(uc_id="1.1.1", category=1, versions=("9.2",))
    ]
    matrix = build_matrix(entries, [], _toy_vocab(), total_sidecars=1)
    assert len(matrix.unknown_findings) == 1
    finding = matrix.unknown_findings[0]
    assert finding.uc_id == "1.1.1"
    assert finding.token == "9.2"
    assert "9.2+" in finding.similar


def test_build_matrix_unknown_token_still_increments_per_token_counts() -> None:
    """Unknown tokens land in per_token_counts so totals round-trip cleanly."""
    entries = [
        SidecarVersionEntry(uc_id="1.1.1", category=1, versions=("Bogus",))
    ]
    matrix = build_matrix(entries, [], _toy_vocab(), total_sidecars=1)
    assert matrix.per_token_counts == {"Bogus": 1}
    assert "Bogus" not in matrix.per_track_counts
    assert "Bogus" not in matrix.per_kind_counts


def test_matrix_to_json_segregates_known_and_unknown() -> None:
    """``per_token_counts`` is keyed by vocab, ``unknown_token_counts`` by drift."""
    matrix = Matrix(
        total_sidecars=2,
        sidecars_with_versions=2,
        per_token_counts={"Cloud": 1, "Bogus": 1},
        per_track_counts={"cloud": 1},
        per_kind_counts={"cloud": 1},
        per_category={1: {"Cloud": 1, "Bogus": 1}},
        unknown_findings=[
            UnknownTokenFinding(uc_id="1.1.1", token="Bogus", similar=())
        ],
    )
    out = _matrix_to_json(matrix, _toy_vocab())
    assert out["per_token_counts"] == {"Cloud": 1, "9.2+": 0}
    assert out["unknown_token_counts"] == {"Bogus": 1}
    assert out["coverage_percent"] == 100.0
    assert out["unknown_findings"][0]["token"] == "Bogus"


def test_matrix_to_json_coverage_handles_zero_total() -> None:
    """A zero-sidecar repo must not divide by zero in coverage_percent."""
    matrix = Matrix(total_sidecars=0, sidecars_with_versions=0)
    out = _matrix_to_json(matrix, _toy_vocab())
    assert out["coverage_percent"] == 0.0


def test_render_markdown_includes_per_category_table() -> None:
    """The markdown report renders the dense 2-D table when categories exist."""
    matrix = Matrix(
        total_sidecars=3,
        sidecars_with_versions=2,
        per_token_counts={"Cloud": 2, "9.2+": 1},
        per_category={1: {"Cloud": 2, "9.2+": 1}},
    )
    md = _render_markdown(matrix, _toy_vocab())
    assert "## Summary" in md
    assert "## Canonical vocabulary" in md
    assert "## Per-category 2-D matrix" in md
    assert "| Category | `9.2+` | `Cloud` |" in md
    assert "| 1 | 1 | 2 |" in md


def test_render_markdown_omits_2d_when_no_categories() -> None:
    """An empty matrix doesn't crash and skips the dense table block."""
    matrix = Matrix(total_sidecars=0, sidecars_with_versions=0)
    md = _render_markdown(matrix, _toy_vocab())
    assert "## Per-category 2-D matrix" not in md


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def test_main_check_mode_returns_nonzero_on_unknown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``main --check`` exits 1 when the corpus contains unknown tokens."""
    from splunk_uc.audits import splunk_version_matrix as svm

    content = tmp_path / "content"
    _write_sidecar(
        content,
        "cat-01-server-compute",
        "1.1.1",
        splunkVersions=["BogusVersion"],
    )
    json_out = tmp_path / "data" / "matrix.json"
    md_out = tmp_path / "docs" / "matrix.md"
    monkeypatch.setattr(svm, "CONTENT_DIR", content)
    monkeypatch.setattr(svm, "MATRIX_JSON_PATH", json_out)
    monkeypatch.setattr(svm, "MATRIX_MD_PATH", md_out)

    rc = svm.main(["--check"])

    assert rc == 1
    err = capsys.readouterr().err
    assert "unknown-token finding" in err
    # --check still produces no in-tree write side effects when --write is off.
    assert not json_out.exists()


def test_main_clean_corpus_returns_zero_and_writes_outputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A clean corpus exits 0 and (in default mode) writes both artefacts."""
    from splunk_uc.audits import splunk_version_matrix as svm

    content = tmp_path / "content"
    _write_sidecar(
        content,
        "cat-01-server-compute",
        "1.1.1",
        splunkVersions=["Cloud", "9.2+"],
    )
    json_out = tmp_path / "data" / "matrix.json"
    md_out = tmp_path / "docs" / "matrix.md"
    monkeypatch.setattr(svm, "CONTENT_DIR", content)
    monkeypatch.setattr(svm, "MATRIX_JSON_PATH", json_out)
    monkeypatch.setattr(svm, "MATRIX_MD_PATH", md_out)

    rc = svm.main([])
    assert rc == 0
    assert json_out.exists()
    assert md_out.exists()
    data = json.loads(json_out.read_text())
    assert data["per_token_counts"]["Cloud"] == 1
    assert data["per_token_counts"]["9.2+"] == 1
    assert data["unknown_token_counts"] == {}


def test_main_preserves_autogenerated_sources_footer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The audit must NOT strip the APA-references footer that
    ``scripts/generate_doc_references.py`` appends.

    The footer is delimited by
    ``<!-- BEGIN-AUTOGENERATED-SOURCES -->`` / ``<!-- END-AUTOGENERATED-SOURCES -->``
    and lives below a ``---`` horizontal rule. We pre-seed the doc
    with a tiny footer, run the audit in write mode, and assert the
    footer (and its separator) survive the overwrite. Without this
    guard the ``Splunk version-matrix audit \u2014 generated artefacts
    are committed`` CI gate fails on every PR.
    """

    from splunk_uc.audits import splunk_version_matrix as svm

    content = tmp_path / "content"
    _write_sidecar(
        content,
        "cat-01-server-compute",
        "1.1.1",
        splunkVersions=["Cloud"],
    )
    json_out = tmp_path / "data" / "matrix.json"
    md_out = tmp_path / "docs" / "matrix.md"
    md_out.parent.mkdir(parents=True)
    seed_footer = (
        "stub body\n\n"
        "---\n\n"
        f"{svm.AUTOGEN_BEGIN_MARKER}\n\n"
        "## References\n\n"
        "**[1]** Seeded source.\n\n"
        f"{svm.AUTOGEN_END_MARKER}\n"
    )
    md_out.write_text(seed_footer, encoding="utf-8")
    monkeypatch.setattr(svm, "CONTENT_DIR", content)
    monkeypatch.setattr(svm, "MATRIX_JSON_PATH", json_out)
    monkeypatch.setattr(svm, "MATRIX_MD_PATH", md_out)

    rc = svm.main([])
    assert rc == 0

    rewritten = md_out.read_text(encoding="utf-8")
    assert svm.AUTOGEN_BEGIN_MARKER in rewritten
    assert svm.AUTOGEN_END_MARKER in rewritten
    assert "Seeded source" in rewritten
    # The "---" rule that lives just above the BEGIN marker must
    # also survive the overwrite.
    begin_idx = rewritten.find(svm.AUTOGEN_BEGIN_MARKER)
    assert "\n---\n" in rewritten[: begin_idx]


def test_extract_autogen_footer_returns_empty_when_missing(
    tmp_path: Path,
) -> None:
    """``_extract_autogen_footer`` is defensive against missing files /
    missing markers so a brand-new doc never crashes the audit."""

    from splunk_uc.audits import splunk_version_matrix as svm

    # Path that does not exist
    assert svm._extract_autogen_footer(tmp_path / "nope.md") == ""

    # File exists but has no markers
    no_marker = tmp_path / "plain.md"
    no_marker.write_text("# Hello\n\nno footer here\n", encoding="utf-8")
    assert svm._extract_autogen_footer(no_marker) == ""

    # BEGIN marker but no END marker — be defensive, treat as missing
    half = tmp_path / "half.md"
    half.write_text(
        f"# Hello\n\n{svm.AUTOGEN_BEGIN_MARKER}\nnever closes\n",
        encoding="utf-8",
    )
    assert svm._extract_autogen_footer(half) == ""


def test_main_json_mode_emits_to_stdout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--json`` emits the structured payload to stdout for piping."""
    from splunk_uc.audits import splunk_version_matrix as svm

    content = tmp_path / "content"
    _write_sidecar(
        content,
        "cat-01-server-compute",
        "1.1.1",
        splunkVersions=["Cloud"],
    )
    monkeypatch.setattr(svm, "CONTENT_DIR", content)
    monkeypatch.setattr(svm, "MATRIX_JSON_PATH", tmp_path / "matrix.json")
    monkeypatch.setattr(svm, "MATRIX_MD_PATH", tmp_path / "matrix.md")

    rc = svm.main(["--json"])
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["per_token_counts"]["Cloud"] == 1


def test_main_missing_vocabulary_returns_two(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A missing vocabulary file is a hard error (exit 2), not a crash."""
    from splunk_uc.audits import splunk_version_matrix as svm

    monkeypatch.setattr(svm, "VOCAB_PATH", tmp_path / "absent.json")

    rc = svm.main([])
    assert rc == 2
    assert "splunk-version vocabulary not found" in capsys.readouterr().err
