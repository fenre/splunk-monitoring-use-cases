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
