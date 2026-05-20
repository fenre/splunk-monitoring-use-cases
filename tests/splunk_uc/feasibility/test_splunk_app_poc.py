"""Hermetic coverage suite for ``splunk_uc.feasibility.splunk_app_poc``.

Brings coverage from 16.6% to 100%.

The Phase 0.5d feasibility spike takes a UC sidecar and emits a
minimal AppInspect-shaped Splunk app under ``build/poc/``. All tests
redirect ``REPO``, ``EXEMPLAR``, ``APP_ROOT`` via ``monkeypatch`` so
no files are ever written outside the per-test temporary directory.
"""

from __future__ import annotations

import json
import pathlib
import xml.etree.ElementTree as ET
from typing import Any

import pytest

from splunk_uc.feasibility import splunk_app_poc as poc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_uc(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a minimal exemplar UC payload."""
    payload: dict[str, Any] = {
        "id": "22.35.1",
        "title": "Exemplar UC With [brackets]",
        "criticality": "High",
        "spl": "index=main\n| stats count by host\n| where count > 10",
        "compliance": [
            {"regulation": "GDPR"},
            {"regulation": "HIPAA"},
        ],
    }
    if extra:
        payload.update(extra)
    return payload


@pytest.fixture
def fake_repo(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    """Construct a hermetic repo skeleton and redirect every module path."""
    exemplar = tmp_path / "content" / "cat-22-x" / "UC-22.35.1.json"
    app_root = tmp_path / "build" / "poc" / poc.APP_ID

    monkeypatch.setattr(poc, "REPO", tmp_path)
    monkeypatch.setattr(poc, "EXEMPLAR", exemplar)
    monkeypatch.setattr(poc, "APP_ROOT", app_root)
    return tmp_path


def _write_exemplar(uc: dict[str, Any]) -> None:
    poc.EXEMPLAR.parent.mkdir(parents=True, exist_ok=True)
    poc.EXEMPLAR.write_text(json.dumps(uc), encoding="utf-8")


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


class TestPureHelpers:
    def test_stanza_name_truncates_to_80_chars(self) -> None:
        uc = _make_uc(extra={"title": "x" * 200})
        name = poc.stanza_name(uc)
        # Always starts with the UC ID prefix.
        assert name.startswith("UC-22.35.1 - ")
        # Slug after the " - " separator is capped at 80 chars.
        tail = name.split(" - ", 1)[1]
        assert len(tail) <= 80

    def test_stanza_name_normalises_non_alphanumerics(self) -> None:
        uc = _make_uc(extra={"title": "GDPR / HIPAA: PCI (DSS)"})
        name = poc.stanza_name(uc)
        # Spaces/slashes/punctuation collapse to single underscores.
        assert "GDPR_HIPAA_PCI_DSS" in name

    def test_spl_as_conf_line_returns_input_unchanged_when_single_line(
        self,
    ) -> None:
        assert poc.spl_as_conf_line("  index=main  ") == "index=main"

    def test_spl_as_conf_line_folds_multi_line_with_continuation(self) -> None:
        out = poc.spl_as_conf_line("index=main\n| stats count\n| sort - count")
        # Each pipe stage now sits on its own line connected via ``\``.
        assert " \\\n" in out
        # Trailing whitespace stripped.
        assert "  " not in out.split("\\")[0]


# ---------------------------------------------------------------------------
# Individual writers
# ---------------------------------------------------------------------------


class TestWriters:
    def test_write_app_conf_has_all_required_stanzas(
        self, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "app.conf"
        poc.write_app_conf(path, uc_count=3)
        content = path.read_text(encoding="utf-8")
        # Every required stanza is present.
        for stanza in ("[install]", "[ui]", "[launcher]", "[package]"):
            assert stanza in content
        assert "version = 0.1.0-alpha" in content
        assert "containing 3 compliance" in content

    def test_write_manifest_emits_valid_json_with_schema_2(
        self, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "app.manifest"
        poc.write_manifest(path, uc_count=2)
        manifest = json.loads(path.read_text(encoding="utf-8"))
        assert manifest["schemaVersion"] == "2.0.0"
        assert manifest["info"]["id"]["name"] == poc.APP_ID
        assert manifest["info"]["id"]["version"] == poc.APP_VERSION

    def test_write_savedsearches_emits_one_stanza_per_uc(
        self, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "savedsearches.conf"
        ucs = [_make_uc(), _make_uc(extra={"id": "22.35.2"})]
        poc.write_savedsearches(path, ucs)
        content = path.read_text(encoding="utf-8")
        # Two stanzas (one per UC).
        assert content.count("\nsearch =") == 2
        # Brackets in the title are stripped from the description.
        assert "[brackets]" not in content
        assert "brackets" in content
        # Compliance tags rendered sorted (GDPR before HIPAA).
        assert "GDPR, HIPAA" in content

    def test_write_savedsearches_handles_unknown_criticality(
        self, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "savedsearches.conf"
        uc = _make_uc()
        # Drop the criticality field to pin the "unknown" fallback.
        uc.pop("criticality")
        poc.write_savedsearches(path, [uc])
        assert "criticality: unknown" in path.read_text(encoding="utf-8")

    def test_write_nav_emits_parseable_xml(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "nav.xml"
        poc.write_nav(path)
        tree = ET.fromstring(path.read_text(encoding="utf-8"))
        # Root tag is <nav>.
        assert tree.tag == "nav"
        # One default view + one search view.
        view_names = [v.get("name") for v in tree.findall("view")]
        assert "compliance_overview" in view_names
        assert "search" in view_names

    def test_write_view_emits_parseable_xml(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "view.xml"
        uc = _make_uc()
        poc.write_view(path, uc)
        ET.fromstring(path.read_text(encoding="utf-8"))

    def test_write_meta_emits_two_stanzas(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "default.meta"
        poc.write_meta(path)
        content = path.read_text(encoding="utf-8")
        assert "[]" in content
        assert "[savedsearches]" in content

    def test_write_readme_lists_every_uc(
        self, fake_repo: pathlib.Path, tmp_path: pathlib.Path
    ) -> None:
        path = tmp_path / "README.md"
        ucs = [_make_uc(), _make_uc(extra={"id": "22.35.2"})]
        poc.write_readme(path, ucs)
        content = path.read_text(encoding="utf-8")
        # Both UC IDs listed.
        assert "UC-22.35.1" in content
        assert "UC-22.35.2" in content
        # Provenance footer present.
        assert "Provenance" in content


# ---------------------------------------------------------------------------
# build_app
# ---------------------------------------------------------------------------


class TestBuildApp:
    def test_exits_2_when_exemplar_missing(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            poc.build_app(poc.EXEMPLAR)
        assert exc.value.code == 2
        assert "exemplar UC not found" in capsys.readouterr().err

    def test_writes_complete_tree_when_exemplar_present(
        self, fake_repo: pathlib.Path
    ) -> None:
        _write_exemplar(_make_uc())
        files = poc.build_app(poc.EXEMPLAR)
        # All expected files emitted.
        names = {p.relative_to(poc.APP_ROOT).as_posix() for p in files}
        for expected in (
            "default/app.conf",
            "default/savedsearches.conf",
            "default/data/ui/nav/default.xml",
            "default/data/ui/views/compliance_overview.xml",
            "metadata/default.meta",
            "app.manifest",
            "README.md",
        ):
            assert expected in names

    def test_rebuild_replaces_pre_existing_app_root(
        self, fake_repo: pathlib.Path
    ) -> None:
        _write_exemplar(_make_uc())
        # Pre-create the APP_ROOT with a stray file.
        poc.APP_ROOT.mkdir(parents=True, exist_ok=True)
        stray = poc.APP_ROOT / "stale.txt"
        stray.write_text("stale", encoding="utf-8")
        poc.build_app(poc.EXEMPLAR)
        # The stray file is gone after rebuild.
        assert not stray.exists()


# ---------------------------------------------------------------------------
# shape_check
# ---------------------------------------------------------------------------


class TestShapeCheck:
    def _full_tree(self, fake_repo: pathlib.Path) -> list[pathlib.Path]:
        _write_exemplar(_make_uc())
        return poc.build_app(poc.EXEMPLAR)

    def test_clean_tree_returns_no_errors(
        self, fake_repo: pathlib.Path
    ) -> None:
        files = self._full_tree(fake_repo)
        assert poc.shape_check(files) == []

    def test_empty_file_list_only_reports_required_misses_not_content_checks(
        self, fake_repo: pathlib.Path
    ) -> None:
        """Pin the three ``if <path> in present:`` False branches (366->377,
        378->384, 385->391). With an empty file list the manifest /
        nav / view content-validation blocks are SKIPPED — only the
        seven "missing required file" errors are reported."""
        errors = poc.shape_check([])
        assert len(errors) == 7
        for err in errors:
            assert err.startswith("missing required file")

    def test_missing_required_file_reports_error(
        self, fake_repo: pathlib.Path
    ) -> None:
        files = self._full_tree(fake_repo)
        # Drop the README from the list.
        files = [p for p in files if p.name != "README.md"]
        errors = poc.shape_check(files)
        assert any("README.md" in e for e in errors)

    def test_manifest_with_wrong_schema_reports_error(
        self, fake_repo: pathlib.Path
    ) -> None:
        files = self._full_tree(fake_repo)
        # Overwrite the manifest with a wrong schemaVersion + wrong app id.
        manifest_path = poc.APP_ROOT / "app.manifest"
        manifest_path.write_text(
            json.dumps(
                {
                    "schemaVersion": "1.0.0",
                    "info": {"id": {"name": "WrongAppId"}},
                }
            ),
            encoding="utf-8",
        )
        errors = poc.shape_check(files)
        assert any("schemaVersion" in e for e in errors)
        assert any("info.id.name" in e for e in errors)

    def test_manifest_with_invalid_json_reports_error(
        self, fake_repo: pathlib.Path
    ) -> None:
        files = self._full_tree(fake_repo)
        (poc.APP_ROOT / "app.manifest").write_text(
            "{ not valid", encoding="utf-8"
        )
        errors = poc.shape_check(files)
        assert any("not valid JSON" in e for e in errors)

    def test_invalid_nav_xml_reports_error(
        self, fake_repo: pathlib.Path
    ) -> None:
        files = self._full_tree(fake_repo)
        nav = poc.APP_ROOT / "default" / "data" / "ui" / "nav" / "default.xml"
        nav.write_text("not <xml>", encoding="utf-8")
        errors = poc.shape_check(files)
        assert any("nav/default.xml" in e for e in errors)

    def test_invalid_view_xml_reports_error(
        self, fake_repo: pathlib.Path
    ) -> None:
        files = self._full_tree(fake_repo)
        view = (
            poc.APP_ROOT
            / "default"
            / "data"
            / "ui"
            / "views"
            / "compliance_overview.xml"
        )
        view.write_text("not <xml>", encoding="utf-8")
        errors = poc.shape_check(files)
        assert any("views/compliance_overview.xml" in e for e in errors)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def test_returns_0_on_happy_path(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_exemplar(_make_uc())
        rc = poc.main([])
        assert rc == 0
        out = capsys.readouterr().out
        assert "PASS" in out
        assert "sha256 (tree)" in out

    def test_returns_1_when_shape_check_fails(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write_exemplar(_make_uc())
        monkeypatch.setattr(
            poc, "shape_check", lambda files: ["fabricated error"]
        )
        rc = poc.main([])
        assert rc == 1
        assert "FAIL: fabricated error" in capsys.readouterr().err

    def test_exits_2_when_exemplar_missing(
        self,
        fake_repo: pathlib.Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # build_app raises SystemExit(2) — propagates through main.
        with pytest.raises(SystemExit) as exc:
            poc.main([])
        assert exc.value.code == 2
        assert "exemplar UC not found" in capsys.readouterr().err

    def test_accepts_none_argv(
        self,
        fake_repo: pathlib.Path,
    ) -> None:
        # build_app() raises before we use argv, so this proves argv=None
        # is accepted by the dispatcher contract.
        with pytest.raises(SystemExit):
            poc.main(None)
