"""Hermetic tests for ``scripts/stamp_ledger_release.py``.

The script transmutes ``data/provenance/mapping-ledger.json`` (the
in-repo, ``signature.state="unsigned"`` artefact) into
``dist/mapping-ledger.json`` with ``signature.state="attested"`` and
emits a markdown manifest alongside. It runs inside the
``release.yml`` workflow immediately before
``actions/attest-build-provenance@v2``.

Tests are fully hermetic: every test monkeypatches the four
module-level path constants (``ROOT``, ``LEDGER_SRC``, ``DIST_DIR``,
``LEDGER_DST``, ``MANIFEST_DST``) to ``tmp_path``-rooted equivalents,
and stubs every ``GITHUB_*`` env var directly. No network, no
mutation of the real ``data/provenance/`` or ``dist/`` directories.

Coverage target: 100% of ``scripts/stamp_ledger_release.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import stamp_ledger_release as M  # noqa: E402


# -----------------------------------------------------------------------------
# Fixture helpers
# -----------------------------------------------------------------------------


def _seed_ledger(
    base: Path,
    *,
    state: str = "unsigned",
    entry_count: int = 3,
    merkle: str = "a" * 64,
    catalogue_commit: str = "abc1234",
    entries: list[dict[str, Any]] | None = None,
) -> Path:
    """Write a minimal, schema-shaped mapping-ledger.json under
    ``base/data/provenance/`` and return its path."""
    if entries is None:
        # 3 entries with mixed sign-off shapes; covers _recount branches.
        entries = [
            {
                "signoffStatus": {
                    "peer": {"status": "signed"},
                    "legal": {"status": "signed"},
                    "sme": {"status": "signed"},
                },
            },
            {
                "signoffStatus": {
                    "peer": {"status": "pending"},
                    "legal": {"status": "pending"},
                    "sme": {"status": "pending"},
                },
            },
            {
                "signoffStatus": {
                    "peer": {"status": "not-required"},
                    "legal": {"status": "not-required"},
                    "sme": {"status": "grandfathered"},
                },
            },
        ]
    src = base / "data" / "provenance" / "mapping-ledger.json"
    src.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "entryCount": entry_count,
        "merkleRoot": merkle,
        "catalogueCommit": catalogue_commit,
        "entries": entries,
        "signature": {"state": state},
    }
    src.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return src


def _patch_paths(
    monkeypatch: pytest.MonkeyPatch,
    base: Path,
    *,
    create_dist: bool = False,
) -> tuple[Path, Path, Path]:
    """Redirect the four module-level path constants under ``base``.

    ``create_dist=True`` pre-creates ``dist/`` for tests that exercise
    ``write_manifest`` in isolation (which does NOT mkdir its parent).
    ``stamp_ledger`` creates ``dist/`` itself, so its tests pass
    ``create_dist=False`` to also exercise the mkdir branch."""
    src = base / "data" / "provenance" / "mapping-ledger.json"
    dist_dir = base / "dist"
    ledger_dst = dist_dir / "mapping-ledger.json"
    manifest_dst = dist_dir / "mapping-ledger.manifest.md"
    monkeypatch.setattr(M, "ROOT", base)
    monkeypatch.setattr(M, "LEDGER_SRC", src)
    monkeypatch.setattr(M, "DIST_DIR", dist_dir)
    monkeypatch.setattr(M, "LEDGER_DST", ledger_dst)
    monkeypatch.setattr(M, "MANIFEST_DST", manifest_dst)
    if create_dist:
        dist_dir.mkdir(parents=True, exist_ok=True)
    return src, ledger_dst, manifest_dst


def _seed_env(monkeypatch: pytest.MonkeyPatch, **overrides: str) -> None:
    """Set GITHUB_* env vars for non-dry-run runs. Defaults are valid."""
    defaults = {
        "GITHUB_SERVER_URL": "https://github.com",
        "GITHUB_REPOSITORY": "owner/repo",
        "GITHUB_RUN_ID": "12345",
        "GITHUB_SHA": "0123456789abcdef0123456789abcdef01234567",
        "GITHUB_REF_NAME": "v1.2.3",
        "GITHUB_WORKFLOW_REF": ".github/workflows/release.yml@refs/tags/v1.2.3",
    }
    defaults.update(overrides)
    for k, v in defaults.items():
        monkeypatch.setenv(k, v)
    # RELEASE_VERSION is optional; ensure it's not leaking from outer env.
    if "RELEASE_VERSION" not in overrides:
        monkeypatch.delenv("RELEASE_VERSION", raising=False)


# -----------------------------------------------------------------------------
# _env
# -----------------------------------------------------------------------------


class TestEnv:
    def test_returns_value_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("FOO", "bar")
        assert M._env("FOO") == "bar"

    def test_returns_default_when_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("FOO", raising=False)
        assert M._env("FOO", default="fallback") == "fallback"

    def test_uses_set_value_over_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("FOO", "bar")
        assert M._env("FOO", default="other") == "bar"

    def test_raises_when_unset_and_no_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("FOO", raising=False)
        with pytest.raises(KeyError, match="FOO"):
            M._env("FOO")


# -----------------------------------------------------------------------------
# resolve_release_metadata
# -----------------------------------------------------------------------------


class TestResolveReleaseMetadata:
    def test_dry_run_returns_placeholders(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Strip every GITHUB_* var to prove dry_run doesn't read them.
        for k in (
            "GITHUB_SERVER_URL",
            "GITHUB_REPOSITORY",
            "GITHUB_RUN_ID",
            "GITHUB_SHA",
            "GITHUB_REF_NAME",
            "GITHUB_WORKFLOW_REF",
            "RELEASE_VERSION",
        ):
            monkeypatch.delenv(k, raising=False)
        md = M.resolve_release_metadata(dry_run=True)
        assert md["serverUrl"] == "https://github.com"
        assert md["repository"] == "fenre/splunk-monitoring-use-cases"
        assert md["runId"] == "0"
        assert md["sha"] == "0" * 40
        assert md["refName"] == "v0.0.0-dryrun"
        assert md["releaseVersion"] == "0.0.0-dryrun"
        # workflowRef has its own default
        assert "release.yml" in md["workflowRef"]

    def test_real_run_uses_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _seed_env(monkeypatch)
        md = M.resolve_release_metadata(dry_run=False)
        assert md["serverUrl"] == "https://github.com"
        assert md["repository"] == "owner/repo"
        assert md["runId"] == "12345"
        assert md["sha"] == "0123456789abcdef0123456789abcdef01234567"
        assert md["refName"] == "v1.2.3"
        # releaseVersion derives from GITHUB_REF_NAME with leading 'v' stripped
        assert md["releaseVersion"] == "1.2.3"

    def test_real_run_release_version_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``RELEASE_VERSION`` env var wins over ``GITHUB_REF_NAME`` if set."""
        _seed_env(monkeypatch)
        monkeypatch.setenv("RELEASE_VERSION", "5.0.0-rc1")
        md = M.resolve_release_metadata(dry_run=False)
        assert md["releaseVersion"] == "5.0.0-rc1"

    def test_real_run_sha_lowercased(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_env(
            monkeypatch,
            GITHUB_SHA="ABCDEF0123456789ABCDEF0123456789ABCDEF01",
        )
        md = M.resolve_release_metadata(dry_run=False)
        assert md["sha"] == "abcdef0123456789abcdef0123456789abcdef01"

    def test_raises_when_run_id_not_numeric(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_env(monkeypatch, GITHUB_RUN_ID="not-a-number")
        with pytest.raises(ValueError, match="GITHUB_RUN_ID must be numeric"):
            M.resolve_release_metadata(dry_run=False)

    def test_raises_when_sha_too_short(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_env(monkeypatch, GITHUB_SHA="abc")
        with pytest.raises(ValueError, match="GITHUB_SHA must be a hex SHA"):
            M.resolve_release_metadata(dry_run=False)

    def test_raises_when_sha_contains_non_hex(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _seed_env(
            monkeypatch,
            GITHUB_SHA="zzz" + "0" * 37,  # 40 chars, but 'z' is not hex
        )
        with pytest.raises(ValueError, match="GITHUB_SHA must be a hex SHA"):
            M.resolve_release_metadata(dry_run=False)

    def test_workflow_ref_has_default_when_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GITHUB_WORKFLOW_REF has a default; pin the fallback path."""
        _seed_env(monkeypatch)
        monkeypatch.delenv("GITHUB_WORKFLOW_REF", raising=False)
        md = M.resolve_release_metadata(dry_run=False)
        assert md["workflowRef"].endswith("release.yml@refs/heads/main")

    def test_short_sha_is_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """7 chars of hex is the minimum acceptable SHA length."""
        _seed_env(monkeypatch, GITHUB_SHA="abc1234")
        md = M.resolve_release_metadata(dry_run=False)
        assert md["sha"] == "abc1234"


# -----------------------------------------------------------------------------
# build_signature_block
# -----------------------------------------------------------------------------


class TestBuildSignatureBlock:
    def _md(self) -> dict[str, str]:
        return {
            "serverUrl": "https://github.com",
            "repository": "owner/repo",
            "runId": "42",
            "sha": "abc1234567890abc1234567890abc1234567890a",
            "refName": "v1.0.0",
            "workflowRef": ".github/workflows/release.yml@refs/tags/v1.0.0",
            "releaseVersion": "1.0.0",
        }

    def test_uses_catalogue_commit_when_present(self) -> None:
        sig = M.build_signature_block(
            ledger={"catalogueCommit": "deadbee"}, md=self._md()
        )
        assert sig["state"] == "attested"
        assert sig["commit"] == "deadbee"
        assert sig["runId"] == "42"
        assert sig["bundlePath"] == M.BUNDLE_FILENAME
        assert sig["signatureAlgorithm"] == M.SIGSTORE_ALGORITHM
        # signedAt is RFC3339 UTC with trailing Z
        assert sig["signedAt"].endswith("Z")
        assert "T" in sig["signedAt"]
        # attestation URL embeds run id
        assert sig["attestationUrl"] == (
            "https://github.com/owner/repo/attestations/42"
        )
        # signer is the workflow repo path
        assert sig["signer"] == (
            "https://github.com/owner/repo/.github/workflows/release.yml"
        )

    def test_falls_back_to_first_7_of_sha_when_catalogue_commit_missing(
        self,
    ) -> None:
        """``if not catalogue_commit:`` — pin the fallback path used when
        the in-repo ledger doesn't yet carry a catalogueCommit field."""
        sig = M.build_signature_block(ledger={}, md=self._md())
        assert sig["commit"] == "abc1234"  # first 7 chars of sha

    def test_falls_back_when_catalogue_commit_is_empty_string(self) -> None:
        sig = M.build_signature_block(
            ledger={"catalogueCommit": ""}, md=self._md()
        )
        assert sig["commit"] == "abc1234"

    def test_signed_at_is_microsecond_zero(self) -> None:
        """``.replace(microsecond=0)`` is intentional — the signedAt
        must be stable to second-precision so identical re-runs in the
        same second produce byte-identical ledgers (modulo seconds)."""
        sig = M.build_signature_block(ledger={}, md=self._md())
        # No fractional seconds should appear before the trailing Z.
        # Format is YYYY-MM-DDTHH:MM:SSZ (no microseconds).
        # ``.000`` or ``.123`` would mean microsecond wasn't zeroed.
        assert "." not in sig["signedAt"]


# -----------------------------------------------------------------------------
# _recount
# -----------------------------------------------------------------------------


class TestRecount:
    def test_aggregates_three_states(self) -> None:
        ledger = {
            "entries": [
                {"signoffStatus": {"peer": {"status": "signed"}}},
                {"signoffStatus": {"peer": {"status": "signed"}}},
                {"signoffStatus": {"peer": {"status": "pending"}}},
                {"signoffStatus": {"peer": {"status": "not-required"}}},
                {"signoffStatus": {"peer": {"status": "grandfathered"}}},
            ]
        }
        signed, pending, nr = M._recount(ledger, "peer")
        assert signed == 2
        assert pending == 1
        assert nr == 2  # not-required + grandfathered both fall into the else branch

    def test_handles_missing_kind(self) -> None:
        """Pin the ``.get(kind, {}).get("status")`` fallback for entries
        that don't carry the requested review kind."""
        ledger = {"entries": [{"signoffStatus": {"peer": {"status": "signed"}}}]}
        signed, pending, nr = M._recount(ledger, "legal")
        # All entries fall into the ``else: nr += 1`` branch when status is None.
        assert signed == 0
        assert pending == 0
        assert nr == 1

    def test_handles_missing_signoff_status(self) -> None:
        ledger = {"entries": [{"id": "x"}]}  # no signoffStatus at all
        signed, pending, nr = M._recount(ledger, "peer")
        assert (signed, pending, nr) == (0, 0, 1)

    def test_handles_missing_entries_key(self) -> None:
        """``ledger.get("entries", [])`` — pin the empty-default path."""
        signed, pending, nr = M._recount({}, "peer")
        assert (signed, pending, nr) == (0, 0, 0)

    def test_handles_empty_entries(self) -> None:
        signed, pending, nr = M._recount({"entries": []}, "peer")
        assert (signed, pending, nr) == (0, 0, 0)


# -----------------------------------------------------------------------------
# stamp_ledger
# -----------------------------------------------------------------------------


class TestStampLedger:
    def test_writes_dist_files_and_promotes_state(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_ledger(tmp_path)
        src, ledger_dst, manifest_dst = _patch_paths(monkeypatch, tmp_path)
        ledger = M.stamp_ledger(dry_run=True)

        # In-memory: signature was promoted
        assert ledger["signature"]["state"] == "attested"
        # On disk: ledger and manifest were written
        assert ledger_dst.exists()
        assert manifest_dst.exists()
        # On disk: written ledger is structurally consistent
        on_disk = json.loads(ledger_dst.read_text(encoding="utf-8"))
        assert on_disk["signature"]["state"] == "attested"
        assert on_disk["entryCount"] == 3
        # File ends with newline (idempotent diff hygiene)
        assert ledger_dst.read_text(encoding="utf-8").endswith("\n")

    def test_exits_when_source_ledger_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _patch_paths(monkeypatch, tmp_path)  # no _seed_ledger
        with pytest.raises(SystemExit) as exc:
            M.stamp_ledger(dry_run=True)
        assert exc.value.code == 1
        assert "FATAL: source ledger not found" in capsys.readouterr().err

    def test_exits_when_already_attested(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Re-stamping an already-attested ledger would re-sign someone
        else's artefact — pin the fatal-misuse guard."""
        _seed_ledger(tmp_path, state="attested")
        _patch_paths(monkeypatch, tmp_path)
        with pytest.raises(SystemExit) as exc:
            M.stamp_ledger(dry_run=True)
        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "FATAL" in err
        assert "'attested'" in err

    def test_exits_when_state_is_arbitrary_other(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Any state other than ``unsigned`` is rejected — including
        future schema additions like ``revoked`` or ``superseded``."""
        _seed_ledger(tmp_path, state="revoked")
        _patch_paths(monkeypatch, tmp_path)
        with pytest.raises(SystemExit) as exc:
            M.stamp_ledger(dry_run=True)
        assert exc.value.code == 1

    def test_exits_when_signature_block_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """If signature block is absent entirely, ``state`` is None
        which is not ``unsigned`` → guard fires."""
        src, _, _ = _patch_paths(monkeypatch, tmp_path)
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_text(
            json.dumps(
                {
                    "entryCount": 0,
                    "merkleRoot": "x" * 64,
                    "catalogueCommit": "deadbee",
                    "entries": [],
                    # NO signature key
                }
            ),
            encoding="utf-8",
        )
        with pytest.raises(SystemExit) as exc:
            M.stamp_ledger(dry_run=True)
        assert exc.value.code == 1

    def test_creates_dist_dir_if_absent(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_ledger(tmp_path)
        _, ledger_dst, _ = _patch_paths(monkeypatch, tmp_path)
        # dist/ does not exist yet at this point
        assert not (tmp_path / "dist").exists()
        M.stamp_ledger(dry_run=True)
        assert (tmp_path / "dist").is_dir()
        assert ledger_dst.exists()


# -----------------------------------------------------------------------------
# write_manifest
# -----------------------------------------------------------------------------


class TestWriteManifest:
    def _md(self) -> dict[str, str]:
        return {
            "serverUrl": "https://github.com",
            "repository": "owner/repo",
            "runId": "42",
            "sha": "abc1234567890abc1234567890abc1234567890a",
            "refName": "v1.0.0",
            "workflowRef": ".github/workflows/release.yml@refs/tags/v1.0.0",
            "releaseVersion": "1.0.0",
        }

    def test_normal_run_has_no_dry_banner(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, _, manifest_dst = _patch_paths(monkeypatch, tmp_path, create_dist=True)
        ledger = {
            "entryCount": 5,
            "merkleRoot": "f" * 64,
            "entries": [
                {"signoffStatus": {"peer": {"status": "signed"}}},
            ],
        }
        M.write_manifest(ledger, '{"x":1}', self._md(), dry_run=False)
        body = manifest_dst.read_text(encoding="utf-8")
        assert "DRY-RUN BUILD" not in body
        assert "v1.0.0" in body
        assert "owner/repo" in body
        assert "5" in body  # entry count

    def test_dry_run_emits_banner(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, _, manifest_dst = _patch_paths(monkeypatch, tmp_path, create_dist=True)
        ledger = {
            "entryCount": 1,
            "merkleRoot": "0" * 64,
            "entries": [],
        }
        M.write_manifest(ledger, '{}', self._md(), dry_run=True)
        body = manifest_dst.read_text(encoding="utf-8")
        assert "DRY-RUN BUILD" in body

    def test_manifest_includes_sha256_of_rendered(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The manifest fingerprint must match SHA-256 of the bytes
        actions/attest-build-provenance will sign — pin the contract."""
        import hashlib

        _, _, manifest_dst = _patch_paths(monkeypatch, tmp_path, create_dist=True)
        rendered = '{"x":1}'
        expected = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        M.write_manifest(
            ledger={"entryCount": 0, "merkleRoot": "", "entries": []},
            rendered=rendered,
            md=self._md(),
            dry_run=False,
        )
        body = manifest_dst.read_text(encoding="utf-8")
        assert expected in body

    def test_manifest_includes_signoff_aggregates(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, _, manifest_dst = _patch_paths(monkeypatch, tmp_path, create_dist=True)
        ledger = {
            "entryCount": 3,
            "merkleRoot": "x" * 64,
            "entries": [
                {
                    "signoffStatus": {
                        "peer": {"status": "signed"},
                        "legal": {"status": "pending"},
                        "sme": {"status": "not-required"},
                    }
                }
            ],
        }
        M.write_manifest(ledger, '{}', self._md(), dry_run=False)
        body = manifest_dst.read_text(encoding="utf-8")
        # Per-review aggregates section is present
        assert "## Sign-off aggregates" in body
        # peer signed=1
        assert "| peer | 1 | 0 | 0 |" in body
        # legal pending=1
        assert "| legal | 0 | 1 | 0 |" in body
        # SME not-required → falls into nr column
        assert "| SME | 0 | 0 | 1 |" in body

    def test_manifest_includes_verification_block(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _, _, manifest_dst = _patch_paths(monkeypatch, tmp_path, create_dist=True)
        M.write_manifest(
            ledger={"entryCount": 0, "merkleRoot": "f" * 64, "entries": []},
            rendered="{}",
            md=self._md(),
            dry_run=False,
        )
        body = manifest_dst.read_text(encoding="utf-8")
        # Operator-facing verification recipe is present
        assert "gh attestation verify" in body
        assert "audit-mapping-ledger" in body
        # Owner is extracted from "owner/repo" split
        assert "--owner owner" in body
        # Bundle filename matches the module constant
        assert M.BUNDLE_FILENAME in body


# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------


class TestMain:
    def test_dry_run_succeeds_and_prints_summary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _seed_ledger(tmp_path)
        src, ledger_dst, manifest_dst = _patch_paths(monkeypatch, tmp_path)
        rc = M.main(["--dry-run"])
        assert rc == 0
        out = capsys.readouterr().out
        # Print includes both filenames
        assert "mapping-ledger.json" in out
        assert "manifest" in out
        # Mentions the merkle root prefix
        assert "merkle root" in out
        # Mentions next-step actions
        assert "actions/attest-build-provenance" in out
        # Files on disk
        assert ledger_dst.exists()
        assert manifest_dst.exists()

    def test_real_run_uses_env(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _seed_ledger(tmp_path)
        _, ledger_dst, _ = _patch_paths(monkeypatch, tmp_path)
        _seed_env(monkeypatch)
        rc = M.main([])
        assert rc == 0
        on_disk = json.loads(ledger_dst.read_text(encoding="utf-8"))
        sig = on_disk["signature"]
        assert sig["state"] == "attested"
        # attestationUrl reflects env-derived run id
        assert sig["attestationUrl"].endswith("/attestations/12345")
        # signer reflects env-derived repository
        assert "owner/repo" in sig["signer"]

    def test_argparse_help_does_not_crash(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            M.main(["--help"])
        # argparse exits cleanly with code 0 on --help
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert "--dry-run" in out
        assert "release" in out.lower()

    def test_unknown_flag_exits_nonzero(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            M.main(["--bogus"])
        assert exc.value.code != 0


# -----------------------------------------------------------------------------
# Module entrypoint
# -----------------------------------------------------------------------------
#
# NOTE: ``stamp_ledger_release.py`` ends with::
#
#     if __name__ == "__main__":
#         sys.exit(main(sys.argv[1:]))
#
# Covering this 2-line tail with ``runpy`` would require seeding the real
# ``data/provenance/mapping-ledger.json`` (or letting the script crash
# on it) plus stubbing the ROOT path in a subprocess context — pure
# boilerplate that doesn't exercise application logic. Documented as
# intentionally omitted, mirroring our pattern in test_audit_doc_regulations.py.
