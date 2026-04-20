# Signed provenance ledger (Phase 5.4)

> **Status:** required for any change to
> `data/provenance/mapping-ledger.json`, `schemas/mapping-ledger.schema.json`,
> `scripts/generate_mapping_ledger.py`, `scripts/audit_mapping_ledger.py`,
> `scripts/stamp_ledger_release.py`, or the ledger-signing steps in
> `.github/workflows/release.yml`.
>
> **Scope:** every clause-level compliance mapping declared across UC
> sidecars under `use-cases/cat-*/uc-*.json`. Currently 1,889 entries
> covering 15 regulation families.

This repository aspires to be the international gold standard for
compliance-monitoring use cases. Peer review (Phase 4.5a), legal review
(Phase 4.5b), SME review (Phase 5.2), and the regulatory change-watch
(Phase 5.3) give reviewers the signal. Phase 5.4 gives an **auditor the
artefact**: a cryptographically verifiable, content-addressable ledger
that records every `(UC, regulation, clause, mode, assurance)` tuple the
catalogue claims, who reviewed it, when it first appeared, and — at
release time — a detached GitHub/Sigstore attestation anchoring the
merkle root of the ledger to a specific commit and workflow run.

## 1. What the ledger proves (and does not prove)

**Proves**

1. **Integrity.** Every compliance mapping in the catalogue, as of
   `catalogueCommit`, is captured in the ledger with a SHA-256
   fingerprint. Mutating any of the six fields that enter the hash
   (`mappingId`, `ucId`, `regulationId`, `regulationVersion`, `clause`,
   `mode`, `assurance`, `derivationSource`) invalidates both the per-entry
   `canonicalHash` and the top-level `merkleRoot`. CI blocks the PR.
2. **Completeness.** The in-repo audit (`scripts/audit_mapping_ledger.py`)
   performs a forward+reverse referential check: every UC sidecar's
   `compliance[]` entry must be in the ledger, and every ledger entry
   must point at a live UC. Dropping a mapping without removing the
   corresponding sidecar line — or vice versa — is a CI-blocking error.
3. **Chain of custody.** Each entry records
   `firstSeenCommit` + `lastModifiedCommit` so auditors can walk the
   git history back to the approval PR, which in turn links to peer,
   legal, and SME signoff records.
4. **Origin and non-repudiation (release artefacts only).** Official
   tagged releases carry a Sigstore bundle produced by
   `actions/attest-build-provenance@v2` inside the
   `fenre/splunk-monitoring-use-cases` GitHub Actions environment.
   Verification with `gh attestation verify` proves the ledger was
   produced by the release workflow at that commit and was not altered
   after signing.

**Does _not_ prove**

- That the mapping is **legally correct.** Clause-citation correctness
  lives with legal review (`docs/legal-review-guide.md`). The ledger
  only asserts that the mapping was reviewed _and_ recorded, not that
  the reviewers were right.
- That the SPL **actually fires.** Detection correctness lives with
  peer review (`docs/peer-review-guide.md`) and SME review
  (`docs/sme-review-guide.md`). The ledger carries the review state
  as a snapshot; it does not re-derive it.
- That the upstream regulation **has not changed** since sign-off.
  That is the job of the regulatory change-watch
  (`docs/regulatory-change-watch.md`).
- That the ledger is **current.** `catalogueCommit` is advisory; CI
  enforces regeneration on every PR via `--check`, but a stale clone
  will happily audit its own stale copy.

The four mechanisms compose: peer + legal + SME establish the truth of a
mapping; change-watch establishes the truth of the underlying regulation;
the ledger establishes the truth of the record.

## 2. Components

| File                                               | Purpose                                                                                                                                                                                                                                                                                                    |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schemas/mapping-ledger.schema.json`               | JSON Schema (Draft 2020-12) that governs the ledger. Defines entry shape, canonicalisation contract, and the `oneOf` signature envelope (`unsigned` or `attested`).                                                                                                                                        |
| `data/provenance/mapping-ledger.json`              | The in-repo ledger. Always `signature.state = "unsigned"` on `main` (so PR CI is deterministic); the attested copy lives in `dist/` at release time.                                                                                                                                                       |
| `scripts/generate_mapping_ledger.py`               | Deterministic generator. Walks every `use-cases/cat-*/uc-*.json`, canonicalises regulation names against `data/regulations.json`, probes git history in a single bulk `git log` pass, snapshots peer/legal/SME signoffs, hashes each entry, and emits the sorted-leaf merkle root. `--check` mode diff-gates. |
| `scripts/audit_mapping_ledger.py`                  | Independent verifier. Re-reads the ledger, recomputes all `canonicalHash`es and the `merkleRoot`, validates against the schema, performs referential integrity against current sidecars, and — when `--verify-signature` is passed — shells out to `gh attestation verify` against the Sigstore bundle.    |
| `scripts/stamp_ledger_release.py`                  | Release-time stamper. Copies the in-repo ledger to `dist/mapping-ledger.json` and flips `signature.state` from `unsigned` to `attested` _before_ Sigstore attestation (because attestation binds the file-at-rest).                                                                                         |
| `.github/workflows/validate.yml`                   | Runs `--check` (regeneration drift) and the audit on every pull request. Uploads the ledger as part of the `qa-gates` artifact.                                                                                                                                                                             |
| `.github/workflows/release.yml`                    | Generates, audits, stamps, and attests the ledger on `v*.*.*` tags. Produces `dist/mapping-ledger.json`, `dist/mapping-ledger.sigstore.bundle.json`, and `dist/mapping-ledger.manifest.md` as release assets.                                                                                                 |

## 3. Record anatomy

Every entry follows the same shape. Abbreviated from a real entry:

```json
{
  "mappingId": "22.5.2::gdpr@2016/679::Art. 32::detects-violation-of::full",
  "ucId": "22.5.2",
  "regulationId": "gdpr",
  "regulationVersion": "2016/679",
  "clause": "Art. 32",
  "mode": "detects-violation-of",
  "assurance": "full",
  "firstSeenCommit": "a7c9f3d",
  "lastModifiedCommit": "217320f",
  "signoffStatus": {
    "peer": { "required": true, "status": "signed", "latestSignoffPr": "#142" },
    "legal": { "required": true, "status": "signed", "latestSignoffPr": "#148" },
    "sme": { "required": true, "status": "signed", "latestSignoffPr": "#151" }
  },
  "canonicalHash": "9b1e…c0a2"
}
```

Derivative entries (propagated by
`scripts/generate_phase3_3_derivatives.py`) additionally carry a
`derivationSource` block pointing at the parent regulation, version,
and clause. The derivationSource participates in the hash — mutating
the parent pointer is a different ledger entry.

### 3.1 What feeds the hash

Only the fields listed in `canonicalisation.fieldOrder` participate:

```
mappingId, ucId, regulationId, regulationVersion,
clause, mode, assurance, derivationSource
```

Everything else (`firstSeenCommit`, `lastModifiedCommit`, `signoffStatus`,
`canonicalHash` itself) is ledger-metadata. It is recomputable and must
not tempt an auditor into thinking the content-addressing stretches
across it.

### 3.2 Regulation-name canonicalisation

UC sidecars use human-readable names (`"GDPR"`, `"EU GDPR"`, `"General
Data Protection Regulation"`). The ledger stores the stable
`regulations.json` slug (`gdpr`). Mapping table and precedence rules
live in `scripts/generate_mapping_ledger.py::NAME_TABLE`. Adding a new
regulation family requires:

1. An entry in `data/regulations.json frameworks[]`.
2. A row in `NAME_TABLE` covering every spelling the sidecar authors
   use (the generator refuses to emit an entry for an unknown name).
3. Regenerating the ledger (`python3 scripts/generate_mapping_ledger.py`)
   in the same PR.

## 4. Canonicalisation and merkle root

### 4.1 Canonical JSON

Per-entry hashing uses **RFC 8785 JSON Canonicalization Scheme** with
the compatible subset the Python standard library supports natively:

- UTF-8, NFC-normalised source strings (sidecars are stored that way).
- Sorted keys, no whitespace, no trailing newline.
- `ensure_ascii=False` so accented regulation names and `§` do not
  sneak in as `\u` escapes (which would break byte-for-byte matching
  across locales).

### 4.2 Leaf hash

For each ledger entry, the generator builds a small dict containing
only the fields in `canonicalisation.fieldOrder`, serialises with
`json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`,
UTF-8-encodes, and hashes with `hashlib.sha256`. That is the
`canonicalHash` field.

### 4.3 Merkle root

The merkle root is a **sorted-leaf rolling hash**, not a binary
Merkle tree. The generator:

1. Sorts entries lexicographically by `mappingId`.
2. Concatenates the hex `canonicalHash` of each entry into a single
   UTF-8 string (no separators).
3. SHA-256s the result.

This trades tree-depth proofs (a standard Merkle tree gives `O(log n)`
membership proofs) for a simpler, recomputable root that every
third-party auditor can re-derive in four lines of Python. Membership
for any individual entry is still a single constant-time lookup by
`mappingId`.

### 4.4 Independent recomputation

Anyone can independently verify the merkle root with no project code:

```python
import hashlib, json
led = json.load(open("data/provenance/mapping-ledger.json"))
leaves = sorted(e["canonicalHash"] for e in led["entries"])
root = hashlib.sha256("".join(leaves).encode("utf-8")).hexdigest()
assert root == led["merkleRoot"]
```

The per-entry hash is similarly recomputable; see `scripts/audit_mapping_ledger.py::canonical_hash_of` for the reference
implementation.

## 5. Signature envelope

The ledger schema defines a `oneOf` between two shapes. The shape in
use is always explicit via `signature.state`.

### 5.1 `unsigned` (development and PR CI)

```json
{
  "state": "unsigned",
  "reason": "development iteration; release workflow promotes to attested"
}
```

This is the only state that appears in `main`. It is what PR CI audits
against. `signature.state == "unsigned"` is valid; the audit only fails
when the caller passes `--require-signature` (which release automation
uses).

### 5.2 `attested` (release artefacts)

```json
{
  "state": "attested",
  "signedAt": "2026-04-16T12:34:56Z",
  "signer": "https://github.com/fenre/splunk-monitoring-use-cases/.github/workflows/release.yml",
  "signatureAlgorithm": "sigstore-cosign-bundle-v0.3",
  "attestationUrl": "https://github.com/fenre/splunk-monitoring-use-cases/attestations/12345678",
  "bundlePath": "mapping-ledger.sigstore.bundle.json",
  "workflowRef": ".github/workflows/release.yml@refs/tags/v5.4.0",
  "runId": "12345678",
  "commit": "217320f"
}
```

`commit` **must equal** the top-level `catalogueCommit` — the audit
rejects mismatches as tampering.

## 6. Release attestation workflow

The release workflow
(`.github/workflows/release.yml`) performs five steps, in order:

1. **Regenerate** the ledger at HEAD: `python3 scripts/generate_mapping_ledger.py --check`.
2. **Audit** the in-repo (`unsigned`) ledger: `python3 scripts/audit_mapping_ledger.py`.
3. **Stamp** a release copy into `dist/`:
   `python3 scripts/stamp_ledger_release.py`. This copies
   `data/provenance/mapping-ledger.json` to `dist/mapping-ledger.json`
   and replaces the signature block with the `attested` shape —
   populating `attestationUrl`, `bundlePath`, `workflowRef`, `runId`,
   and `commit` from the GitHub Actions environment. The in-repo file
   is **not** mutated.
4. **Attest** via `actions/attest-build-provenance@v2` with
   `subject-path: dist/mapping-ledger.json`. This produces a Sigstore
   bundle signed by a Fulcio-issued OIDC identity certificate for the
   workflow.
5. **Verify end-to-end.** The workflow temporarily swaps the stamped
   copy over the audit source and runs
   `scripts/audit_mapping_ledger.py --require-signature --verify-signature`.
   This exercises the same verification path a downstream consumer
   would use; if it fails, the release is aborted.

Why stamp _before_ attestation? `actions/attest-build-provenance@v2`
attests the file at the path you give it. Mutating the file after
attestation would invalidate the signature. So the pipeline is
generator → auditor → stamper → attester, never the other way around.

Outputs published as release assets:

- `mapping-ledger.json` — the stamped, `attested`-state ledger.
- `mapping-ledger.sigstore.bundle.json` — the Sigstore bundle produced
  by `actions/attest-build-provenance@v2`, renamed to the canonical
  path the ledger's `signature.bundlePath` points at.
- `mapping-ledger.manifest.md` — human-readable release manifest with
  merkle root, entry count, per-review signoff aggregates, and the
  verification one-liner reproduced below.

## 7. Verification protocol

There are three flavours of verification, in order of increasing
trust:

### 7.1 Trust-but-verify: the hash chain (no network, no tools beyond Python)

```bash
python3 scripts/audit_mapping_ledger.py
```

Exit code 0 means:

- The ledger validates against `schemas/mapping-ledger.schema.json`.
- Every `canonicalHash` was recomputed and matched.
- The `merkleRoot` was recomputed and matched.
- Referential integrity against the current sidecars holds.
- `catalogueCommit` resolves against `git cat-file`.
- The signature envelope is internally consistent.

This is the bar PR CI enforces.

### 7.2 Require-but-trust: insist on `signature.state == "attested"`

```bash
python3 scripts/audit_mapping_ledger.py --require-signature
```

Same as §7.1 but also refuses an `unsigned` ledger. Use this to
assert _"this is a release artefact, not a working copy."_

### 7.3 Verify-with-Sigstore: cryptographic proof of origin

```bash
gh attestation verify mapping-ledger.json \
  --owner fenre \
  --bundle mapping-ledger.sigstore.bundle.json

python3 scripts/audit_mapping_ledger.py \
  --require-signature \
  --verify-signature
```

The first command proves — via Sigstore's transparency log and the
Fulcio identity certificate — that `mapping-ledger.json` was signed
by the `fenre/splunk-monitoring-use-cases` GitHub Actions environment
for this release. The second command re-runs §7.1, then shells out to
`gh attestation verify` itself as a belt-and-braces check that the
bundle still validates against the file on disk.

`scripts/audit_mapping_ledger.py` searches for the Sigstore bundle in
three places, in order:

1. The repository root (in-tree case).
2. The directory that contains the ledger file (the auditor downloaded
   both assets into the same folder).
3. `dist/` under the repo root (release-build local inspection).

Any of these satisfies the check; a missing bundle is a fatal error
only when `--verify-signature` is explicitly requested.

## 8. Operator workflows

### 8.1 Adding or changing a mapping

1. Edit the UC sidecar's `compliance[]` entry as normal.
2. Run `python3 scripts/generate_mapping_ledger.py` to regenerate the
   ledger. The audit will fail if you skip this step.
3. Run `python3 scripts/audit_mapping_ledger.py` to confirm the
   regeneration is self-consistent.
4. Commit both the sidecar change and
   `data/provenance/mapping-ledger.json` in the **same commit**, so
   `firstSeenCommit` / `lastModifiedCommit` point at the same SHA.
5. PR CI re-runs `--check` and the audit. A successful run means:
   - The ledger matches the sidecars byte-for-byte.
   - The regeneration is reproducible (the same SHAs drop out on every run).

### 8.2 Responding to a PR-CI ledger-drift failure

**Symptom:**
`FATAL: ledger drift (expected merkleRoot=abc…, got def…)` or
`FATAL: entry count mismatch`.

**Cause:** A sidecar `compliance[]` was modified without regenerating
the ledger.

**Fix:**

```bash
git pull
python3 scripts/generate_mapping_ledger.py
git add data/provenance/mapping-ledger.json
git commit -m "provenance: refresh mapping-ledger for <UC id>"
git push
```

### 8.3 Responding to an audit-script failure

**Symptom:**
`FATAL: canonicalHash mismatch for 22.5.2::gdpr@…`

**Cause:** The on-disk ledger was hand-edited (or corrupted by a
merge). The audit is the last line of defence against a bad
three-way merge silently rewriting a compliance claim.

**Fix:**

1. Do not trust the on-disk ledger. Regenerate from sidecars:
   `python3 scripts/generate_mapping_ledger.py`.
2. Review the diff carefully. Anything that changed is a real
   compliance-graph change; route it through the usual peer → legal
   → SME flow.
3. If the diff is surprising, `git log -p data/provenance/mapping-ledger.json`
   tells you when the corruption entered.

### 8.4 Responding to a stale `catalogueCommit`

**Symptom:**
`FATAL: catalogueCommit 217320f is not reachable from HEAD`.

**Cause:** The ledger was last generated on a branch that has been
force-pushed, or your clone is shallow.

**Fix:**

- Unshallow: `git fetch --unshallow`.
- Regenerate at HEAD: `python3 scripts/generate_mapping_ledger.py`.
- Commit the refreshed ledger.

### 8.5 Verifying a downloaded release

```bash
# In the directory where you downloaded the release assets:
gh attestation verify mapping-ledger.json \
  --owner fenre \
  --bundle mapping-ledger.sigstore.bundle.json
```

Expected: `✓ Verification succeeded!`. Then, optionally, clone the
repo at the release tag and run the audit against the downloaded
file:

```bash
git clone --depth=1 \
  --branch v5.4.0 \
  https://github.com/fenre/splunk-monitoring-use-cases.git
cd splunk-monitoring-use-cases
cp ~/Downloads/mapping-ledger.json data/provenance/
cp ~/Downloads/mapping-ledger.sigstore.bundle.json .
python3 scripts/audit_mapping_ledger.py \
  --require-signature \
  --verify-signature
```

Expected: `PASS: mapping ledger OK (1,889 entries, merkle root …, signature=attested)`.

### 8.6 Local dry-run of the release stamper

```bash
python3 scripts/stamp_ledger_release.py --dry-run
```

Writes `dist/mapping-ledger.json` and `dist/mapping-ledger.manifest.md`
with placeholder metadata and a conspicuous DRY-RUN banner. The
resulting files are **not** safe to publish as a release, but they
let authors sanity-check schema changes before cutting a tag.

## 9. Determinism guarantees

The generator is deterministic under the following conditions:

- The working tree is clean (no unstaged edits to sidecars).
- `catalogueCommit` is a real reachable commit — this is the only
  input to `generatedAt`, which is read from the commit's author date
  via `git show -s --format=%cI`.
- Python version ≥ 3.11 (the stdlib `json.dumps` output is stable
  across 3.11.x).
- `git` ≥ 2.30 (bulk `git log --name-only` output is stable across
  minor versions).

`generatedAt` is deliberately **not** wall-clock; two runs of the
generator on the same commit produce byte-identical ledgers, even
after `touch`ing sidecars, even across OSes. Any non-determinism here
would show up as the CI diff-gate rejecting otherwise-correct PRs.

If `git` metadata is unavailable (shallow clones, non-git checkouts),
the generator falls back to a fixed epoch of `2026-01-01T00:00:00Z`
so the audit still has a stable reference point — at the cost of
losing commit-date provenance. CI is hermetic enough that this
fallback only triggers in exotic local setups.

## 10. Versioning and evolution

`schemaVersion` is `1.0.0`. Any change to

- the entry shape (`entries[].*` fields),
- the set of fields in `canonicalisation.fieldOrder`,
- the `hashAlgorithm` constant, or
- the merkle construction (§4.3)

is a **breaking** change that requires a major bump and a migration
script. Minor bumps (`1.1.0`) are reserved for additive ledger-metadata
fields that do not participate in the hash. Patches (`1.0.1`) are
reserved for documentation, audit-script, and signature-envelope fixes
that do not touch the hash.

A v2.0.0 schema will plausibly introduce

- `sha3-256` or BLAKE3 for the `hashAlgorithm` constant, and
- a binary Merkle tree with inclusion proofs, for efficient
  per-entry verification against a short root.

The current `oneOf`-based signature envelope accommodates multiple
`signatureAlgorithm` values without a schema bump.

## 11. Cross-references

- `docs/peer-review-guide.md` — §5, the peer review QA gate.
- `docs/legal-review-guide.md` — §6, the legal review QA gate.
- `docs/sme-review-guide.md` — §7, the SME review QA gate.
- `docs/regulatory-change-watch.md` — the Phase 5.3 ledger that watches
  for upstream regulation changes.
- `docs/coverage-methodology.md` — how clause%, priority-weighted%, and
  assurance-adjusted% are computed; the ledger's `entryCount` is the
  denominator for those metrics.
- `api/README.md` — the static API surface the ledger underpins.
- `LEGAL.md` §5e — legal consequences of a failed attestation.
- `CHANGELOG.md` — Phase 5.4 release notes.
