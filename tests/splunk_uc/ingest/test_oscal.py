"""Hermetic coverage suite for ``splunk_uc.ingest.oscal``.

The OSCAL driver downloads NIST OSCAL catalogues and profiles, then
normalises them into flat control / included-control lists. We
monkeypatch ``fetch`` to return a stub FetchRecord and pre-seed each
local file with hand-crafted OSCAL JSON, so the suite stays hermetic.

Brings coverage from 21.4% to 100%.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from splunk_uc.ingest import manifest as mf
from splunk_uc.ingest import oscal as os_mod


def _stub_fetch(
    monkeypatch: pytest.MonkeyPatch,
    fail_for: set[str] | None = None,
) -> list[str]:
    """Replace ``fetch`` with a stub that records each source_id and
    raises if it appears in ``fail_for``."""
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
            sha256="x" * 64,
            fetched_at="2026-05-20T10:00:00Z",
        )

    monkeypatch.setattr(os_mod, "fetch", _fake_fetch)
    return seen


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    """Stage a fake repo whose VENDOR_DIR / CROSSWALK_DIR / MANIFEST_PATH
    are rooted under tmp_path."""
    monkeypatch.setattr(os_mod, "_REPO", tmp_path)
    monkeypatch.setattr(os_mod, "VENDOR_DIR", tmp_path / "vendor" / "oscal")
    monkeypatch.setattr(
        os_mod, "CROSSWALK_DIR", tmp_path / "data" / "crosswalks" / "oscal"
    )
    monkeypatch.setattr(
        os_mod,
        "MANIFEST_PATH",
        tmp_path / "data" / "provenance" / "ingest-manifest.json",
    )
    # Repoint each SOURCES entry's local path under the patched vendor dir.
    new_sources = []
    for src in os_mod.SOURCES:
        new = dict(src)
        new["local"] = tmp_path / "vendor" / "oscal" / pathlib.Path(src["local"]).name
        new_sources.append(new)
    monkeypatch.setattr(os_mod, "SOURCES", new_sources)
    return tmp_path


def _seed_catalog(path: pathlib.Path) -> None:
    """Write a minimal OSCAL catalog with one group + nested controls."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "catalog": {
                    "metadata": {
                        "title": "Demo Catalogue",
                        "version": "1.0",
                        "oscal-version": "1.1.2",
                        "last-modified": "2026-05-01T00:00:00Z",
                    },
                    "groups": [
                        {
                            "id": "AC",
                            "title": "Access Control",
                            "controls": [
                                {
                                    "id": "AC-1",
                                    "title": "Policy",
                                    "links": [
                                        {"rel": "related", "href": "#AC-2"}
                                    ],
                                    "props": [
                                        {
                                            "name": "label",
                                            "value": "AC-1",
                                            "ns": "https://nist.gov",
                                        },
                                        # Missing ``name`` → filtered out.
                                        {"value": "ignored"},
                                    ],
                                    "controls": [
                                        {"id": "AC-1.1", "title": "Sub"},
                                    ],
                                }
                            ],
                            "groups": [
                                {
                                    "id": "AC-extra",
                                    "title": "More AC",
                                    "controls": [
                                        {"id": "AC-99", "title": "Extra"},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )


def _seed_profile(path: pathlib.Path) -> None:
    """Write a minimal OSCAL profile with one import + with-ids list."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "profile": {
                    "metadata": {
                        "title": "Demo Profile",
                        "version": "1.0",
                        "oscal-version": "1.1.2",
                        "last-modified": "2026-05-01T00:00:00Z",
                    },
                    "imports": [
                        {
                            "href": "https://example.com/catalog.json",
                            "include-controls": [
                                {"with-ids": ["AC-1", "AC-2"]},
                                # Missing ``with-ids`` → defaults to empty list.
                                {},
                            ],
                        },
                        # Import with no include-controls → also a no-op.
                        {"href": "https://example.com/empty.json"},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )


class TestFlatten:
    def test_handles_nested_controls_and_subgroups(self) -> None:
        acc: list[dict[str, object]] = []
        os_mod._flatten(
            {
                "id": "G",
                "controls": [
                    {
                        "id": "C1",
                        "title": "T1",
                        "controls": [{"id": "C1.1", "title": "T1.1"}],
                    },
                ],
                "groups": [
                    {"id": "G2", "controls": [{"id": "C2", "title": "T2"}]},
                ],
            },
            acc,
            [],
        )
        ids = [c["id"] for c in acc]
        # Outer + nested control + sub-group control all surface.
        assert ids == ["C1", "C1.1", "C2"]

    def test_uses_title_when_group_lacks_id(self) -> None:
        acc: list[dict[str, object]] = []
        os_mod._flatten(
            {"title": "Group Title", "controls": [{"id": "C", "title": "T"}]},
            acc,
            [],
        )
        # The path string should pick up the title fallback.
        assert "Group Title" in str(acc[0]["path"])

    def test_uses_question_mark_when_group_lacks_id_and_title(self) -> None:
        acc: list[dict[str, object]] = []
        os_mod._flatten({"controls": [{"id": "C", "title": "T"}]}, acc, [])
        assert "?" in str(acc[0]["path"])


class TestNormaliseCatalog:
    def test_emits_flat_controls_with_metadata(self) -> None:
        out = os_mod._normalise_catalog(
            "src-id",
            {
                "catalog": {
                    "metadata": {
                        "title": "T",
                        "version": "v",
                        "oscal-version": "ov",
                        "last-modified": "lm",
                    },
                    "groups": [
                        {"id": "G", "controls": [{"id": "C", "title": "ct"}]}
                    ],
                }
            },
        )
        assert out["kind"] == "catalog"
        assert out["source_id"] == "src-id"
        assert out["title"] == "T"
        assert out["control_count"] == 1
        assert out["controls"][0]["id"] == "C"


class TestNormaliseProfile:
    def test_emits_included_controls(self) -> None:
        out = os_mod._normalise_profile(
            "src-id",
            {
                "profile": {
                    "metadata": {"title": "P", "version": "1"},
                    "imports": [
                        {
                            "href": "h",
                            "include-controls": [{"with-ids": ["a", "b"]}],
                        }
                    ],
                }
            },
        )
        assert out["kind"] == "profile"
        assert out["included_control_count"] == 2
        ids = [r["control_id"] for r in out["included_controls"]]
        assert ids == ["a", "b"]


class TestRun:
    def test_full_run_writes_normalised_files_and_manifest(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = _stub_fetch(monkeypatch)
        # Seed every source's local file with either a catalog or
        # profile payload, depending on kind.
        for src in os_mod.SOURCES:
            if src["kind"] == "catalog":
                _seed_catalog(src["local"])
            else:
                _seed_profile(src["local"])

        rc = os_mod.run()
        assert rc == 0
        # Every source was fetched.
        assert seen == [s["id"] for s in os_mod.SOURCES]
        # Each source emitted a *.normalised.json file.
        for src in os_mod.SOURCES:
            out = os_mod.CROSSWALK_DIR / f"{src['id']}.normalised.json"
            assert out.exists()
            body = json.loads(out.read_text(encoding="utf-8"))
            # File ends with a trailing newline.
            assert out.read_text(encoding="utf-8").endswith("\n")
            assert body["kind"] == src["kind"]
        # The manifest was written/merged with one record per source.
        manifest_body = json.loads(os_mod.MANIFEST_PATH.read_text(encoding="utf-8"))
        assert len(manifest_body["provenance"]) == len(os_mod.SOURCES)

    def test_returns_2_on_unknown_kind(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # Replace SOURCES with a single junk-kind entry.
        bad_local = fake_repo / "vendor" / "oscal" / "junk.json"
        bad_local.parent.mkdir(parents=True)
        bad_local.write_text(json.dumps({"catalog": {"metadata": {}}}), encoding="utf-8")
        monkeypatch.setattr(
            os_mod,
            "SOURCES",
            [
                {
                    "id": "junk-kind",
                    "url": "https://example.com/junk.json",
                    "local": bad_local,
                    "kind": "alien",
                }
            ],
        )
        _stub_fetch(monkeypatch)
        rc = os_mod.run()
        assert rc == 2
        assert "unknown kind 'alien'" in capsys.readouterr().err


class TestMain:
    def test_main_returns_run_rc_and_discards_argv(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # No SOURCES → trivial successful run.
        monkeypatch.setattr(os_mod, "SOURCES", [])
        rc = os_mod.main(["--ignored", "--anything"])
        assert rc == 0
        assert os_mod.MANIFEST_PATH.exists()
