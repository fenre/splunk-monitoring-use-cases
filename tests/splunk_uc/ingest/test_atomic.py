"""Hermetic coverage suite for ``splunk_uc.ingest.atomic``.

The Atomic Red Team driver downloads Red Canary's ``index.yaml``,
walks every tactic → technique → atomic_tests tree, and emits two
flat JSON files: ``atomics.normalised.json`` and
``techniques.normalised.json``. Tests monkeypatch ``fetch`` and
pre-seed ``vendor/atomic-red-team/index.yaml`` with hand-crafted YAML.

Brings coverage from 16.3% to 100%.
"""

from __future__ import annotations

import json
import pathlib

import pytest
import yaml

from splunk_uc.ingest import atomic as atomic_mod
from splunk_uc.ingest import manifest as mf


def _stub_fetch(
    monkeypatch: pytest.MonkeyPatch,
    fail: bool = False,
) -> list[str]:
    seen: list[str] = []

    def _fake_fetch(
        *,
        source_id: str,
        url: str,
        dest: pathlib.Path,
        repo_root: pathlib.Path,
        **_kw: object,
    ) -> mf.FetchRecord:
        seen.append(source_id)
        if fail:
            raise RuntimeError("synthetic-fetch-failure")
        return mf.FetchRecord(
            source_id=source_id,
            url=url,
            local=str(dest),
            bytes=len(dest.read_bytes()) if dest.exists() else 0,
            sha256="r" * 64,
            fetched_at="2026-05-20T10:00:00Z",
        )

    monkeypatch.setattr(atomic_mod, "fetch", _fake_fetch)
    return seen


@pytest.fixture
def fake_repo(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
    monkeypatch.setattr(atomic_mod, "_REPO", tmp_path)
    monkeypatch.setattr(
        atomic_mod, "VENDOR_DIR", tmp_path / "vendor" / "atomic-red-team"
    )
    monkeypatch.setattr(
        atomic_mod,
        "CROSSWALK_DIR",
        tmp_path / "data" / "crosswalks" / "atomic-red-team",
    )
    monkeypatch.setattr(
        atomic_mod,
        "MANIFEST_PATH",
        tmp_path / "data" / "provenance" / "ingest-manifest.json",
    )
    new_source = dict(atomic_mod.SOURCE)
    new_source["local"] = tmp_path / "vendor" / "atomic-red-team" / "index.yaml"
    monkeypatch.setattr(atomic_mod, "SOURCE", new_source)
    return tmp_path


class TestAsListAndFirstLine:
    def test_as_list_handles_none(self) -> None:
        assert atomic_mod._as_list(None) == []

    def test_as_list_returns_list_unchanged(self) -> None:
        assert atomic_mod._as_list([1, 2, 3]) == [1, 2, 3]

    def test_as_list_wraps_scalar(self) -> None:
        assert atomic_mod._as_list("solo") == ["solo"]

    def test_first_line_returns_first_non_empty_line(self) -> None:
        assert atomic_mod._first_line("\n\nhello\nworld\n") == "hello"

    def test_first_line_returns_empty_when_text_only_blank(self) -> None:
        assert atomic_mod._first_line("   \n\n   \n") == ""

    def test_first_line_returns_empty_for_non_string_input(self) -> None:
        # Pin the ``if not isinstance(text, str)`` early-return.
        assert atomic_mod._first_line(None) == ""
        assert atomic_mod._first_line(42) == ""
        assert atomic_mod._first_line(["a", "b"]) == ""


class TestAttackUrl:
    def test_subtechnique_url(self) -> None:
        assert (
            atomic_mod._attack_url("T1059.001")
            == "https://attack.mitre.org/techniques/T1059/001/"
        )

    def test_parent_technique_url(self) -> None:
        assert (
            atomic_mod._attack_url("T1059")
            == "https://attack.mitre.org/techniques/T1059/"
        )


class TestWalkTechniqueBlock:
    def test_returns_empty_when_block_is_not_dict(self) -> None:
        meta, tests = atomic_mod._walk_technique_block("not-a-dict")
        assert meta == {}
        assert tests == []

    def test_extracts_meta_and_tests(self) -> None:
        meta, tests = atomic_mod._walk_technique_block(
            {
                "technique": {"name": "Powershell", "x_mitre_is_subtechnique": True},
                "atomic_tests": [{"name": "test-1"}],
            }
        )
        assert meta == {"name": "Powershell", "x_mitre_is_subtechnique": True}
        assert tests == [{"name": "test-1"}]

    def test_technique_meta_not_dict_is_dropped(self) -> None:
        meta, tests = atomic_mod._walk_technique_block(
            {"technique": "not-a-mapping", "atomic_tests": [{"name": "t"}]}
        )
        assert meta == {}
        assert len(tests) == 1


class TestNormalise:
    def test_raises_value_error_when_doc_not_mapping(self) -> None:
        with pytest.raises(ValueError, match="did not parse as a mapping"):
            atomic_mod._normalise([])
        with pytest.raises(ValueError, match="did not parse as a mapping"):
            atomic_mod._normalise("string-not-dict")

    def test_skips_non_dict_tactic_value(self) -> None:
        """Pin ``if not isinstance(techniques, dict): continue``."""
        out = atomic_mod._normalise({"execution": "not-a-mapping"})
        assert out["techniques_count"] == 0
        assert out["atomics_count"] == 0

    def test_skips_unrecognised_technique_id(self) -> None:
        out = atomic_mod._normalise(
            {
                "execution": {
                    "BAD-ID": {"technique": {"name": "x"}, "atomic_tests": []},
                    "T1059": {"technique": {"name": "PS"}, "atomic_tests": []},
                }
            }
        )
        # Only the well-formed T1059 entry survives.
        ids = [t["attack_id"] for t in out["techniques"]]
        assert ids == ["T1059"]

    def test_aggregates_full_payload(self) -> None:
        out = atomic_mod._normalise(
            {
                "execution": {
                    "T1059.001": {
                        "technique": {
                            "name": "PowerShell",
                            "x_mitre_is_subtechnique": True,
                        },
                        "atomic_tests": [
                            {
                                "name": "test-1",
                                "auto_generated_guid": "guid-1",
                                "description": "first line\nrest",
                                "supported_platforms": ["Windows", "Linux"],
                                "executor": {
                                    "name": "PowerShell",
                                    "cleanup_command": "Remove-Item",
                                },
                                "elevation_required": True,
                            },
                            # Test under same technique → atomic_count increments.
                            {
                                "name": "test-2",
                                "auto_generated_guid": "guid-2",
                                "description": None,  # non-string description
                                "supported_platforms": None,  # _as_list([]) path
                                # executor missing → branches into {} fallback.
                            },
                            # Non-dict element interleaved → filtered.
                            "comment-string-line",
                        ],
                    },
                    "T1059": {
                        "technique": {"name": "Command Line"},
                        "atomic_tests": [
                            {
                                "name": "parent-test",
                                "supported_platforms": ["macOS"],
                                "executor": "not-a-dict",
                            }
                        ],
                    },
                },
                "discovery": {
                    # Re-mentioning T1059 under a different tactic → the
                    # tactics list aggregates without duplicates.
                    "T1059": {"technique": {"name": "Command Line"}, "atomic_tests": []},
                },
            }
        )
        assert out["techniques_count"] == 2
        assert out["atomics_count"] == 3
        # Tactics are sorted + de-duped on T1059.
        cmd = next(t for t in out["techniques"] if t["attack_id"] == "T1059")
        assert sorted(cmd["tactics"]) == ["discovery", "execution"]
        # Platforms are union'd from atomic tests + sorted.
        ps = next(t for t in out["techniques"] if t["attack_id"] == "T1059.001")
        assert ps["platforms"] == ["linux", "windows"]
        # Subtechnique flag survives.
        assert ps["is_subtechnique"] is True
        # The atomics list is sorted on (attack_id, test_name).
        keys = [(a["attack_id"], str(a["test_name"] or "")) for a in out["atomics"]]
        assert keys == sorted(keys)

    def test_blank_technique_name_does_not_overwrite_existing_name(self) -> None:
        """Pin ``if technique_name and not technique_entry['name']`` False
        branch (technique_name truthy but entry already named)."""
        out = atomic_mod._normalise(
            {
                "execution": {
                    "T1059": {"technique": {"name": "First-Seen"}, "atomic_tests": []},
                },
                "discovery": {
                    "T1059": {"technique": {"name": "Different"}, "atomic_tests": []},
                },
            }
        )
        # First-seen name wins.
        assert out["techniques"][0]["name"] == "First-Seen"

    def test_later_mention_supplies_name_when_first_mention_had_none(self) -> None:
        """Pin line 132: ``technique_name`` truthy AND
        ``technique_entry['name']`` falsy → True branch.

        Triggered when the first mention of a technique has no name
        (or an empty one) and a later mention does. The two mentions
        must share the same tactic dict via two keys whose stripped
        form collides on the same ``tid``.
        """
        out = atomic_mod._normalise(
            {
                "execution": {
                    # First mention: empty technique metadata → name=""
                    "T1059": {"technique": {}, "atomic_tests": []},
                    # Second mention (whitespace key) strips to same tid
                    # and supplies the name → True branch fires.
                    " T1059": {
                        "technique": {"name": "Cmd-Interpreter"},
                        "atomic_tests": [],
                    },
                }
            }
        )
        entry = next(t for t in out["techniques"] if t["attack_id"] == "T1059")
        assert entry["name"] == "Cmd-Interpreter"

    def test_duplicate_tactic_for_same_technique_skips_append(self) -> None:
        """Pin branch 133->135: ``tactic_name in technique_entry['tactics']``
        already, so the append is skipped and we drop straight into the
        atomic_tests loop. Same key-collision trick as the test above."""
        out = atomic_mod._normalise(
            {
                "execution": {
                    "T1059": {"technique": {"name": "A"}, "atomic_tests": []},
                    " T1059": {"technique": {"name": "B"}, "atomic_tests": []},
                }
            }
        )
        # Tactics list contains "execution" only once despite the
        # duplicate-key collision.
        entry = next(t for t in out["techniques"] if t["attack_id"] == "T1059")
        assert entry["tactics"] == ["execution"]


class TestRun:
    def test_full_run_writes_two_files_and_manifest(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seen = _stub_fetch(monkeypatch)
        # Seed index.yaml with a minimal but realistic payload.
        payload = {
            "execution": {
                "T1059": {
                    "technique": {"name": "Cmd"},
                    "atomic_tests": [
                        {
                            "name": "tc",
                            "supported_platforms": ["Linux"],
                            "executor": {"name": "bash"},
                        }
                    ],
                }
            }
        }
        atomic_mod.SOURCE["local"].parent.mkdir(parents=True, exist_ok=True)
        atomic_mod.SOURCE["local"].write_text(
            yaml.safe_dump(payload), encoding="utf-8"
        )
        rc = atomic_mod.run()
        assert rc == 0
        assert seen == [atomic_mod.SOURCE["id"]]
        # Both output files exist.
        atomics = atomic_mod.CROSSWALK_DIR / "atomics.normalised.json"
        techniques = atomic_mod.CROSSWALK_DIR / "techniques.normalised.json"
        assert atomics.exists() and techniques.exists()
        # Trailing newline + sorted keys.
        for path in (atomics, techniques):
            text = path.read_text(encoding="utf-8")
            assert text.endswith("\n")
        # Manifest has one record.
        manifest_body = json.loads(atomic_mod.MANIFEST_PATH.read_text(encoding="utf-8"))
        assert len(manifest_body["provenance"]) == 1
        assert manifest_body["provenance"][0]["source_id"] == atomic_mod.SOURCE["id"]

    def test_returns_2_when_fetch_fails(
        self,
        fake_repo: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _stub_fetch(monkeypatch, fail=True)
        rc = atomic_mod.run()
        assert rc == 2
        assert "FAIL: synthetic-fetch-failure" in capsys.readouterr().err
        # No outputs are produced when fetch fails.
        atomics = atomic_mod.CROSSWALK_DIR / "atomics.normalised.json"
        assert not atomics.exists()


class TestMain:
    def test_main_returns_run_rc_and_discards_argv(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_fetch(monkeypatch)
        atomic_mod.SOURCE["local"].parent.mkdir(parents=True, exist_ok=True)
        atomic_mod.SOURCE["local"].write_text(
            yaml.safe_dump({"execution": {}}), encoding="utf-8"
        )
        rc = atomic_mod.main(["--ignored"])
        assert rc == 0
