"""Comprehensive unit tests for ``src/splunk_uc/audits/regulation_alignment.py``.

Pins every documented contract of the ``audit-regulation-alignment`` lint:

- module-level constants (``REPO`` resolves to a real path);
- the ``_lower_to_canon`` builder (canonical ``id`` always wins, ``shortName``
  and ``aliases`` populate the case-insensitive lookup, whitespace-only and
  non-string labels are skipped, missing ``frameworks`` key returns empty);
- the ``main()`` CLI matrix — unknown regulation labels surface on stderr
  with exit-1, case-insensitive matching, the ``--fix-case`` rewrite path
  (rewrites only when the surface label differs from the canonical id),
  non-list / non-dict / non-string / empty-string compliance rows skipped,
  the path-relative-to-repo formatting in error lines, and the no-rewrite-
  when-already-canonical short circuit.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any, Protocol

import pytest

from splunk_uc.audits import regulation_alignment as ra


class MakeUC(Protocol):
    def __call__(
        self,
        uc_id: str,
        compliance: Any = None,
        category: int = 1,
    ) -> pathlib.Path: ...


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """Build hermetic ``content/`` + ``data/regulations.json`` skeleton."""
    (tmp_path / "content").mkdir()
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(ra, "REPO", tmp_path)
    return tmp_path


@pytest.fixture
def regs_file(fake_repo: pathlib.Path) -> pathlib.Path:
    """Materialise a minimal ``data/regulations.json`` with three frameworks.

    Two frameworks exercise the alias path; one is id-only.
    """
    data = {
        "frameworks": [
            {
                "id": "gdpr",
                "shortName": "GDPR",
                "aliases": ["General Data Protection Regulation", "EU-GDPR"],
            },
            {
                "id": "hipaa",
                "shortName": "HIPAA",
                "aliases": [],
            },
            {
                "id": "pci-dss",
                "shortName": "PCI DSS",
                "aliases": ["PCI-DSS", "PCI"],
            },
        ]
    }
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture
def make_uc(fake_repo: pathlib.Path) -> MakeUC:
    """Factory that materialises a UC sidecar under ``content/cat-NN-foo/``."""

    def _make(
        uc_id: str,
        compliance: Any = None,
        category: int = 1,
    ) -> pathlib.Path:
        cat_dir = fake_repo / "content" / f"cat-{category:02d}-foo"
        cat_dir.mkdir(exist_ok=True)
        sidecar = cat_dir / f"UC-{uc_id}.json"
        payload: dict[str, Any] = {"id": uc_id, "title": f"UC {uc_id}"}
        if compliance is not None:
            payload["compliance"] = compliance
        sidecar.write_text(json.dumps(payload), encoding="utf-8")
        return sidecar

    return _make


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_repo_resolves_to_path() -> None:
    """`REPO` is a `Path` object resolved at import time."""
    assert isinstance(ra.REPO, pathlib.Path)
    assert ra.REPO.is_absolute()


# ---------------------------------------------------------------------------
# _lower_to_canon
# ---------------------------------------------------------------------------


def test_lower_to_canon_id_short_name_aliases_all_lookup_to_canon(
    regs_file: pathlib.Path,
) -> None:
    """Every entry (id, shortName, aliases) maps to the canonical id."""
    m = ra._lower_to_canon(regs_file)
    assert m["gdpr"] == "gdpr"
    assert m["general data protection regulation"] == "gdpr"
    assert m["eu-gdpr"] == "gdpr"
    assert m["hipaa"] == "hipaa"
    assert m["pci-dss"] == "pci-dss"
    assert m["pci dss"] == "pci-dss"
    assert m["pci"] == "pci-dss"


def test_lower_to_canon_keys_are_casefolded(regs_file: pathlib.Path) -> None:
    """All keys are lower (casefolded) — case-insensitive lookup."""
    m = ra._lower_to_canon(regs_file)
    for k in m:
        assert k == k.casefold()


def test_lower_to_canon_short_name_can_differ_from_id(
    regs_file: pathlib.Path,
) -> None:
    """`shortName=PCI DSS` and `id=pci-dss` both map to `pci-dss`."""
    m = ra._lower_to_canon(regs_file)
    assert m["pci dss"] == m["pci-dss"] == "pci-dss"


def test_lower_to_canon_missing_frameworks_returns_empty(
    fake_repo: pathlib.Path,
) -> None:
    """No `frameworks` key → empty lookup."""
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps({}), encoding="utf-8")
    assert ra._lower_to_canon(p) == {}


def test_lower_to_canon_empty_frameworks_returns_empty(
    fake_repo: pathlib.Path,
) -> None:
    """Empty `frameworks` array → empty lookup."""
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps({"frameworks": []}), encoding="utf-8")
    assert ra._lower_to_canon(p) == {}


def test_lower_to_canon_skips_non_string_aliases(
    fake_repo: pathlib.Path,
) -> None:
    """Non-string entries in `aliases` are silently skipped."""
    data = {
        "frameworks": [
            {
                "id": "foo",
                "shortName": "Foo",
                "aliases": ["bar", 42, None, "baz"],
            }
        ]
    }
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    m = ra._lower_to_canon(p)
    assert m == {"foo": "foo", "bar": "foo", "baz": "foo"}


def test_lower_to_canon_skips_whitespace_only_labels(
    fake_repo: pathlib.Path,
) -> None:
    """Whitespace-only strings in any slot are skipped."""
    data = {
        "frameworks": [
            {
                "id": "foo",
                "shortName": "   ",
                "aliases": ["", "  ", "bar"],
            }
        ]
    }
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    m = ra._lower_to_canon(p)
    assert m == {"foo": "foo", "bar": "foo"}


def test_lower_to_canon_missing_aliases_default_empty(
    fake_repo: pathlib.Path,
) -> None:
    """Missing `aliases` key defaults to empty list via `.get(..., [])`."""
    data = {
        "frameworks": [
            {"id": "foo", "shortName": "Foo"},
        ]
    }
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    m = ra._lower_to_canon(p)
    assert m == {"foo": "foo", "foo".casefold(): "foo"}


def test_lower_to_canon_missing_short_name_skipped(
    fake_repo: pathlib.Path,
) -> None:
    """Missing `shortName` (None via `.get`) is filtered by isinstance."""
    data = {
        "frameworks": [
            {"id": "foo", "aliases": ["bar"]},
        ]
    }
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    m = ra._lower_to_canon(p)
    assert m == {"foo": "foo", "bar": "foo"}


def test_lower_to_canon_uppercase_id_lowercased_in_lookup_only(
    fake_repo: pathlib.Path,
) -> None:
    """`id="FOO"` → lookup key is `foo` but canonical (value) stays `FOO`."""
    data = {"frameworks": [{"id": "FOO", "aliases": ["bar"]}]}
    p = fake_repo / "data" / "regulations.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    m = ra._lower_to_canon(p)
    assert m == {"foo": "FOO", "bar": "FOO"}


# ---------------------------------------------------------------------------
# main() — happy paths and scaffolding
# ---------------------------------------------------------------------------


def test_main_empty_content_returns_zero(
    regs_file: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty content tree → exit 0 + no stderr output."""
    assert ra.main([]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_clean_uc_returns_zero(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A UC with a canonical regulation id passes."""
    make_uc(
        "1.1.1",
        compliance=[{"regulation": "gdpr", "clauses": ["Art. 30"]}],
    )
    assert ra.main([]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_case_insensitive_match_passes(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`GDPR` (matches shortName casefolded) is accepted."""
    make_uc(
        "1.1.1",
        compliance=[{"regulation": "GDPR"}],
    )
    assert ra.main([]) == 0
    assert capsys.readouterr().err == ""


def test_main_alias_match_passes(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An alias like `EU-GDPR` matches the canonical id."""
    make_uc(
        "1.1.1",
        compliance=[{"regulation": "EU-GDPR"}],
    )
    assert ra.main([]) == 0
    assert capsys.readouterr().err == ""


def test_main_argv_none_passes_through(
    regs_file: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`argv=None` falls through to argparse's `sys.argv` default."""
    monkeypatch.setattr("sys.argv", ["audit-regulation-alignment"])
    assert ra.main(None) == 0


def test_main_help_exits_cleanly(
    regs_file: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--help` exits with code 0."""
    with pytest.raises(SystemExit) as excinfo:
        ra.main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "--fix-case" in out


# ---------------------------------------------------------------------------
# main() — unknown regulations
# ---------------------------------------------------------------------------


def test_main_unknown_regulation_surfaces_on_stderr(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unknown regulation produces stderr line and exit 1."""
    make_uc(
        "1.1.1",
        compliance=[{"regulation": "Unknown Reg"}],
    )
    assert ra.main([]) == 1
    err = capsys.readouterr().err
    assert "compliance[0].regulation unknown" in err
    assert "'Unknown Reg'" in err
    assert "cat-01-foo/UC-1.1.1.json" in err


def test_main_unknown_regulation_index_in_message(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The index of the offending compliance row is included."""
    make_uc(
        "1.1.1",
        compliance=[
            {"regulation": "gdpr"},
            {"regulation": "Bogus"},
            {"regulation": "hipaa"},
        ],
    )
    assert ra.main([]) == 1
    err = capsys.readouterr().err
    assert "compliance[1].regulation unknown" in err
    assert "compliance[0]" not in err
    assert "compliance[2]" not in err


def test_main_multiple_unknowns_all_reported(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every unknown across the corpus is reported (no early exit)."""
    make_uc("1.1.1", compliance=[{"regulation": "BogusA"}])
    make_uc("1.1.2", compliance=[{"regulation": "BogusB"}])
    assert ra.main([]) == 1
    err = capsys.readouterr().err
    assert "BogusA" in err
    assert "BogusB" in err


# ---------------------------------------------------------------------------
# main() — non-list / non-dict / non-string / empty row handling
# ---------------------------------------------------------------------------


def test_main_non_list_compliance_skipped(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A non-list `compliance` field is skipped (not an error)."""
    make_uc("1.1.1", compliance={"regulation": "BogusA"})
    assert ra.main([]) == 0
    assert capsys.readouterr().err == ""


def test_main_missing_compliance_skipped(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing `compliance` field is silently ignored."""
    make_uc("1.1.1")
    assert ra.main([]) == 0


def test_main_non_dict_compliance_row_skipped(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-dict items inside the compliance array are silently skipped."""
    make_uc(
        "1.1.1",
        compliance=[
            "not-a-dict",
            42,
            None,
            {"regulation": "gdpr"},
        ],
    )
    assert ra.main([]) == 0
    assert capsys.readouterr().err == ""


def test_main_non_string_regulation_skipped(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-string `regulation` value (int, None, list) is skipped silently."""
    make_uc(
        "1.1.1",
        compliance=[
            {"regulation": 42},
            {"regulation": None},
            {"regulation": ["gdpr"]},
        ],
    )
    assert ra.main([]) == 0
    assert capsys.readouterr().err == ""


def test_main_empty_regulation_string_skipped(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty string or whitespace-only regulation is skipped silently."""
    make_uc(
        "1.1.1",
        compliance=[
            {"regulation": ""},
            {"regulation": "   "},
        ],
    )
    assert ra.main([]) == 0
    assert capsys.readouterr().err == ""


def test_main_missing_regulation_key_skipped(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Compliance row without a `regulation` key is skipped silently."""
    make_uc(
        "1.1.1",
        compliance=[{"clauses": ["Art. 30"]}],
    )
    assert ra.main([]) == 0
    assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------
# main() — --fix-case rewrite path
# ---------------------------------------------------------------------------


def test_main_fix_case_rewrites_mismatched_label(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """`--fix-case` rewrites a mismatched surface label to canonical id."""
    sidecar = make_uc(
        "1.1.1",
        compliance=[{"regulation": "GDPR", "clauses": ["Art. 30"]}],
    )
    assert ra.main(["--fix-case"]) == 0
    rewritten = json.loads(sidecar.read_text(encoding="utf-8"))
    assert rewritten["compliance"][0]["regulation"] == "gdpr"
    assert rewritten["compliance"][0]["clauses"] == ["Art. 30"]


def test_main_fix_case_rewrites_alias_to_canon(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """Aliases like `EU-GDPR` rewrite to canonical `gdpr`."""
    sidecar = make_uc(
        "1.1.1",
        compliance=[{"regulation": "EU-GDPR"}],
    )
    assert ra.main(["--fix-case"]) == 0
    rewritten = json.loads(sidecar.read_text(encoding="utf-8"))
    assert rewritten["compliance"][0]["regulation"] == "gdpr"


def test_main_fix_case_no_rewrite_when_already_canonical(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """If surface label already equals canon, no rewrite occurs.

    Note: the file may still be touched if any OTHER row dirties the doc.
    But a single canonical row produces a clean pass and the file content
    stays byte-identical to what `make_uc` wrote.
    """
    sidecar = make_uc(
        "1.1.1",
        compliance=[{"regulation": "gdpr"}],
    )
    original_bytes = sidecar.read_bytes()
    assert ra.main(["--fix-case"]) == 0
    assert sidecar.read_bytes() == original_bytes


def test_main_no_fix_case_does_not_rewrite(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """Without `--fix-case`, a mismatched surface label is left alone."""
    sidecar = make_uc(
        "1.1.1",
        compliance=[{"regulation": "GDPR"}],
    )
    original_bytes = sidecar.read_bytes()
    assert ra.main([]) == 0
    assert sidecar.read_bytes() == original_bytes


def test_main_fix_case_writes_only_dirty_files(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """`--fix-case` only writes files where at least one row was rewritten."""
    sidecar_canonical = make_uc(
        "1.1.1",
        compliance=[{"regulation": "gdpr"}],
        category=1,
    )
    sidecar_mismatched = make_uc(
        "2.1.1",
        compliance=[{"regulation": "GDPR"}],
        category=2,
    )
    original_canonical = sidecar_canonical.read_bytes()
    assert ra.main(["--fix-case"]) == 0
    assert sidecar_canonical.read_bytes() == original_canonical
    rewritten = json.loads(sidecar_mismatched.read_text(encoding="utf-8"))
    assert rewritten["compliance"][0]["regulation"] == "gdpr"


def test_main_fix_case_preserves_unicode(
    fake_repo: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """`ensure_ascii=False` is respected — non-ASCII characters round-trip."""
    data = {
        "frameworks": [
            {"id": "iso", "shortName": "ISO 27001", "aliases": []},
        ]
    }
    (fake_repo / "data" / "regulations.json").write_text(json.dumps(data), encoding="utf-8")
    sidecar = make_uc(
        "1.1.1",
        compliance=[
            {"regulation": "ISO 27001", "clauses": ["Anhang A — éàñ"]},
        ],
    )
    assert ra.main(["--fix-case"]) == 0
    text = sidecar.read_text(encoding="utf-8")
    assert "Anhang A — éàñ" in text
    assert "iso" in json.loads(text)["compliance"][0]["regulation"]


def test_main_fix_case_still_exits_one_on_unknowns(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`--fix-case` does not suppress the unknown-label exit code."""
    sidecar = make_uc(
        "1.1.1",
        compliance=[
            {"regulation": "GDPR"},
            {"regulation": "Bogus"},
        ],
    )
    assert ra.main(["--fix-case"]) == 1
    err = capsys.readouterr().err
    assert "compliance[1].regulation unknown" in err
    rewritten = json.loads(sidecar.read_text(encoding="utf-8"))
    assert rewritten["compliance"][0]["regulation"] == "gdpr"
    assert rewritten["compliance"][1]["regulation"] == "Bogus"


def test_main_fix_case_multiple_rows_one_file(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
) -> None:
    """Multiple mismatched rows in one file all get rewritten in one pass."""
    sidecar = make_uc(
        "1.1.1",
        compliance=[
            {"regulation": "GDPR"},
            {"regulation": "HIPAA"},
            {"regulation": "PCI"},
        ],
    )
    assert ra.main(["--fix-case"]) == 0
    rewritten = json.loads(sidecar.read_text(encoding="utf-8"))
    assert rewritten["compliance"][0]["regulation"] == "gdpr"
    assert rewritten["compliance"][1]["regulation"] == "hipaa"
    assert rewritten["compliance"][2]["regulation"] == "pci-dss"


def test_main_unknown_path_uses_repo_relative_format(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The error path is rendered relative to REPO (no absolute prefix)."""
    make_uc("1.1.1", compliance=[{"regulation": "Bogus"}], category=22)
    assert ra.main([]) == 1
    err = capsys.readouterr().err
    assert "content/cat-22-foo/UC-1.1.1.json" in err
    assert "/tmp/" not in err.split("compliance")[0]


def test_main_sidecars_walked_in_sorted_order(
    regs_file: pathlib.Path,
    make_uc: MakeUC,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Sidecars are walked in sorted order — error lines reflect that."""
    make_uc("1.1.2", compliance=[{"regulation": "B"}])
    make_uc("1.1.1", compliance=[{"regulation": "A"}])
    assert ra.main([]) == 1
    err = capsys.readouterr().err
    pos_a = err.index("'A'")
    pos_b = err.index("'B'")
    assert pos_a < pos_b
