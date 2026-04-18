#!/usr/bin/env python3
"""
Phase 5.4 — release-time ledger stamping.

Produces release artefacts from data/provenance/mapping-ledger.json:

    dist/mapping-ledger.json           Stamped copy with signature.state=attested,
                                       pointing at the GitHub attestation that
                                       release.yml will produce for this file.

    dist/mapping-ledger.manifest.md    Human-readable release manifest summarising
                                       merkle root, entry count, per-signoff state
                                       aggregates, and verification instructions.

The in-repo copy (data/provenance/mapping-ledger.json) remains with
signature.state="unsigned" so PR builds continue to validate deterministically
via scripts/audit_mapping_ledger.py. Only the release artefact carries the
attested envelope.

Why stamp *before* attestation?
    `actions/attest-build-provenance@v2` attests the file at the path you give
    it. If we mutated the file after attestation we'd invalidate the signature.
    So the pipeline is:

        1. regenerate ledger in-repo (signature.state=unsigned)     [generator]
        2. audit in-repo ledger                                     [audit]
        3. copy to dist/ and stamp signature.state=attested         [THIS SCRIPT]
        4. `actions/attest-build-provenance@v2` on dist/mapping-ledger.json
        5. upload dist/mapping-ledger.json + the Sigstore bundle

    The stamped file is self-consistent: it names the attestationUrl it will
    receive (runId + repository), the workflow ref that produced it, and the
    commit — all of which are known from env before step 4 runs.

Environment contract (all from GitHub Actions):
    GITHUB_SERVER_URL       e.g. https://github.com
    GITHUB_REPOSITORY       owner/repo
    GITHUB_RUN_ID           numeric run id
    GITHUB_SHA              full 40-char commit SHA
    GITHUB_REF_NAME         tag name (e.g. v5.4.0)
    GITHUB_WORKFLOW_REF     e.g. .github/workflows/release.yml@refs/tags/v5.4.0
    RELEASE_VERSION         version string (without leading v); optional override

Outside GitHub Actions (local dry-run) the script substitutes placeholder
values and prints a big red warning; this mode is not suitable for publishing
a real release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
LEDGER_SRC = ROOT / "data" / "provenance" / "mapping-ledger.json"
DIST_DIR = ROOT / "dist"
LEDGER_DST = DIST_DIR / "mapping-ledger.json"
MANIFEST_DST = DIST_DIR / "mapping-ledger.manifest.md"

# The SignatureAlgorithm enum in schemas/mapping-ledger.schema.json.
SIGSTORE_ALGORITHM = "sigstore-cosign-bundle-v0.3"

# Filename that actions/attest-build-provenance writes into dist/ via
# --subject-path. The release workflow renames the attestation bundle to this
# path so the ledger's signature.bundlePath reference is self-consistent.
BUNDLE_FILENAME = "mapping-ledger.sigstore.bundle.json"


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise KeyError(f"Missing required env var {name!r}")
    return value


def resolve_release_metadata(
    dry_run: bool,
) -> dict[str, str]:
    """Gather the release inputs we need to populate signature.*."""
    defaults: dict[str, str] = {
        "serverUrl": "https://github.com",
        "repository": "fenre/splunk-monitoring-use-cases",
        "runId": "0",
        "sha": "0" * 40,
        "refName": "v0.0.0-dryrun",
        "workflowRef": ".github/workflows/release.yml@refs/heads/main",
        "releaseVersion": "0.0.0-dryrun",
    }
    if dry_run:
        md = dict(defaults)
    else:
        md = {
            "serverUrl": _env("GITHUB_SERVER_URL", defaults["serverUrl"]),
            "repository": _env("GITHUB_REPOSITORY", defaults["repository"]),
            "runId": _env("GITHUB_RUN_ID"),
            "sha": _env("GITHUB_SHA"),
            "refName": _env("GITHUB_REF_NAME"),
            "workflowRef": _env("GITHUB_WORKFLOW_REF", defaults["workflowRef"]),
            "releaseVersion": os.environ.get(
                "RELEASE_VERSION",
                os.environ.get("GITHUB_REF_NAME", defaults["releaseVersion"]).lstrip("v"),
            ),
        }
    if not md["runId"].isdigit():
        raise ValueError(f"GITHUB_RUN_ID must be numeric, got {md['runId']!r}")
    if len(md["sha"]) < 7 or not all(c in "0123456789abcdef" for c in md["sha"].lower()):
        raise ValueError(f"GITHUB_SHA must be a hex SHA, got {md['sha']!r}")
    md["sha"] = md["sha"].lower()
    return md


def build_signature_block(
    ledger: dict[str, Any],
    md: dict[str, str],
) -> dict[str, Any]:
    """Return the signature object that replaces the in-repo 'unsigned' block."""
    catalogue_commit = ledger.get("catalogueCommit", "")
    # schemas/mapping-ledger.schema.json requires signature.commit == catalogueCommit.
    # Use the short-SHA that the generator wrote, or fall back to the first 7 chars
    # of GITHUB_SHA when the catalogue copy was produced from an untracked state.
    if not catalogue_commit:
        catalogue_commit = md["sha"][:7]

    attestation_url = (
        f"{md['serverUrl']}/{md['repository']}/attestations/{md['runId']}"
    )
    signer = f"https://github.com/{md['repository']}/.github/workflows/release.yml"

    return {
        "state": "attested",
        "signedAt": datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "signer": signer,
        "signatureAlgorithm": SIGSTORE_ALGORITHM,
        "attestationUrl": attestation_url,
        "bundlePath": BUNDLE_FILENAME,
        "workflowRef": md["workflowRef"],
        "runId": md["runId"],
        "commit": catalogue_commit,
    }


def stamp_ledger(dry_run: bool) -> dict[str, Any]:
    if not LEDGER_SRC.exists():
        print(
            f"FATAL: source ledger not found at {LEDGER_SRC.relative_to(ROOT)}. "
            "Run scripts/generate_mapping_ledger.py before stamping.",
            file=sys.stderr,
        )
        sys.exit(1)

    ledger = json.loads(LEDGER_SRC.read_text(encoding="utf-8"))

    current_state = (ledger.get("signature") or {}).get("state")
    if current_state != "unsigned":
        # This is a fatal misuse: stamping an already-attested ledger would
        # re-sign someone else's artefact. Release automation must call us on
        # the pristine in-repo copy only.
        print(
            f"FATAL: in-repo ledger has signature.state={current_state!r}; "
            "release stamping requires 'unsigned'. Regenerate from source "
            "before retrying.",
            file=sys.stderr,
        )
        sys.exit(1)

    md = resolve_release_metadata(dry_run)
    ledger["signature"] = build_signature_block(ledger, md)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(ledger, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    LEDGER_DST.write_text(rendered, encoding="utf-8")

    write_manifest(ledger, rendered, md, dry_run)
    return ledger


def write_manifest(
    ledger: dict[str, Any],
    rendered: str,
    md: dict[str, str],
    dry_run: bool,
) -> None:
    """Emit a human-readable manifest alongside the stamped ledger."""
    sha256 = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    entry_count = ledger.get("entryCount", 0)
    merkle = ledger.get("merkleRoot", "")

    # Aggregate per-review sign-off states. We emit (signed, pending,
    # not-required+grandfathered) as a compact audit-facing summary.
    peer_signed, peer_pending, peer_nr = _recount(ledger, "peer")
    legal_signed, legal_pending, legal_nr = _recount(ledger, "legal")
    sme_signed, sme_pending, sme_nr = _recount(ledger, "sme")

    dry_banner = ""
    if dry_run:
        dry_banner = (
            "> ⚠️  **DRY-RUN BUILD** — metadata below was produced outside of\n"
            "> GitHub Actions. This manifest is for local inspection only and\n"
            "> MUST NOT be published as a real release asset.\n\n"
        )

    body = (
        f"# Mapping-ledger release manifest — v{md['releaseVersion']}\n\n"
        f"{dry_banner}"
        f"| Field | Value |\n"
        f"|---|---|\n"
        f"| Release | `v{md['releaseVersion']}` |\n"
        f"| Commit | `{md['sha'][:7]}` |\n"
        f"| Workflow | `{md['workflowRef']}` |\n"
        f"| Run | [{md['runId']}]({md['serverUrl']}/{md['repository']}/actions/runs/{md['runId']}) |\n"
        f"| Entries | {entry_count:,} |\n"
        f"| Merkle root | `{merkle}` |\n"
        f"| Ledger SHA-256 | `{sha256}` |\n"
        f"| Signature algorithm | `{SIGSTORE_ALGORITHM}` |\n"
        f"| Bundle filename | `{BUNDLE_FILENAME}` |\n\n"
        f"## Sign-off aggregates\n\n"
        f"| Review | signed | pending | not-required |\n"
        f"|---|---:|---:|---:|\n"
        f"| peer | {peer_signed} | {peer_pending} | {peer_nr} |\n"
        f"| legal | {legal_signed} | {legal_pending} | {legal_nr} |\n"
        f"| SME | {sme_signed} | {sme_pending} | {sme_nr} |\n\n"
        f"## Verifying this ledger\n\n"
        f"```bash\n"
        f"# 1. Verify the signature over the ledger file\n"
        f"gh attestation verify mapping-ledger.json \\\n"
        f"  --owner {md['repository'].split('/', 1)[0]} \\\n"
        f"  --bundle {BUNDLE_FILENAME}\n\n"
        f"# 2. Re-derive the merkle root yourself\n"
        f"python3 scripts/audit_mapping_ledger.py --verify-signature\n"
        f"```\n\n"
        f"Expected output: `PASS: mapping ledger OK ({entry_count:,} entries, "
        f"merkle root {merkle[:16]}…, signature=attested)`.\n\n"
        f"See [docs/signed-provenance.md](../docs/signed-provenance.md) for the\n"
        f"full verification protocol and operator workflows.\n"
    )
    MANIFEST_DST.write_text(body, encoding="utf-8")


def _recount(ledger: dict[str, Any], kind: str) -> tuple[int, int, int]:
    signed = pending = nr = 0
    for entry in ledger.get("entries", []):
        status = entry.get("signoffStatus", {}).get(kind, {}).get("status")
        if status == "signed":
            signed += 1
        elif status == "pending":
            pending += 1
        else:
            nr += 1
    return signed, pending, nr


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Copy data/provenance/mapping-ledger.json to dist/ and promote "
            "signature.state from 'unsigned' to 'attested'."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Use placeholder release metadata instead of reading GitHub Actions "
            "env vars. Intended for local smoke tests; produces a manifest with "
            "a red DRY-RUN banner."
        ),
    )
    args = parser.parse_args(argv)

    ledger = stamp_ledger(dry_run=args.dry_run)
    merkle = ledger.get("merkleRoot", "")
    entry_count = ledger.get("entryCount", 0)
    print(
        f"Stamped {LEDGER_DST.relative_to(ROOT)}: "
        f"{entry_count:,} entries, merkle root {merkle[:16]}…, "
        f"signature.state=attested."
    )
    print(
        f"Manifest at {MANIFEST_DST.relative_to(ROOT)}. "
        f"Next step: actions/attest-build-provenance on {LEDGER_DST.relative_to(ROOT)}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
