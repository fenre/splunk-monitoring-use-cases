"""Tests for ``splunk_uc.generators.dashboards``."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from splunk_uc.generators import dashboards as gen

REPO = Path(__file__).resolve().parents[3]
FIXTURE = REPO / "tests" / "fixtures" / "dashboards" / "UC-99.98.01.json"
AMP_FIXTURE = {
    "id": "99.98.02",
    "title": "Identity & Access Review",
    "criticality": "high",
    "description": "Tracks privileged access anomalies.",
    "spl": "index=iam sourcetype=okta:system\n| stats count",
}


@pytest.fixture
def fixture_uc() -> dict:
    return gen.load_uc(FIXTURE)


@pytest.fixture
def tmp_content(tmp_path: Path, fixture_uc: dict) -> Path:
    cat = tmp_path / "cat-99-fixture"
    cat.mkdir()
    sidecar = cat / "UC-99.98.01.json"
    sidecar.write_text(json.dumps(fixture_uc), encoding="utf-8")
    high = cat / "UC-99.98.02.json"
    high.write_text(json.dumps(AMP_FIXTURE), encoding="utf-8")
    low = {
        **fixture_uc,
        "id": "99.98.03",
        "criticality": "low",
        "title": "Low priority probe",
    }
    (cat / "UC-99.98.03.json").write_text(json.dumps(low), encoding="utf-8")
    return tmp_path


def test_derive_panel_spl_pipe_per_line(fixture_uc: dict) -> None:
    primary, timechart, table = gen.derive_panel_spl(fixture_uc)
    assert gen.check_pipe_per_line(primary)
    assert gen.check_pipe_per_line(timechart)
    assert gen.check_pipe_per_line(table)
    assert "makeresults" not in primary.lower()


def test_derive_panel_spl_empty_qs_uses_spl() -> None:
    uc = {"spl": "index=main sourcetype= syslog\n| head 10", "cimSpl": "", "qs": ""}
    primary, _, _ = gen.derive_panel_spl(uc)
    assert primary.startswith("index=main")
    assert "| stats count" in primary


def test_derive_panel_spl_multiline_timechart() -> None:
    uc = {
        "spl": (
            "index=os sourcetype=cpu\n"
            "| eval cpu_used = 100 - pctIdle\n"
            "| timechart span=1h avg(cpu_used) as avg_cpu by host\n"
            "| where avg_cpu > 90"
        )
    }
    _, timechart, _ = gen.derive_panel_spl(uc)
    assert "timechart" in timechart
    assert gen.check_pipe_per_line(timechart)


def test_render_simple_xml_escapes_ampersand() -> None:
    uc = {**AMP_FIXTURE, "title": "Identity & Access Review"}
    xml = gen.render_simple_xml(uc)
    assert "Identity &amp; Access Review" in xml
    assert "Identity & Access" not in xml.replace("&amp;", "")


def test_render_studio_json_in_cdata(fixture_uc: dict) -> None:
    xml = gen.render_studio(fixture_uc)
    root = ET.fromstring(xml)
    definition = root.find("definition")
    assert definition is not None and definition.text
    payload = json.loads(definition.text.strip())
    assert payload["title"] == fixture_uc["title"]
    assert "dataSources" in payload
    assert payload["visualizations"]["viz_kpi"]["type"] == "splunk.singlevalue"


def test_template_placeholders_populated(fixture_uc: dict) -> None:
    xml = gen.render_simple_xml(fixture_uc)
    assert "${" not in xml
    assert "UC-99.98.01" in xml
    assert "medium" in xml
    studio = gen.render_studio(fixture_uc)
    assert "${" not in studio


def test_emit_all_writes_three_ucs(tmp_content: Path, tmp_path: Path) -> None:
    out = tmp_path / "dashboards"
    report = gen.emit_all(tmp_content, out)
    assert report.written == 3
    assert (out / "UC-99.98.01" / "simple.xml").is_file()
    assert (out / "UC-99.98.01" / "studio.xml").is_file()


def test_emit_all_criticality_filter(tmp_content: Path, tmp_path: Path) -> None:
    out = tmp_path / "dashboards"
    report = gen.emit_all(tmp_content, out, criticality="high")
    assert report.written == 1
    assert report.uc_ids == ["UC-99.98.02"]


def test_emit_all_only_filter(tmp_content: Path, tmp_path: Path) -> None:
    out = tmp_path / "dashboards"
    report = gen.emit_all(tmp_content, out, only="UC-99.98.03")
    assert report.written == 1
    assert report.uc_ids == ["UC-99.98.03"]


def test_emit_deterministic(tmp_content: Path, tmp_path: Path) -> None:
    out = tmp_path / "dashboards"
    gen.emit_all(tmp_content, out)
    first = (out / "UC-99.98.01" / "simple.xml").read_text(encoding="utf-8")
    gen.emit_all(tmp_content, out)
    second = (out / "UC-99.98.01" / "simple.xml").read_text(encoding="utf-8")
    assert first == second


def test_emit_check_clean_after_write(tmp_content: Path, tmp_path: Path) -> None:
    out = tmp_path / "dashboards"
    gen.emit_all(tmp_content, out)
    report = gen.emit_all(tmp_content, out, check=True)
    assert report.drift == 0
    assert report.errors == []


def test_emit_check_fails_on_drift(tmp_content: Path, tmp_path: Path) -> None:
    out = tmp_path / "dashboards"
    gen.emit_all(tmp_content, out)
    path = out / "UC-99.98.01" / "simple.xml"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    report = gen.emit_all(tmp_content, out, check=True)
    assert report.drift >= 1


def test_validate_no_banned_spl_patterns(fixture_uc: dict) -> None:
    primary, timechart, table = gen.derive_panel_spl(fixture_uc)
    for spl in (primary, timechart, table):
        assert gen.validate_spl_text(spl) == []


def test_studio_types_use_splunk_prefix(fixture_uc: dict) -> None:
    studio = gen.render_studio(fixture_uc)
    errors = gen.validate_studio_xml(studio)
    assert errors == []


def test_main_check_exit_code(tmp_content: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "dashboards"
    monkeypatch.setattr(gen, "CONTENT_ROOT", tmp_content)
    assert gen.main(["--out", str(out)]) == 0
    assert gen.main(["--check", "--out", str(out)]) == 0


def test_main_check_fails_without_output(tmp_content: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "missing"
    monkeypatch.setattr(gen, "CONTENT_ROOT", tmp_content)
    assert gen.main(["--check", "--out", str(out)]) == 1


def test_emit_real_catalog_sample(tmp_path: Path) -> None:
    """Smoke-test one real sidecar when content/ is present."""
    real = REPO / "content" / "cat-01-server-compute" / "UC-1.1.1.json"
    if not real.is_file():
        pytest.skip("catalog sidecar not available")
    uc = gen.load_uc(real)
    simple = gen.render_simple_xml(uc, path=real)
    studio = gen.render_studio(uc, path=real)
    assert gen.validate_artefact_pair(simple, studio) == []


def test_emit_many_real_ucs_meets_floor(tmp_path: Path) -> None:
    content = REPO / "content"
    if not content.is_dir():
        pytest.skip("content/ not available")
    out = tmp_path / "dashboards"
    report = gen.emit_all(content, out, limit=600)
    assert report.written >= 500
    assert report.errors == []
