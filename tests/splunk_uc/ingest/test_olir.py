"""Hermetic coverage suite for ``splunk_uc.ingest.olir``.

The OLIR driver downloads CTID Mappings Explorer JSON, then normalises
each mapping_object into a flat per-mapping record + capability_idx +
attack_idx side tables. Tests monkeypatch ``fetch`` and pre-seed each
source's local file with hand-crafted CTID payloads.

Brings coverage from 22.2% to 100%.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from splunk_uc.ingest import manifest as mf
from splunk_uc.ingest import olir as olir_mod


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
            sha256="o" * 64,
            fetched_at="2026-05-20T10:00:00Z",
        )

    monkeypatch.setattr(olir_mod, "fetch", _fake_fetch)
    return seen


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    monkeypatch.setattr(olir_mod, "_REPO", tmp_path)
    monkeypatch.setattr(olir_mod, "VENDOR_DIR", tmp_path / "vendor" / "olir")
    monkeypatch.setattr(
        olir_mod, "CROSSWALK_DIR", tmp_path / "data" / "crosswalks" / "olir"
    )
    monkeypatch.setattr(
        olir_mod,
        "MANIFEST_PATH",
        tmp_path / "data" / "provenance" / "ingest-manifest.json",
    )
    new_sources = []
    for src in olir_mod.SOURCES:
        new = dict(src)
        new["local"] = tmp_path / "vendor" / "olir" / pathlib.Path(src["local"]).name
        new_sources.append(new)
    monkeypatch.setattr(olir_mod, "SOURCES", new_sources)
    return tmp_path


def _seed_payload(path: pathlib.Path, *, with_orphan: bool = False) -> None:
    """Write a CTID Mappings Explorer payload to ``path``.

    Includes one valid mapping + one orphan if ``with_orphan`` is set.
    """
    objects: list[dict[str, object]] = [
        {
            "capability_id": "CAP-1",
            "capability_description": "Capability 1",
            "capability_group": "Group A",
            "attack_object_id": "T1001",
            "attack_object_name": "Tactic 1",
            "mapping_type": "primary",
            "status": "complete",
            "comments": "n/a",
            "references": [{"href": "https://ref/"}],
        },
        # Same capability mapping to a second technique — exercises the
        # idx-deduping branches in _normalise.
        {
            "capability_id": "CAP-1",
            "capability_description": "Capability 1",
            "capability_group": "Group A",
            "attack_object_id": "T1002",
            "attack_object_name": "Tactic 2",
        },
        # A second capability mapping to the FIRST technique — both
        # capability_idx and attack_idx should aggregate.
        {
            "capability_id": "CAP-2",
            "capability_description": None,
            "capability_group": None,
            "attack_object_id": "T1001",
            "attack_object_name": "Tactic 1",
        },
    ]
    if with_orphan:
        # Missing capability_id → skipped by the `if not ... continue` filter.
        objects.append({"attack_object_id": "T-orphan", "capability_id": None})
        # Missing attack_object_id → also skipped.
        objects.append({"capability_id": "CAP-orphan", "attack_object_id": None})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "metadata": {"upstream": "ctid"},
                "mapping_objects": objects,
            }
        ),
        encoding="utf-8",
    )


class TestNormalise:
    def test_aggregates_capabilities_and_techniques(self) -> None:
        src = {
            "id": "demo",
            "framework": "Demo",
            "framework_id": "demo",
            "framework_version": "v1",
            "attack_version": "16.1",
            "attack_domain": "enterprise",
        }
        payload = {
            "metadata": {"x": 1},
            "mapping_objects": [
                {
                    "capability_id": "C1",
                    "attack_object_id": "T1",
                    "capability_description": "d",
                    "capability_group": "g",
                },
                {
                    "capability_id": "C1",
                    "attack_object_id": "T2",
                    "capability_description": "d",
                },
                {
                    "capability_id": "C2",
                    "attack_object_id": "T1",
                },
            ],
        }
        out = olir_mod._normalise(src, payload)
        # 3 mappings, 2 capabilities, 2 attack IDs.
        assert out["mapping_count"] == 3
        assert out["capabilities_mapped"] == 2
        assert out["attack_ids_mapped"] == 2
        # by_capability is sorted by capability_id.
        cap_ids = [c["capability_id"] for c in out["by_capability"]]
        assert cap_ids == ["C1", "C2"]
        # C1's attack_ids list is sorted + de-duped.
        c1 = next(c for c in out["by_capability"] if c["capability_id"] == "C1")
        assert c1["attack_ids"] == ["T1", "T2"]
        # by_attack carries the same property.
        t1 = next(a for a in out["by_attack"] if a["attack_object_id"] == "T1")
        assert t1["capabilities"] == ["C1", "C2"]
        # The mappings list is sorted on (capability_id, attack_object_id).
        keys = [(r["capability_id"], r["attack_object_id"]) for r in out["mappings"]]
        assert keys == sorted(keys)

    def test_skips_objects_missing_required_fields(self) -> None:
        """Pin the ``if not capability_id or not attack_id: continue`` branch."""
        src = {
            "id": "demo",
            "framework": "Demo",
            "framework_id": "demo",
            "framework_version": "v1",
            "attack_version": "16.1",
            "attack_domain": "enterprise",
        }
        payload = {
            "mapping_objects": [
                {"capability_id": None, "attack_object_id": "T1"},
                {"capability_id": "C1", "attack_object_id": None},
                {"capability_id": "C1", "attack_object_id": "T1"},
            ],
        }
        out = olir_mod._normalise(src, payload)
        assert out["mapping_count"] == 1

    def test_handles_payload_without_mapping_objects(self) -> None:
        src = {
            "id": "demo",
            "framework": "Demo",
            "framework_id": "demo",
            "framework_version": "v1",
            "attack_version": "16.1",
            "attack_domain": "enterprise",
        }
        out = olir_mod._normalise(src, {})
        assert out["mapping_count"] == 0
        assert out["mappings"] == []
        assert out["upstream_metadata"] == {}


class TestRun:
    def test_full_run_writes_files_index_and_manifest(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = _stub_fetch(monkeypatch)
        for src in olir_mod.SOURCES:
            _seed_payload(src["local"])

        rc = olir_mod.run()
        assert rc == 0
        # Every source was fetched.
        assert seen == [s["id"] for s in olir_mod.SOURCES]
        # Each source emitted a normalised file.
        for src in olir_mod.SOURCES:
            out = olir_mod.CROSSWALK_DIR / f"{src['id']}.normalised.json"
            assert out.exists()
            # Trailing newline + deterministic key ordering.
            text = out.read_text(encoding="utf-8")
            assert text.endswith("\n")
            assert text.find('"attack_domain"') < text.find('"mapping_count"')
        # The _index.json file aggregates every source.
        index_path = olir_mod.CROSSWALK_DIR / "_index.json"
        assert index_path.exists()
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        assert idx["source"] == "ctid-mappings-explorer"
        assert {s["source"] for s in idx["sources"]} == {
            s["id"] for s in olir_mod.SOURCES
        }
        # The provenance manifest was merged.
        manifest_body = json.loads(olir_mod.MANIFEST_PATH.read_text(encoding="utf-8"))
        assert len(manifest_body["provenance"]) == len(olir_mod.SOURCES)

    def test_returns_2_on_fetch_failure_and_stops_at_first(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Pin the ``except Exception: return 2`` branch."""
        # Make the very first source fail.
        first_id = olir_mod.SOURCES[0]["id"]
        seen = _stub_fetch(monkeypatch, fail_for={first_id})
        rc = olir_mod.run()
        assert rc == 2
        # Only the failing source was attempted (the loop short-circuits).
        assert seen == [first_id]
        # The FAIL line is printed to stderr.
        assert "FAIL: synthetic-fetch-failure" in capsys.readouterr().err
        # No _index.json or normalised file is produced when fetch fails.
        assert not (olir_mod.CROSSWALK_DIR / "_index.json").exists()


class TestMain:
    def test_main_returns_run_rc_and_discards_argv(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(olir_mod, "SOURCES", [])
        rc = olir_mod.main(["--ignored", "--anything"])
        assert rc == 0
        # _index.json should still be written even when there are no sources.
        assert (olir_mod.CROSSWALK_DIR / "_index.json").exists()
