"""Hermetic coverage suite for ``splunk_uc.ingest.attack``.

The ATT&CK driver downloads three MITRE STIX 2.1 bundles (Enterprise /
ICS / Mobile) and normalises every supported STIX object type into
flat JSON. Tests monkeypatch ``fetch`` and pre-seed each source's local
file with hand-crafted bundles that exercise every STIX type the
normaliser knows about.

Brings coverage from 15.0% to 100%.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from splunk_uc.ingest import attack as atk
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
            sha256="a" * 64,
            fetched_at="2026-05-20T10:00:00Z",
        )

    monkeypatch.setattr(atk, "fetch", _fake_fetch)
    return seen


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    monkeypatch.setattr(atk, "_REPO", tmp_path)
    monkeypatch.setattr(atk, "VENDOR_DIR", tmp_path / "vendor" / "attack")
    monkeypatch.setattr(
        atk, "CROSSWALK_DIR", tmp_path / "data" / "crosswalks" / "attack"
    )
    monkeypatch.setattr(
        atk,
        "MANIFEST_PATH",
        tmp_path / "data" / "provenance" / "ingest-manifest.json",
    )
    new_sources = []
    for src in atk.SOURCES:
        new = dict(src)
        new["local"] = tmp_path / "vendor" / "attack" / pathlib.Path(src["local"]).name
        new_sources.append(new)
    monkeypatch.setattr(atk, "SOURCES", new_sources)
    return tmp_path


def _bundle() -> dict[str, object]:
    """Build a STIX bundle with every type the normaliser supports."""
    return {
        "id": "bundle--demo",
        "objects": [
            # Technique with external mitre-attack ref + sub-tech + tactics.
            {
                "type": "attack-pattern",
                "id": "ap--1",
                "name": "Exec via PowerShell",
                "description": "demo",
                "external_references": [
                    {
                        "source_name": "mitre-attack",
                        "external_id": "T1059.001",
                        "url": "https://attack.mitre.org/T1059/001/",
                    }
                ],
                "kill_chain_phases": [{"phase_name": "execution"}],
                "x_mitre_platforms": ["Windows"],
                "x_mitre_data_sources": ["Process: Process Creation"],
                "x_mitre_detection": "Monitor for powershell.exe",
                "x_mitre_is_subtechnique": True,
                "revoked": False,
                "x_mitre_deprecated": False,
                "created": "2020-01-01",
                "modified": "2026-01-01",
            },
            # Tactic.
            {
                "type": "x-mitre-tactic",
                "id": "tac--1",
                "name": "Execution",
                "x_mitre_shortname": "execution",
            },
            # Mitigation.
            {
                "type": "course-of-action",
                "id": "coa--1",
                "name": "Application Whitelisting",
            },
            # Group with aliases.
            {
                "type": "intrusion-set",
                "id": "is--1",
                "name": "APT-X",
                "aliases": ["AKA1", "AKA2"],
            },
            # Software entries — both malware and tool variants share
            # the same dispatch arm.
            {"type": "malware", "id": "mw--1", "name": "MalwareX"},
            {"type": "tool", "id": "tl--1", "name": "ToolY"},
            # Campaign with aliases.
            {
                "type": "campaign",
                "id": "ca--1",
                "name": "OpZero",
                "aliases": ["Op0"],
            },
            # Data source + component.
            {"type": "x-mitre-data-source", "id": "ds--1", "name": "Process"},
            {
                "type": "x-mitre-data-component",
                "id": "dc--1",
                "name": "Process Creation",
                "x_mitre_data_source_ref": "ds--1",
            },
            # Relationship.
            {
                "type": "relationship",
                "id": "rel--1",
                "relationship_type": "uses",
                "source_ref": "is--1",
                "target_ref": "ap--1",
                "description": "APT-X uses T1059.001",
            },
            # Unknown type — silently ignored.
            {"type": "x-mitre-asset", "id": "asset--1"},
            # Object with no external_references → empty attack_id.
            {
                "type": "attack-pattern",
                "id": "ap--2",
                "name": "No-Refs",
                "external_references": [],
            },
            # Object whose only external_reference is non-mitre-attack →
            # empty attack_id (pins the `startswith` filter False branch).
            {
                "type": "attack-pattern",
                "id": "ap--3",
                "name": "Wrong-Source",
                "external_references": [
                    {"source_name": "capec", "external_id": "CAPEC-100"}
                ],
            },
            # mitre-attack ref without external_id → still empty attack_id
            # (pins the `if ref.get("external_id")` False branch).
            {
                "type": "attack-pattern",
                "id": "ap--4",
                "name": "Missing-ExtID",
                "external_references": [
                    {"source_name": "mitre-attack", "url": "https://attack.mitre.org/x/"}
                ],
            },
        ],
    }


class TestHelpers:
    def test_attack_id_returns_external_id_on_match(self) -> None:
        assert (
            atk._attack_id(
                {
                    "external_references": [
                        {"source_name": "mitre-attack", "external_id": "T1059"}
                    ]
                }
            )
            == "T1059"
        )

    def test_attack_id_returns_empty_when_no_match(self) -> None:
        assert atk._attack_id({"external_references": []}) == ""
        assert atk._attack_id({}) == ""
        # mitre-attack source but no external_id → False branch of inner if.
        assert (
            atk._attack_id(
                {"external_references": [{"source_name": "mitre-attack"}]}
            )
            == ""
        )
        # Non-mitre source → False branch of startswith.
        assert (
            atk._attack_id(
                {
                    "external_references": [
                        {"source_name": "capec", "external_id": "CAPEC-X"}
                    ]
                }
            )
            == ""
        )

    def test_external_url_returns_url_on_match(self) -> None:
        url = atk._external_url(
            {
                "external_references": [
                    {"source_name": "mitre-attack", "url": "https://x/"}
                ]
            }
        )
        assert url == "https://x/"

    def test_external_url_skips_when_url_missing(self) -> None:
        # mitre-attack ref but no url → loop continues, returns "".
        assert (
            atk._external_url(
                {"external_references": [{"source_name": "mitre-attack"}]}
            )
            == ""
        )


class TestNormalise:
    def test_dispatches_every_stix_type(self) -> None:
        out = atk._normalise("enterprise", _bundle())
        # techniques: 4 attack-patterns in the bundle (1 valid + 3 edge).
        assert out["techniques_count"] == 4
        assert out["tactics_count"] == 1
        assert out["mitigations_count"] == 1
        assert out["groups_count"] == 1
        # malware + tool both dispatch into software.
        assert out["software_count"] == 2
        assert out["campaigns_count"] == 1
        assert out["data_sources_count"] == 1
        assert out["data_components_count"] == 1
        assert out["relationships_count"] == 1
        assert out["domain"] == "enterprise"
        assert out["bundle_id"] == "bundle--demo"

    def test_handles_bundle_with_no_objects(self) -> None:
        out = atk._normalise("ics", {"id": "b", "objects": None})
        assert out["techniques_count"] == 0
        assert out["domain"] == "ics"

    def test_revoked_and_deprecated_flags_propagate(self) -> None:
        out = atk._normalise(
            "enterprise",
            {
                "id": "b",
                "objects": [
                    {
                        "type": "course-of-action",
                        "id": "coa--r",
                        "name": "Revoked",
                        "revoked": True,
                        "x_mitre_deprecated": True,
                    }
                ],
            },
        )
        assert out["mitigations"][0]["revoked"] is True
        assert out["mitigations"][0]["deprecated"] is True


class TestRun:
    def test_full_run_writes_normalised_files_and_manifest(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = _stub_fetch(monkeypatch)
        for src in atk.SOURCES:
            src["local"].parent.mkdir(parents=True, exist_ok=True)
            src["local"].write_text(json.dumps(_bundle()), encoding="utf-8")

        rc = atk.run()
        assert rc == 0
        assert seen == [s["id"] for s in atk.SOURCES]
        for src in atk.SOURCES:
            out = atk.CROSSWALK_DIR / f"{src['id']}.normalised.json"
            assert out.exists()
            body = json.loads(out.read_text(encoding="utf-8"))
            assert body["domain"] == src["domain"]
            # File ends with a trailing newline + sorted keys.
            assert out.read_text(encoding="utf-8").endswith("\n")
        # Manifest got one record per source.
        manifest_body = json.loads(atk.MANIFEST_PATH.read_text(encoding="utf-8"))
        assert len(manifest_body["provenance"]) == len(atk.SOURCES)

    def test_returns_2_on_fetch_failure_at_first_source(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        first_id = atk.SOURCES[0]["id"]
        seen = _stub_fetch(monkeypatch, fail_for={first_id})
        rc = atk.run()
        assert rc == 2
        # The loop short-circuits at the first failure.
        assert seen == [first_id]
        assert "FAIL: synthetic-fetch-failure" in capsys.readouterr().err


class TestMain:
    def test_main_returns_run_rc_and_discards_argv(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(atk, "SOURCES", [])
        rc = atk.main(["--ignored", "--anything"])
        assert rc == 0
        assert atk.MANIFEST_PATH.exists()
