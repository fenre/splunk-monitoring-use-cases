# Legacy `use-cases/` Burndown Plan (P1 step 7)

Status: **PHASE A COMPLETE** — 2026-05-09. The 20 orphans listed
in the diagnostic snapshot below have been migrated to JSON SSOT.
The legacy tree now has zero orphans and Phase B (move
`use-cases/` → `content-legacy/`) is unblocked.

This document is the canonical maintainer playbook for retiring
the legacy `use-cases/cat-*.md` markdown tree in favour of the
JSON SSOT under `content/cat-*-*/`. It captures the coverage
diff, lists the 20 UCs that originally existed only in legacy
markdown, and sequences the safe deletion in three phases.

---

## TL;DR

- **Live state (post-Phase-A):** the legacy tree has **0 orphans**.
  Every UC ID in `use-cases/cat-*.md` now also exists as a JSON
  sidecar under `content/`. CI enforces this with
  `scripts/audit_legacy_orphans.py --check`.
- **JSON SSOT** (`content/`) carries **7,677 UC sidecars** (up from
  7,657 pre-Phase-A; the +20 came from this migration).
- **Legacy markdown** (`use-cases/`) still references its original
  6,625 UC IDs across 24 files (Phase A added JSON sidecars
  *next to* legacy markdown — it did not delete or reformat the
  legacy tree).
- **Overlap:** all 6,625 legacy IDs are covered by SSOT.
- **SSOT-only (legacy markdown is genuinely out-of-date):**
  1,052 UCs — these reflect ongoing JSON-first authoring since
  Phase A's snapshot.

The 20 orphans were 100% recoverable: well-formed UC sections in
the legacy markdown with the standard fields (criticality,
difficulty, monitoring type, value, App/TA, equipment models,
data sources, SPL). They were migration-ready, not
authorship-required, and were converted by hand to JSON sidecars
that validate against `schemas/uc.schema.json` v1.7.0.

---

## Diagnostic snapshot (2026-05-09, HEAD `40cb461`)

The pre-Phase-A snapshot is preserved here for historical
reference and so that the migration-status doc has a stable
"before" anchor. The post-Phase-A live snapshot is in the TL;DR
above.

| Bucket                          | Count |
|---------------------------------|-------|
| Both (covered by SSOT)          | 6,605 |
| Only in legacy markdown (orphans) | 20  |
| Only in JSON SSOT (newer)       | 1,052 |
| **Legacy total**                | 6,625 |
| **SSOT total**                  | 7,657 |

Reproducible with:

```bash
python3 - <<'PY'
import re, pathlib
ROOT = pathlib.Path('.')
legacy_ids = set()
for f in sorted(ROOT.glob('use-cases/cat-*.md')) + sorted(ROOT.glob('use-cases/cat-*/UC-*.md')):
    text = f.read_text(encoding='utf-8', errors='ignore')
    legacy_ids.update(m.group(1) for m in re.finditer(r'UC-(\d+\.\d+\.\d+)\b', text))
ssot_ids = {m.group(1) for f in ROOT.glob('content/cat-*/UC-*.json')
            if (m := re.search(r'UC-(\d+\.\d+\.\d+)\.json$', f.name))}
print(f'legacy={len(legacy_ids)} ssot={len(ssot_ids)} both={len(legacy_ids & ssot_ids)} '
      f'legacy_only={len(legacy_ids - ssot_ids)} ssot_only={len(ssot_ids - legacy_ids)}')
PY
```

---

## The 20 orphan UCs (now migrated to JSON SSOT)

All originated in `use-cases/cat-05-network-infrastructure.md`
and slot into existing SSOT subcategories. 19 of 20 are clean
contiguous extensions; 1 fills a SSOT numbering gap. They were
migrated 2026-05-09 — every ID below now has an
`UC-X.Y.Z.json` sidecar under
`content/cat-05-network-infrastructure/`.

### Subcategory 5.1 — IGP / routing protocol (extends from index 66)

| UC ID         | Title                                                          |
|---------------|----------------------------------------------------------------|
| UC-5.1.67     | IS-IS Adjacency and SPF Calculation Monitoring                 |
| UC-5.1.68     | BFD Session State for IGP Fast Failure Detection               |
| UC-5.1.69     | IPv6 Interface and Neighbor Discovery Monitoring               |
| UC-5.1.70     | NTP Stratum and Peer Health on Network Devices                 |
| UC-5.1.71     | QoS DSCP Marking and Classification Visibility                 |
| UC-5.1.72     | PIM Neighbor and Multicast Group State Monitoring              |
| UC-5.1.73     | IGMP Snooping and Multicast Group Membership                   |
| UC-5.1.74     | VLAN Configuration Change and VTP Audit                        |
| UC-5.1.75     | Network Topology Discovery and Source-of-Truth Reconciliation  |

### Subcategory 5.4 — Wireless / WLC (extends from index 37)

| UC ID         | Title                                                          |
|---------------|----------------------------------------------------------------|
| UC-5.4.38     | Cisco C9800 WLC AP Join Failures                               |
| UC-5.4.39     | Cisco C9800 Client Authentication and Session Monitoring       |
| UC-5.4.40     | Cisco C9800 RF Performance and Channel Assignment              |

### Subcategory 5.5 — SD-WAN / SASE (extends from index 20)

| UC ID         | Title                                                          |
|---------------|----------------------------------------------------------------|
| UC-5.5.21     | VMware VeloCloud Orchestrator Tunnel Health                    |
| UC-5.5.22     | Aruba EdgeConnect SD-WAN Tunnel and Application Performance    |
| UC-5.5.23     | Versa Networks SD-WAN Path Quality and Routing Decisions       |
| UC-5.5.24     | Fortinet SD-WAN Health-Check and SLA Compliance                |
| UC-5.5.25     | Cato Networks SASE Event Monitoring                            |

### Subcategory 5.6 — DNS / DHCP (extends from index 17)

| UC ID         | Title                                                          |
|---------------|----------------------------------------------------------------|
| UC-5.6.18     | BlueCat DNS Edge Query Analytics                               |
| UC-5.6.19     | BlueCat DHCP Lease Utilization and Scope Health                |

### Subcategory 5.8 — Network management platforms (fills SSOT gap)

| UC ID         | Title                                                          | Note                              |
|---------------|----------------------------------------------------------------|-----------------------------------|
| UC-5.8.26     | CDN Origin Hit Rate and Cache Efficiency (CloudFront / Akamai / Fastly) | SSOT skipped 5.8.26; legacy fills it. |

SSOT 5.8 already has UC-5.8.{1-5, 7-25, 27-30} (28 files). The
gap at 5.8.6 is pre-existing in both legacy and SSOT — not part of
this burndown.

---

## Burndown phases

The migration is intentionally split across three calendar phases
to leave a soak window for any external consumer that still
references `use-cases/cat-*.md` directly. The whole sequence
spans one minor release cycle.

### Phase A — Migrate the 20 orphans (COMPLETE 2026-05-09)

**Goal (achieved):** zero net loss of content. Every legacy-only
UC now has a JSON sidecar in `content/cat-05-network-infrastructure/`.

What landed:

1. **20 new JSON sidecars** under
   `content/cat-05-network-infrastructure/UC-5.{1,4,5,6,8}.*.json`,
   each validating against `schemas/uc.schema.json` v1.7.0
   (required fields: `id`, `title`, `criticality`, `difficulty`,
   `monitoringType`, `value`, `app`, `dataSources`, `spl`,
   `implementation`, `visualization`, `cimModels`,
   `grandmaExplanation`).
2. **20 regenerated markdown companions** via
   `scripts/generate_md_from_json.py`.
3. **`_category.json` updated**: subcategory `useCaseCount`
   ratchets — 5.1: 66 → 75; 5.4: 37 → 40; 5.5: 20 → 25;
   5.6: 17 → 19; 5.8: 28 → 29. Category total: 700 → 720.
4. **Auditor flipped to `--check`**: validate.yml + Makefile +
   `EXPECTED_ORPHAN_COUNT_AT_BASELINE` decremented 20 → 0;
   `docs/ci-architecture.md` prose updated.
5. **Author quality:** all 20 UCs ship with `status: community`
   (no SME review yet — that's the explicit gold-tier-deferred
   contract). Field-level provenance flows from the original
   legacy markdown; equipment and `equipmentModels` were
   normalised against the SSOT registry.

**Acceptance gate (now live):**
`scripts/audit_legacy_orphans.py --check` exits 0 — confirmed
2026-05-09 with `Zero orphans.` Reproducible build artefacts
verified byte-identical post-migration.

### Phase B — Move `use-cases/` → `content-legacy/`, freeze for one minor

**Goal:** clear public signal that the legacy tree is no longer
authoritative, while preserving deep links from external bookmarks
through the deprecation window.

1. `git mv use-cases content-legacy` (keeps git history).
2. Add `content-legacy/README.md` with a one-line redirect:
   *"This tree was the original authoring format. The JSON SSOT
   under `content/` is now authoritative. This directory will be
   deleted in v8.1."*
3. Update `.cursorignore` to exclude `content-legacy/` from
   AI-context to prevent agents from authoring there.
4. Update `pages.yml` and `validate.yml` path triggers to drop
   `use-cases/**` and add `content-legacy/**` (read-only — any
   PR that modifies a file there fails CI).
5. Update `docs/migration-status.md` with a "P1 step 7 — Phase B
   complete" stamp and the calendar deadline for Phase C.
6. Add a release-note entry to `index.html` and `CHANGELOG.md`.

### Phase C — Delete `content-legacy/` in v8.1

**Goal:** zero residual artefacts of the legacy authoring system.

1. `git rm -r content-legacy/` — single PR, one commit.
2. Drop the path from `.cursorignore` (no longer needed).
3. Drop the path from `validate.yml` and `pages.yml` triggers.
4. Update `docs/migration-status.md` with a "P1 step 7 — Phase C
   complete" stamp.

---

## Cross-references

- **`docs/migration-status.md`** — this is the index for every
  P1 sub-step; this doc is its detail page for step 7.
- **`docs/architecture.md`** §3 (Use case content) — describes
  the JSON SSOT contract that this burndown serves.
- **`docs/external-consumer-matrix.md`** — `use-cases/` is *not*
  on the external-consumer surface list; deletion has zero
  impact on MCP tools, API endpoints, or SSG URLs.
- **`docs/rollback-playbook.md`** — Phase B's `git mv` is the
  rollback point. Phase C cannot be cleanly rolled back; soak
  Phase B for one full release cycle (≥3 months) before Phase C.
- **`schemas/uc.schema.json`** — gold-standard contract every
  Phase-A migrated sidecar must satisfy.

---

## Why this is safe

1. **JSON SSOT is the published surface.** `dist/catalog.json`,
   `api/v1/`, the MCP server, and the SSG all build from
   `content/`, never from `use-cases/`. Deleting `use-cases/`
   does not change a single byte of any consumer-visible artefact.
2. **The 20 orphans are not in any release artefact.** Because
   the build pipeline reads JSON SSOT, the orphan markdown UCs
   never made it into `catalog.json`, the MCP wire format, or
   the static site. They are content liability, not consumer
   contract.
3. **Phase B is fully reversible.** Git history preserves the
   tree; `git mv content-legacy use-cases` restores the previous
   state at any point during the deprecation window.
4. **CI gates the migration.** `audit_uc_structure.py --full`
   runs against the JSON SSOT; the burndown does not introduce
   any new validation pressure on existing UCs.

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** Anthropic, et al. (2026). *Model Context Protocol Specification*. Anthropic PBC. Retrieved May 11, 2026, from https://modelcontextprotocol.io/

<a id="ref-2"></a>**[2]** Cisco Systems, Inc. (2026). *Cisco Catalyst SD-WAN Documentation*. Retrieved May 11, 2026, from https://www.cisco.com/c/en/us/support/routers/sd-wan/series.html

<a id="ref-3"></a>**[3]** Fortinet, Inc. (2026). *Fortinet FortiOS Documentation*. Retrieved May 11, 2026, from https://docs.fortinet.com/product/fortigate

<a id="ref-4"></a>**[4]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<!-- END-AUTOGENERATED-SOURCES -->
