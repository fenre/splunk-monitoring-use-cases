"""Tests for tools/build/build_info.py — BUILD-INFO.json emission."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = str(REPO_ROOT / "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from build import parse_content  # noqa: E402
from build import build_info  # noqa: E402


def _minimal_catalog(project_root: Path) -> parse_content.Catalog:
    return parse_content.Catalog(
        project_root=project_root,
        categories=[
            {
                "i": 1,
                "n": "Cat A",
                "s": [
                    {
                        "i": "1.1",
                        "n": "Sub",
                        "u": [{"i": "1.1.1", "n": "UC"}],
                    }
                ],
            }
        ],
        regulations={"r1": {"name": "Rule One", "shortName": "R1"}},
    )


class TestBuildInfoWrite:
    EXPECTED_TOP_KEYS = frozenset({
        "$schema",
        "version",
        "catalogueVersion",
        "apiVersion",
        "git",
        "build",
        "counts",
        "schemas",
        "stability",
    })

    def test_payload_has_expected_structure(self, tmp_path: Path):
        (tmp_path / "VERSION").write_text("9.9.9-test\n", encoding="utf-8")
        catalog = _minimal_catalog(tmp_path)
        dist = tmp_path / "dist"
        dist.mkdir()
        out = build_info.write(dist, catalog)

        assert out.name == "BUILD-INFO.json"
        data = json.loads(out.read_text(encoding="utf-8"))
        assert set(data.keys()) == self.EXPECTED_TOP_KEYS

        assert data["$schema"] == "/schemas/v2/build-info.schema.json"
        assert data["version"] == "2.0.0"
        assert data["catalogueVersion"] == "9.9.9-test"
        assert data["apiVersion"] == "v1"

        git = data["git"]
        assert isinstance(git, dict)
        for key in ("sha", "shortSha", "branch", "commitTimestamp", "tag"):
            assert key in git
            assert isinstance(git[key], str)

        build = data["build"]
        assert build["reproducible"] is False
        assert "timestamp" in build
        assert build["tool"] == "tools/build/build.py"
        assert "python" in build
        assert "platform" in build
        assert "toolVersion" in build

        counts = data["counts"]
        assert counts["categories"] == 1
        assert counts["regulations"] == 1
        assert counts["useCases"] == 1
        assert counts["useCases"] == catalog.uc_count

        assert isinstance(data["schemas"], dict)
        assert isinstance(data["stability"], dict)

    def test_reproducible_flag_and_build_platform(self, tmp_path: Path):
        catalog = parse_content.empty(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        out = build_info.write(out_dir, catalog, reproducible=True)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["build"]["reproducible"] is True
        assert data["build"]["platform"] == "ubuntu-latest"

    def test_catalogue_version_fallback_without_version_file(self, tmp_path: Path):
        catalog = parse_content.empty(tmp_path)
        dist = tmp_path / "dist"
        dist.mkdir()
        build_info.write(dist, catalog)
        data = json.loads((dist / "BUILD-INFO.json").read_text(encoding="utf-8"))
        assert data["catalogueVersion"] == "0.0.0"


class TestBuildInfoHelpers:
    def test_read_version(self, tmp_path: Path):
        assert build_info._read_version(tmp_path) == "0.0.0"
        (tmp_path / "VERSION").write_text("1.2.3", encoding="utf-8")
        assert build_info._read_version(tmp_path) == "1.2.3"

    def test_schema_versions_missing_dir(self, tmp_path: Path):
        assert build_info._schema_versions(tmp_path) == {}

    def test_schema_versions_reads_version_field(self, tmp_path: Path):
        schemas = tmp_path / "schemas"
        schemas.mkdir()
        sch = schemas / "test.schema.json"
        sch.write_text(json.dumps({"version": "3"}), encoding="utf-8")
        out = build_info._schema_versions(tmp_path)
        assert out.get("test.schema.json") == "3"
