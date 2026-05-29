"""Tests for ``splunk_uc.generators.alert_actions`` (Task H-4)."""

from __future__ import annotations

import html.parser
import tempfile
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONTENT = _REPO_ROOT / "content"
_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "alert-actions"

from splunk_uc.generators import alert_actions as M  # noqa: E402

FIXTURE_UCS = ("UC-1.1.1", "UC-1.1.10", "UC-1.2.20")


class _HtmlSmokeParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag, attrs

    def error(self, message: str) -> None:
        self.errors.append(message)


def _sidecar_for(uc_id: str) -> Path:
    stem = uc_id.removeprefix("UC-")
    matches = sorted(_CONTENT.glob(f"cat-*/UC-{stem}.json"))
    assert matches, f"missing sidecar for {uc_id}"
    return matches[0]


@pytest.mark.parametrize("uc_id", FIXTURE_UCS)
def test_generator_emits_three_files_per_fixture_uc(uc_id: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        rendered = M.render_templates(M.load_uc_record(_sidecar_for(uc_id)))
        M.write_templates(rendered, out)
        assert (out / "soar" / f"{uc_id}.yaml").is_file()
        assert (out / "email" / f"{uc_id}.html").is_file()
        assert (out / "email" / f"{uc_id}.txt").is_file()


def test_criticality_tiers_map_to_distinct_subjects() -> None:
    high = M.render_templates(M.load_uc_record(_sidecar_for("UC-1.1.1")))
    med = M.render_templates(M.load_uc_record(_sidecar_for("UC-1.1.10")))
    low = M.render_templates(M.load_uc_record(_sidecar_for("UC-1.2.20")))
    assert "[CRITICAL]" in high.email_html
    assert "[ALERT]" in med.email_html
    assert "[INFO]" in low.email_html


def test_determinism_two_runs_byte_identical() -> None:
    path = _sidecar_for("UC-1.1.1")
    first = M.render_templates(M.load_uc_record(path))
    second = M.render_templates(M.load_uc_record(path))
    assert first == second


def test_check_passes_on_golden_fixtures() -> None:
    assert M.main(["--check", "--limit", "20", "--fixtures-root", str(_FIXTURES)]) == 0


def test_check_fails_when_fixture_drifted(tmp_path: Path) -> None:
    drift_root = tmp_path / "fixtures"
    drift_root.mkdir()
    (drift_root / "soar").mkdir()
    (drift_root / "email").mkdir()
    (drift_root / "soar" / "UC-1.1.1.yaml").write_text("name: stale\n", encoding="utf-8")
    (drift_root / "email" / "UC-1.1.1.html").write_text("<html></html>\n", encoding="utf-8")
    (drift_root / "email" / "UC-1.1.1.txt").write_text("stale\n", encoding="utf-8")
    assert M.main(["--check", "--fixtures-root", str(drift_root)]) == 1


@pytest.mark.parametrize("uc_id", FIXTURE_UCS)
def test_soar_yaml_parses(uc_id: str) -> None:
    rendered = M.render_templates(M.load_uc_record(_sidecar_for(uc_id)))
    doc = yaml.safe_load(rendered.soar_yaml)
    assert isinstance(doc, dict)
    assert doc["uc_id"] == uc_id
    assert doc["human_acknowledgement_required"] is True
    assert "spl_reference" in doc


@pytest.mark.parametrize("uc_id", FIXTURE_UCS)
def test_html_parses_without_errors(uc_id: str) -> None:
    rendered = M.render_templates(M.load_uc_record(_sidecar_for(uc_id)))
    parser = _HtmlSmokeParser()
    parser.feed(rendered.email_html)
    assert parser.errors == []


@pytest.mark.parametrize("uc_id", FIXTURE_UCS)
def test_required_runtime_placeholders_present(uc_id: str) -> None:
    rendered = M.render_templates(M.load_uc_record(_sidecar_for(uc_id)))
    for blob in (rendered.email_html, rendered.email_txt):
        assert uc_id in blob
        assert "{timestamp_placeholder}" in blob
        assert "{spl_summary}" in blob
        assert "fenre.github.io" in blob


def test_limit_caps_uc_count() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        count = M.generate_all(content_dir=_CONTENT, out_dir=out, limit=5)
        assert count == 5
        assert len(list((out / "soar").glob("UC-*.yaml"))) == 5
