"""Tests for permanent-identity ledger and UC ID audits."""

from __future__ import annotations

import json
import pathlib
from typing import Any

import pytest

from splunk_uc import id_ledger
from splunk_uc.audits import uc_id_migration_blast, uc_ids
from splunk_uc.generators import id_ledger as gen_id_ledger


@pytest.fixture
def fake_repo(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    content = tmp_path / "content"
    content.mkdir()
    ledger = tmp_path / "data"
    ledger.mkdir()
    migrations = ledger / "uc-id-migrations"
    migrations.mkdir()
    version = tmp_path / "VERSION"
    version.write_text("9.9.9\n", encoding="utf-8")

    monkeypatch.setattr(id_ledger, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(id_ledger, "CONTENT", content)
    monkeypatch.setattr(id_ledger, "LEDGER_PATH", ledger / "id-ledger.json")
    monkeypatch.setattr(id_ledger, "COLLISIONS_PATH", ledger / "id-ledger-collisions.json")
    monkeypatch.setattr(id_ledger, "MIGRATIONS_DIR", migrations)
    monkeypatch.setattr(id_ledger, "VERSION_PATH", version)
    monkeypatch.setattr(id_ledger, "CAT25_REMAP_PATH", ledger / "cat25_id_remap.json")

    monkeypatch.setattr(uc_ids, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(uc_ids, "CONTENT", content)
    monkeypatch.setattr(uc_ids, "LEDGER_PATH", ledger / "id-ledger.json")

    monkeypatch.setattr(gen_id_ledger, "LEDGER_PATH", ledger / "id-ledger.json")

    monkeypatch.setattr(uc_id_migration_blast, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(uc_id_migration_blast, "CONTENT", content)
    monkeypatch.setattr(uc_id_migration_blast, "MIGRATIONS_DIR", migrations)
    return tmp_path


def _make_cat(fake_repo: pathlib.Path, category: int) -> pathlib.Path:
    cat = fake_repo / "content" / f"cat-{category:02d}-test"
    cat.mkdir(parents=True, exist_ok=True)
    return cat


def _write_uc(cat: pathlib.Path, uc_id: str, title: str = "Test UC", spl: str = "index=x") -> None:
    payload = {"id": uc_id, "title": title, "spl": spl}
    (cat / f"UC-{uc_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_ledger(fake_repo: pathlib.Path, entries: list[dict[str, Any]]) -> None:
    normalized: list[dict[str, Any]] = []
    for entry in entries:
        row = dict(entry)
        fp = row.get("contentFingerprint", "")
        if fp and "fingerprintRevisions" not in row:
            row["fingerprintRevisions"] = [
                {
                    "contentFingerprint": fp,
                    "catalogueVersion": row.get("firstSeenVersion", "9.9.9"),
                }
            ]
        normalized.append(row)
    doc = {
        "schemaVersion": "1.1.0",
        "generatedAt": "2026-09-01T00:00:00Z",
        "catalogueCommit": "abc1234",
        "catalogueVersion": "9.9.9",
        "identityGuaranteeSince": "8.26.0",
        "identityBaselineVersion": "8.25.0",
        "identityBaselineCommit": id_ledger.IDENTITY_BASELINE_COMMIT,
        "hashAlgorithm": "sha256",
        "fingerprintFields": ["title", "spl"],
        "entryCount": len(normalized),
        "entries": normalized,
    }
    path = fake_repo / "data" / "id-ledger.json"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


class TestFingerprintRevisions:
    def test_merge_appends_on_content_change(self) -> None:
        prior = {
            "contentFingerprint": "a" * 64,
            "fingerprintRevisions": [
                {
                    "contentFingerprint": "a" * 64,
                    "catalogueVersion": "8.25.0",
                }
            ],
        }
        new_fp = "b" * 64
        revisions = id_ledger.merge_fingerprint_revisions(
            prior, new_fp, "8.26.0", "deadbeef"
        )
        assert len(revisions) == 2
        assert revisions[-1]["contentFingerprint"] == new_fp
        assert revisions[-1]["catalogueVersion"] == "8.26.0"

    def test_merge_does_not_duplicate_same_fingerprint(self) -> None:
        fp = "c" * 64
        prior = {
            "contentFingerprint": fp,
            "fingerprintRevisions": [{"contentFingerprint": fp, "catalogueVersion": "8.25.0"}],
        }
        revisions = id_ledger.merge_fingerprint_revisions(prior, fp, "8.26.0", "deadbeef")
        assert len(revisions) == 1

    def test_revision_shortening_fails_validation(self) -> None:
        previous = {
            "entries": [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": "a" * 64,
                    "fingerprintRevisions": [
                        {"contentFingerprint": "a" * 64, "catalogueVersion": "8.25.0"},
                        {"contentFingerprint": "b" * 64, "catalogueVersion": "8.26.0"},
                    ],
                    "firstSeenVersion": "8.25.0",
                }
            ]
        }
        new_doc = {
            "entries": [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": "b" * 64,
                    "fingerprintRevisions": [
                        {"contentFingerprint": "b" * 64, "catalogueVersion": "8.26.0"},
                    ],
                    "firstSeenVersion": "8.25.0",
                }
            ]
        }
        issues = id_ledger.validate_ledger_revision_monotonicity(previous, new_doc)
        assert any("shortened" in i for i in issues)


class TestContentFingerprint:
    def test_stable_for_same_payload(self) -> None:
        payload = {"title": "Alpha", "spl": "index=a"}
        assert id_ledger.content_fingerprint(payload) == id_ledger.content_fingerprint(payload)

    def test_changes_when_title_changes(self) -> None:
        a = {"title": "Alpha", "spl": "index=a"}
        b = {"title": "Beta", "spl": "index=a"}
        assert id_ledger.content_fingerprint(a) != id_ledger.content_fingerprint(b)


class TestLedgerValidation:
    def test_missing_catalogue_id_fails(self, fake_repo: pathlib.Path) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        _write_ledger(fake_repo, [])
        issues = id_ledger.validate_catalogue_against_ledger()
        assert any("missing from data/id-ledger.json" in i for i in issues)

    def test_removed_identifier_cannot_be_reissued(self, fake_repo: pathlib.Path) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        _write_ledger(
            fake_repo,
            [
                {
                    "id": "1.1.1",
                    "status": "removed",
                    "contentFingerprint": id_ledger.UNKNOWN_FINGERPRINT,
                    "firstSeenVersion": "8.0.0",
                    "removedInVersion": "8.1.0",
                }
            ],
        )
        issues = id_ledger.validate_catalogue_against_ledger()
        assert any("Reuse of removed identifier" in i for i in issues)

    def test_fingerprint_mismatch_fails(self, fake_repo: pathlib.Path) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1", title="Live title", spl="index=live")
        _write_ledger(
            fake_repo,
            [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": "0" * 64,
                    "firstSeenVersion": "8.25.0",
                }
            ],
        )
        issues = id_ledger.validate_catalogue_against_ledger()
        assert any("Fingerprint mismatch" in i for i in issues)


class TestAuditUcIdsIntegration:
    def test_gaps_do_not_fail(self, fake_repo: pathlib.Path) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        _write_uc(cat, "1.1.3")
        fp = id_ledger.content_fingerprint({"title": "Test UC", "spl": "index=x"})
        _write_ledger(
            fake_repo,
            [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": fp,
                    "firstSeenVersion": "8.25.0",
                },
                {
                    "id": "1.1.3",
                    "status": "active",
                    "contentFingerprint": fp,
                    "firstSeenVersion": "8.25.0",
                },
            ],
        )
        assert uc_ids.main([]) == 0

    def test_reuse_fails_audit(self, fake_repo: pathlib.Path) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        _write_ledger(
            fake_repo,
            [
                {
                    "id": "1.1.1",
                    "status": "removed",
                    "contentFingerprint": id_ledger.UNKNOWN_FINGERPRINT,
                    "firstSeenVersion": "8.0.0",
                    "removedInVersion": "8.1.0",
                }
            ],
        )
        rc = uc_ids.main([])
        assert rc == 1


class TestGenerateIdLedger:
    def test_removal_leaves_gap_without_renumbering(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.2")
        previous = {
            "entries": [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": id_ledger.content_fingerprint(
                        {"title": "Test UC", "spl": "index=x"}
                    ),
                    "firstSeenVersion": "8.25.0",
                },
                {
                    "id": "1.1.2",
                    "status": "active",
                    "contentFingerprint": id_ledger.content_fingerprint(
                        {"title": "Test UC", "spl": "index=x"}
                    ),
                    "firstSeenVersion": "8.25.0",
                },
            ]
        }
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: {"1.1.1"})
        doc = id_ledger.build_ledger_document(previous=previous)
        active_ids = {e["id"] for e in doc["entries"] if e["status"] == "active"}
        removed_ids = {e["id"] for e in doc["entries"] if e["status"] == "removed"}
        assert active_ids == {"1.1.2"}
        assert removed_ids == {"1.1.1"}

    def test_baseline_seed_records_tag_content_as_revision_one(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1", title="Rewritten title", spl="index=new")
        _write_uc(cat, "1.1.2")
        _write_uc(cat, "1.1.3", title="Added after baseline")
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: set())
        baseline = {
            "1.1.1": {"id": "1.1.1", "title": "Original title", "spl": "index=old"},
            "1.1.2": {"id": "1.1.2", "title": "Test UC", "spl": "index=x"},
        }
        doc = id_ledger.build_ledger_document(baseline=baseline)
        by_id = {e["id"]: e for e in doc["entries"]}

        rewritten = by_id["1.1.1"]["fingerprintRevisions"]
        assert [r["catalogueVersion"] for r in rewritten] == [
            id_ledger.IDENTITY_BASELINE_VERSION,
            "9.9.9",
        ]
        assert rewritten[0]["contentFingerprint"] == id_ledger.content_fingerprint(
            baseline["1.1.1"]
        )
        assert rewritten[0]["catalogueCommit"] == id_ledger.IDENTITY_BASELINE_COMMIT

        assert len(by_id["1.1.2"]["fingerprintRevisions"]) == 1
        assert by_id["1.1.2"]["firstSeenVersion"] == id_ledger.IDENTITY_BASELINE_VERSION
        assert by_id["1.1.3"]["firstSeenVersion"] == "9.9.9"
        assert "firstSeenVersionSource" not in by_id["1.1.3"]

    def test_removal_before_baseline_omits_removed_in_version(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _make_cat(fake_repo, 1)
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: {"1.1.9"})
        monkeypatch.setattr(id_ledger, "_git_last_payload", lambda _uc_id: None)
        doc = id_ledger.build_ledger_document(baseline={})
        (entry,) = doc["entries"]
        assert entry["status"] == "removed"
        assert "removedInVersion" not in entry
        assert entry["removedInVersionNote"]

    def test_regeneration_keeps_notes_and_undiscovered_removals(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        fp = id_ledger.content_fingerprint({"title": "Test UC", "spl": "index=x"})
        removed_row = {
            "id": "1.1.5",
            "status": "removed",
            "contentFingerprint": fp,
            "fingerprintRevisions": [{"contentFingerprint": fp, "catalogueVersion": "unknown"}],
            "firstSeenVersion": "unknown",
            "removedInVersionNote": "before baseline",
        }
        previous = {
            "generatedAt": "2026-09-01T00:00:00Z",
            "catalogueCommit": "abc1234",
            "catalogueVersion": "9.9.9",
            "entries": [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": fp,
                    "fingerprintRevisions": [{"contentFingerprint": fp, "catalogueVersion": "8.25.0"}],
                    "firstSeenVersion": "8.25.0",
                    "firstSeenVersionSource": "identity-baseline",
                    "firstSeenVersionNote": "note",
                },
                removed_row,
            ],
        }
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: set())
        doc = id_ledger.build_ledger_document(previous=previous)
        by_id = {e["id"]: e for e in doc["entries"]}
        assert by_id["1.1.1"]["firstSeenVersionSource"] == "identity-baseline"
        assert by_id["1.1.5"] == removed_row
        assert doc["generatedAt"] == "2026-09-01T00:00:00Z"
        assert doc["catalogueCommit"] == "abc1234"

    def test_header_refreshes_when_entries_change(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1", title="Edited")
        previous = {
            "generatedAt": "2026-09-01T00:00:00Z",
            "catalogueCommit": "abc1234",
            "catalogueVersion": "9.9.9",
            "entries": [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": "a" * 64,
                    "fingerprintRevisions": [{"contentFingerprint": "a" * 64, "catalogueVersion": "8.25.0"}],
                    "firstSeenVersion": "8.25.0",
                }
            ],
        }
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: set())
        doc = id_ledger.build_ledger_document(previous=previous)
        assert doc["generatedAt"] != "2026-09-01T00:00:00Z"
        assert len(doc["entries"][0]["fingerprintRevisions"]) == 2

    def test_main_writes_then_check_passes(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        _write_ledger(
            fake_repo,
            [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": "a" * 64,
                    "firstSeenVersion": "8.25.0",
                }
            ],
        )
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: set())
        assert gen_id_ledger.main([]) == 0
        assert "Wrote" in capsys.readouterr().out
        assert gen_id_ledger.main(["--check"]) == 0
        assert "PASS: id-ledger OK" in capsys.readouterr().out

    def test_main_check_fails_when_ledger_missing(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        monkeypatch.chdir(fake_repo)
        monkeypatch.setattr(gen_id_ledger, "load_baseline_payloads", lambda: {})
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: set())
        assert gen_id_ledger.main(["--check"]) == 1
        assert "missing" in capsys.readouterr().err

    def test_main_check_fails_when_catalogue_changed(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        _write_ledger(
            fake_repo,
            [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": id_ledger.content_fingerprint(
                        {"title": "Test UC", "spl": "index=x"}
                    ),
                    "firstSeenVersion": "8.25.0",
                }
            ],
        )
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: set())
        _write_uc(cat, "1.1.1", title="Renamed")
        assert gen_id_ledger.main(["--check"]) == 1
        assert "stale" in capsys.readouterr().err

    def test_main_reseed_fails_when_baseline_tag_is_absent(
        self, fake_repo: pathlib.Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        assert gen_id_ledger.main(["--reseed"]) == 1
        assert "cannot read" in capsys.readouterr().err

    def test_main_refuses_to_shorten_revision_history(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cat = _make_cat(fake_repo, 1)
        _write_uc(cat, "1.1.1")
        _write_ledger(
            fake_repo,
            [
                {
                    "id": "1.1.1",
                    "status": "active",
                    "contentFingerprint": "b" * 64,
                    "firstSeenVersion": "8.25.0",
                }
            ],
        )
        monkeypatch.setattr(id_ledger, "discover_removed_ids", lambda _catalogue: set())
        monkeypatch.setattr(
            gen_id_ledger,
            "validate_ledger_revision_monotonicity",
            lambda _previous, _generated: ["1.1.1 lost a revision"],
        )
        before = (fake_repo / "data" / "id-ledger.json").read_text(encoding="utf-8")
        assert gen_id_ledger.main(["--check"]) == 1
        assert "shortened" in capsys.readouterr().err
        assert gen_id_ledger.main([]) == 1
        assert "shortened" in capsys.readouterr().err
        assert (fake_repo / "data" / "id-ledger.json").read_text(encoding="utf-8") == before


class TestMigrationBlastGuard:
    def test_manifest_change_key_round_trip(self) -> None:
        change = uc_id_migration_blast.IdentifierChange("remap", "1.1.1", "2.2.2")
        manifest = {
            "changes": [
                {
                    "kind": "remap",
                    "from": "1.1.1",
                    "to": "2.2.2",
                    "identityPreserved": True,
                }
            ]
        }
        keys = uc_id_migration_blast.manifest_change_keys(manifest)
        assert uc_id_migration_blast.change_key(change) in keys

    def test_bulk_without_manifest_fails(self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        changes = [
            uc_id_migration_blast.IdentifierChange("remap", f"1.1.{i}", f"2.2.{i}")
            for i in range(1, 15)
        ]
        monkeypatch.setattr(uc_id_migration_blast, "resolve_base_ref", lambda _x: "base")
        monkeypatch.setattr(uc_id_migration_blast, "detect_identifier_changes", lambda _b: changes)
        monkeypatch.setattr(uc_id_migration_blast, "migration_files_in_diff", lambda _b: [])
        assert uc_id_migration_blast.main(["--check"]) == 1

    def test_bulk_with_manifest_passes(self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        changes = [
            uc_id_migration_blast.IdentifierChange("remap", f"1.1.{i}", f"2.2.{i}")
            for i in range(1, 15)
        ]
        manifest_path = fake_repo / "data" / "uc-id-migrations" / "bulk.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schemaVersion": "1.0.0",
                    "description": "test bulk remap",
                    "changes": [
                        {
                            "kind": "remap",
                            "from": c.from_id,
                            "to": c.to_id,
                            "identityPreserved": True,
                        }
                        for c in changes
                    ],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(uc_id_migration_blast, "resolve_base_ref", lambda _x: "base")
        monkeypatch.setattr(uc_id_migration_blast, "detect_identifier_changes", lambda _b: changes)
        monkeypatch.setattr(
            uc_id_migration_blast, "migration_files_in_diff", lambda _b: [manifest_path]
        )
        assert uc_id_migration_blast.main(["--check"]) == 0

    def test_fingerprint_churn_counts_toward_threshold(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        changes = [
            uc_id_migration_blast.IdentifierChange("fingerprint_change", f"25.59.{i}", f"25.59.{i}")
            for i in range(1, 15)
        ]
        monkeypatch.setattr(uc_id_migration_blast, "resolve_base_ref", lambda _x: "base")
        monkeypatch.setattr(uc_id_migration_blast, "detect_identifier_changes", lambda _b: changes)
        monkeypatch.setattr(uc_id_migration_blast, "migration_files_in_diff", lambda _b: [])
        assert uc_id_migration_blast.main(["--check"]) == 1

    def test_fingerprint_churn_manifest_key(self) -> None:
        change = uc_id_migration_blast.IdentifierChange("fingerprint_change", "25.59.1", "25.59.1")
        manifest = {
            "changes": [
                {
                    "kind": "fingerprint_change",
                    "from": "25.59.1",
                    "to": "25.59.1",
                    "identityPreserved": False,
                }
            ]
        }
        keys = uc_id_migration_blast.manifest_change_keys(manifest)
        assert uc_id_migration_blast.change_key(change) in keys

    def test_bulk_fingerprint_manifest_covers_many_ids(
        self, fake_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        changes = [
            uc_id_migration_blast.IdentifierChange("fingerprint_change", f"3.1.{i}", f"3.1.{i}")
            for i in range(1, 24)
        ]
        manifest_path = fake_repo / "data" / "uc-id-migrations" / "spl-refresh.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "schemaVersion": "1.0.0",
                    "description": "Bulk SPL refresh across cluster monitoring UCs",
                    "changes": [
                        {
                            "kind": "bulk_fingerprint_change",
                            "identifiers": [f"3.1.{i}" for i in range(1, 24)],
                            "identityPreserved": True,
                            "reason": "Replace deprecated stats syntax; monitoring intent unchanged",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(uc_id_migration_blast, "resolve_base_ref", lambda _x: "base")
        monkeypatch.setattr(uc_id_migration_blast, "detect_identifier_changes", lambda _b: changes)
        monkeypatch.setattr(
            uc_id_migration_blast, "migration_files_in_diff", lambda _b: [manifest_path]
        )
        assert uc_id_migration_blast.main(["--check"]) == 0
