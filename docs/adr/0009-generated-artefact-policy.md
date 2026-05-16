# ADR-0009: Generated artefacts are uncommitted by default

- **Status:** Accepted
- **Date:** 2026-05-08
- **Deciders:** Repository maintainers

## Context

The repository has accumulated a mixed strategy for generated
artefacts. Some are committed at every PR (`catalog.json`, `data.js`,
`llms.txt`, `llms-full.txt`); others are reproduced in `dist/` only
during build (`api/v1/`, the SSG `dist/uc/UC-X.Y.Z/` per-UC HTML, the
search shards). The same artefact can simultaneously exist as:

1. A committed root-level copy under `./catalog.json` (read by the
   browser on `index.html` for the SPA, read by external consumers,
   read by some audits).
2. A regenerated copy under `dist/catalog.json` produced by every
   build.

This duality has caused real harm:

- Until P1 step 5b (2026-05-08), the `_stage_public()` step in
  `tools/build/build.py` *copied* the project-root `catalog.json`
  over the freshly built `dist/catalog.json`. The committed copy
  silently shadowed the SSOT-derived output; whichever was on disk
  at the time of the build became authoritative until the next
  audit ran.
- PRs that only touch `content/cat-*/` and forget to regenerate
  `catalog.json` introduce subtle drift; CI's git-diff watchlist
  catches it but only after a CI round-trip, not on the local
  pre-commit hook.
- External consumers fetching `https://github.com/.../catalog.json`
  receive a snapshot whose freshness is bounded by the last
  contributor's local `make build`, which is an unstable contract.
- The committed binaries inflate `git clone` size and pollute PR
  diffs (the catalog is ~9 MB; `data.js` is ~43 MB).

The codeguard supply-chain rules are clear: every committed artefact
should either be the canonical source of truth or be reproducible
from a canonical source via a deterministic build. A generated
artefact stored alongside its source — without provenance metadata —
is the worst of both worlds: it is opaque to PR review yet trusted by
consumers.

[ADR-0007](0007-json-as-source-of-truth.md) and
[ADR-0008](0008-canonical-constants.md) close the source-of-truth
side. This ADR closes the artefact side.

## Decision

**Generated artefacts are NEITHER committed NOR maintained at HEAD.**
They are produced into `dist/` during `make build` and shipped via
exactly one of three release channels:

1. **GitHub Pages** — for browser-facing artefacts (`dist/index.html`,
   `dist/api/`, `dist/catalog.json`, `dist/uc/UC-X.Y.Z/`). Deployed
   per-push from `main` by [`pages.yml`](../../.github/workflows/pages.yml)
   with Sigstore provenance. The Pages site is the canonical
   external endpoint.
2. **GitHub Releases** — for distributable archives (`.spl`, `.tgz`,
   the SBOM bundle, the `llms-full.txt` snapshot). Attached at tag
   creation by [`release.yml`](../../.github/workflows/release.yml)
   with `actions/attest-build-provenance` Sigstore attestations and
   the `anchore/sbom-action` artefact bundle (SPDX, CycloneDX, source).
3. **Per-tag tagged blobs** — for any artefact that absolutely must
   be browsable in the git history (machine-readable corpora that
   third-party tooling pins to a tag). These live under `releases/<tag>/`
   in tagged commits **only**; they are not present at `HEAD`.

**No generated artefact may exist simultaneously at HEAD and at a
tag.** The rule is binary: either the artefact is regenerated from
sources every build (the default), or it is published only at tag
boundaries with an explicit Sigstore attestation. Mixed strategies
are explicitly disallowed because they reintroduce the shadowing
class of bugs that motivated this ADR.

### Per-artefact decisions

| Artefact | Disposition |
|---|---|
| `dist/catalog.json` | Generated; published via Pages. Project-root `./catalog.json` will be deleted in P1 step 5c (`p1-delete-legacy-final`). |
| `dist/data.js` | Generated; will be retired in P5 (`p5-data-js-retire`) once the Vite frontend lands. |
| `dist/llms.txt`, `dist/llms-full.txt` | Generated; published via Pages. Project-root copies deleted in P1 step 5c. |
| `dist/api/v1/**.json` | Generated; published via Pages with `cache-control: public, max-age=600`. |
| `dist/uc/UC-X.Y.Z/index.html` | Generated; published via Pages. Permalink contract is per [ADR-0005](0005-uc-id-x-y-z-scheme.md). |
| `dist/manifest.json`, `dist/openapi.yaml` | Generated; published via Pages. Drop the `generatedAt` timestamp once P8 reproducibility lands. |
| `dist/BUILD-INFO.json` | Generated; intentionally non-reproducible (carries build commit + timestamp). Published via Pages but not consumed by clients. |
| `releases/v*.tar.gz`, `*.spl` | Tagged-only via Releases with Sigstore attestation. Never at HEAD. |
| `dist/SHA256SUMS.txt`, `dist/sbom-*.json` | Tagged-only via Releases. |
| `data/baselines/<vX.Y.Z>.json` | **Exception**: committed at HEAD because it is a build-time *input*, not output. Recorded snapshots of historical state used by drift audits. |

The `data/baselines/` exception is intentional: those files are
authored once per release tag and read by audits as inputs, not
emitted by the build. They satisfy [ADR-0008](0008-canonical-constants.md)'s
JSON-as-singleton rule and live forever.

### Reproducibility contract

For an artefact to be eligible for the "uncommitted, regenerate from
source" path, it must be **byte-reproducible**: two consecutive
`make build` invocations from the same git SHA must produce
identical bytes. This is enforced by
`tests/build/test_legacy_artifacts_parity.py` for the SSOT-derived
artefacts (catalog.json, llms*.txt, data.js).

Artefacts that are *not yet* byte-reproducible (today: the search
shards, the manifest timestamp, BUILD-INFO.json) remain on the
"published-via-Pages" path but the gap is tracked under
`p4-build-reproducibility` for closure during P8 observability.
Until then, consumers pinning to the Pages URL get whatever the
latest deploy emitted; consumers wanting bit-stable inputs use the
release tarballs.

## Consequences

**Positive:**

- The shadowing class of bug (committed file silently overrides
  generated output) cannot recur — the committed file simply doesn't
  exist.
- PR diffs no longer include 9 MB JSON re-emissions; the diff signal
  matches the actual change.
- Repository clone size shrinks measurably (catalog.json + data.js +
  llms*.txt = ~52 MB committed; ~52 MB removed from every clone).
- External consumers point at a stable URL (Pages or Release asset)
  with provenance metadata, not at a `raw.githubusercontent.com`
  blob whose freshness depends on the last contributor's local
  build.
- Sigstore + SBOM workflow becomes the integrity contract; consumers
  can `gh attestation verify` exactly what they downloaded.
- Audits like `audit_repo_consistency.py` get to assert "no
  generated artefact at HEAD" as a hard invariant.

**Negative:**

- Forks that depend on `catalog.json` being browsable in the git
  history must repoint to the Pages URL or pull a release tarball.
  Mitigation: the migration is announced in `CHANGELOG.md` and the
  `External-consumer impact matrix` (planned under
  `p11-consumer-matrix`) calls out every affected URL with its new
  endpoint.
- Contributors testing `index.html` locally without first running
  `make build` see an empty SPA. Mitigation: `make serve` runs the
  build first; the README and CONTRIBUTING.md call this out.
- The reproducibility gap (BUILD-INFO timestamp, search shards)
  means the Pages output is technically not bit-stable today.
  Mitigation: tracked under `p4-build-reproducibility`; consumers
  needing stability use Releases.

**Required CI gates** (extant or planned):

- `tests/build/test_legacy_artifacts_parity.py:test_legacy_artefacts_not_in_project_static_files`
  — pins that the build pipeline doesn't accidentally re-add
  generated names to `_PROJECT_STATIC_FILES`.
- `python3 -m splunk_uc audit-repo-consistency` — extended in P1 step 5c to
  fail if `./catalog.json`, `./data.js`, or `./llms*.txt` reappear
  at the project root.
- `tests/build/test_legacy_artifacts_parity.py` — byte-reproducible
  re-emission of catalog.json + llms*.txt across two consecutive
  builds.
- `release.yml` — Sigstore attestation on every Release asset; the
  attestation chain is the integrity contract for the
  "tagged-only" artefacts.

## Alternatives considered

- **Continue the mixed strategy** with a watchdog audit. Rejected:
  the watchdog itself was the reason we discovered the shadowing
  bug, and watchdogs are reactive — the bug had been live for
  months. Removing the duplicate eliminates the failure mode.
- **Commit only at release tags** (no project-root copy at HEAD,
  but tag commits include them). Rejected: still allows external
  consumers to pin against `raw.githubusercontent.com/.../v8.0.0/catalog.json`,
  which is fine; but Pages already serves a stable, attested
  endpoint, so the tag-only commit adds maintenance without adding
  capability.
- **Branch protection rule that blocks generated paths.** Rejected:
  branch protection is a syntactic guard; the audit is a semantic
  guard. We want the audit because it covers the case where someone
  introduces a *new* generated path that branch protection didn't
  yet know about.

## Migration

Phase 1 step 5b (DONE 2026-05-08) made `dist/` SSOT-authoritative
for `catalog.json`, `data.js`, and `llms*.txt` by removing those
names from `_PROJECT_STATIC_FILES`. The project-root copies remain
as a transitional staging during one release, then:

- **P1 step 5c** (`p1-delete-legacy-final`) deletes the project-root
  copies, repoints the consumers (`scripts/equipment_lib.py`,
  `python3 -m splunk_uc audit-repo-consistency`, `python3 -m splunk_uc audit-splunk-cloud-compat`,
  `python3 -m splunk_uc generate-api-surface`, `tools/capture_baselines.py`),
  and updates the CI watchlist + path triggers.
- **P5 (`p5-data-js-retire`)** deletes `dist/data.js` once the apps/web/
  pages no longer need it.

After both phases land, the only generated artefacts at HEAD are the
ones explicitly enumerated in this ADR's per-artefact table; every
new addition requires updating the table.

## Links

- Renderer: [`tools/build/render_legacy_artifacts.py`](../../tools/build/render_legacy_artifacts.py)
- Build pipeline: [`tools/build/build.py`](../../tools/build/build.py)
- Reproducibility gate: [`tests/build/test_legacy_artifacts_parity.py`](../../tests/build/test_legacy_artifacts_parity.py)
- Release pipeline: [`.github/workflows/release.yml`](../../.github/workflows/release.yml)
- Pages pipeline: [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml)
- Related ADRs: [ADR-0007](0007-json-as-source-of-truth.md) (UC source
  of truth), [ADR-0008](0008-canonical-constants.md) (every constant
  has one home), [ADR-0003](0003-single-catalog-json-plus-per-category-api.md)
  (catalog.json shape contract)
- Repo-overhaul plan: cross-cutting policy `policy-generated`,
  `p1-delete-legacy-final`, `p5-data-js-retire`,
  `p4-build-reproducibility`

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Related repository documents

- [`docs/adr/0003-single-catalog-json-plus-per-category-api.md`](0003-single-catalog-json-plus-per-category-api.md)
- [`docs/adr/0005-uc-id-x-y-z-scheme.md`](0005-uc-id-x-y-z-scheme.md)
- [`docs/adr/0007-json-as-source-of-truth.md`](0007-json-as-source-of-truth.md)
- [`docs/adr/0008-canonical-constants.md`](0008-canonical-constants.md)

### Cited by

- [`docs/DESIGN.md`](../DESIGN.md)
- [`docs/adr/0008-canonical-constants.md`](0008-canonical-constants.md)
- [`docs/adr/0010-sample-and-sample-data-co-exist.md`](0010-sample-and-sample-data-co-exist.md)
- [`docs/adr/0011-schema-lineage-governance.md`](0011-schema-lineage-governance.md)
- [`docs/adr/0013-frontend-rebuild-scaffold.md`](0013-frontend-rebuild-scaffold.md)
- [`docs/adr/README.md`](README.md)
- [`docs/capacity-and-staffing.md`](../capacity-and-staffing.md)
- [`docs/external-consumer-matrix.md`](../external-consumer-matrix.md)
- [`docs/north-star-scorecard.md`](../north-star-scorecard.md)
- [`docs/rollback-playbook.md`](../rollback-playbook.md)

<!-- END-AUTOGENERATED-SOURCES -->
