"""Tests for ``splunk_uc.audits.dashboards``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from splunk_uc.audits import dashboards as audit
from splunk_uc.generators import dashboards as gen

REPO = Path(__file__).resolve().parents[3]


@pytest.fixture
def mini_corpus(tmp_path: Path) -> tuple[Path, Path]:
    content = tmp_path / "content"
    cat = content / "cat-99-fixture"
    cat.mkdir(parents=True)
    fixture = REPO / "tests" / "fixtures" / "dashboards" / "UC-99.98.01.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    (cat / "UC-99.98.01.json").write_text(json.dumps(payload), encoding="utf-8")
    out = tmp_path / "dashboards"
    gen.emit_all(content, out)
    return content, out


def test_audit_generated_validates_pairs(mini_corpus: tuple[Path, Path]) -> None:
    _, out = mini_corpus
    report = audit.audit_generated(out)
    assert report.checked == 1
    assert report.errors == []


def test_audit_main_requires_check_flag() -> None:
    with pytest.raises(SystemExit):
        audit.main([])


def test_audit_main_ok_after_generate(mini_corpus: tuple[Path, Path]) -> None:
    _, out = mini_corpus
    validation = audit.audit_generated(out)
    assert validation.checked == 1
    assert validation.errors == []


def test_audit_main_fails_on_corrupt_studio(
    mini_corpus: tuple[Path, Path],
) -> None:
    _, out = mini_corpus
    studio = out / "UC-99.98.01" / "studio.xml"
    assert studio.is_file()
    studio.write_text(
        "<dashboard><definition><![CDATA[{not json}]]></definition></dashboard>",
        encoding="utf-8",
    )
    report = audit.audit_generated(out)
    assert report.errors


def test_audit_pipe_per_line_exported() -> None:
    assert audit.check_pipe_per_line("index=x\n| stats count")


def test_audit_validate_spl_rejects_makeresults() -> None:
    errors = audit.validate_spl_text("| makeresults count=1\n| stats count")
    assert any("makeresults" in err for err in errors)


def test_audit_main_runs_check_against_mini_corpus(
    mini_corpus: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    content, out = mini_corpus
    rc = audit.main(["--check", "--out", str(out), "--content", str(content)])
    captured = capsys.readouterr()
    # Single-UC fixture is well below the 500-pair floor — gate returns 1.
    assert rc == 1
    assert "audit-dashboards" in captured.out


def test_audit_main_surfaces_validation_errors(
    mini_corpus: tuple[Path, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    content, out = mini_corpus
    studio = out / "UC-99.98.01" / "studio.xml"
    studio.write_text(
        "<dashboard><definition><![CDATA[{not json}]]></definition></dashboard>",
        encoding="utf-8",
    )
    rc = audit.main(["--check", "--out", str(out), "--content", str(content)])
    captured = capsys.readouterr()
    assert rc == 1
    assert "ERROR" in captured.err


def test_audit_validate_artefact_pair_round_trip(mini_corpus: tuple[Path, Path]) -> None:
    _, out = mini_corpus
    panel_dir = out / "UC-99.98.01"
    simple_text = (panel_dir / "simple.xml").read_text(encoding="utf-8")
    studio_text = (panel_dir / "studio.xml").read_text(encoding="utf-8")
    errors = audit.validate_artefact_pair(simple_text, studio_text)
    assert errors == []


def test_audit_validate_simple_xml_rejects_unknown_root() -> None:
    errors = audit.validate_simple_xml("<not_dashboard></not_dashboard>")
    assert errors


def test_audit_validate_studio_xml_rejects_missing_definition() -> None:
    errors = audit.validate_studio_xml('<dashboard version="2"><label>x</label></dashboard>')
    assert errors


def test_audit_generated_skips_when_no_pairs(tmp_path: Path) -> None:
    report = audit.audit_generated(tmp_path)
    assert report.checked == 0


def test_audit_emit_report_dataclass_round_trip() -> None:
    report = audit.EmitReport(checked=3, drift=0, skipped=0, errors=[], uc_ids=["UC-1.2.3"])
    assert report.checked == 3
    assert report.uc_ids == ["UC-1.2.3"]
