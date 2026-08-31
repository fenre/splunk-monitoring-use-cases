# Kraftberedskapsforskriften — compliance expansion spec

Status: **Phase 4 implemented** (2026-08-31)  
Regulation ID: `no-kbf-nve`  
Authoritative source: [Lovdata SF/forskrift/2012-12-07-1157](https://lovdata.no/dokument/SF/forskrift/2012-12-07-1157)

## Problem

Bootstrap coverage reported **100 % clause coverage** with a single `commonClause` (`§6-1`), while all five cat-22.26 KBF UCs mapped to that one paragraph regardless of SPL semantics.

## Solution (Phase 1)

1. Expand `commonClauses[]` to **18 monitorable paragraphs** across kap. 2, 4, 6, and 7.
2. Add `obligationModel` pointing to source map, coverage matrix, and methodology doc (NIS2 pattern).
3. Retag UC-22.26.6–10 to semantically correct clauses.
4. Cross-map five existing OT UCs (cat-14) with dual `NO KBF` compliance entries.
5. Add `no-kbf-nve` to evidence-pack generator allowlist.

## ID strategy

Subcategory **22.26** had 20 UCs at Phase 1 bootstrap (not a schema maximum — e.g. 22.11 has 110). Phase 2 adds **22.26.21–28** for uncovered NO KBF clauses. The only ID rule is **gap-free ordering within the subcategory** (DESIGN.md).

## Phase 2 (implemented)

| UC | Clause | Title |
|----|--------|-------|
| 22.26.21 | §2-3 | KBF emergency risk register freshness monitoring |
| 22.26.22 | §2-5 | KBF grid incident notification chain latency |
| 22.26.23 | §2-10 | KBF internkontroll control-test evidence archive |
| 22.26.24 | §4-1 | KBF reparasjonsberedskap spare-parts register monitoring |
| 22.26.25 | §6-1 | Kraftsensitiv information access path monitoring |
| 22.26.26 | §6-5 | KBF supplier security agreement access compliance |
| 22.26.27 | §6-7 | KBF personkontroll privileged access correlation |
| 22.26.28 | §6-8 | Kraftsensitiv system backup and restore-test monitoring |

## Phase 3 (implemented)

- **18 NIS2 dual-mapping entries** on KBF UCs (22.26.6–28) and OT cross-maps (14.2.4, 14.2.9, 14.2.11, 14.6.6, 14.9.14)
- Machine-readable map: `data/no-kbf-nis2-dual-mapping.json` (15 clause-pair rows)
- Prose uplift: fixed stale §6-1 references in UC-22.26.7–10 `detailedImplementation`

## Phase 4 (implemented)

- **Silver-depth uplift** on UC-22.26.21–28: expanded `detailedImplementation` with vendor UI validation (Step 3) and product-specific troubleshooting (Step 5); lift scores 80–90/100.
- **`audit-no-kbf-coverage`** drift gate: `python3 -m splunk_uc audit-no-kbf-coverage` validates matrix rows, source-map URLs, `regulations.json` alignment, and UC traceability (`targetUcIds` ↔ compliance entries). Makefile target: `make audit-no-kbf-coverage`.
- **Matrix traceability fixes**: §6-3 targets UC-22.26.7 only (14.2.4 remains §7-10); §4-1 targets UC-22.26.24 only; added NVE §6-1 veileder URL to source map.
- **Norwegian regulatory primer** expanded in `non-technical-view.js` / `non-technical-view.data.ts` (18-clause KBF coverage, NIS2 dual-mapping, KBO-enheter).

## Phase 5 backlog

| Priority | Work |
|----------|------|
| P1 | SME review of dual-mapping assurance levels |
| P2 | Gold-tier lift (90+) on 22.26.21–28 if product-specificity score needs bump |
| P3 | Wire `audit-no-kbf-coverage` into CI validate.yml (optional ratchet) |

## Success metrics (Phase 1 target)

- Honest clause % (not 100 % on a 1-clause denominator)
- ≥ 10 distinct paragraphs with ≥ 1 UC
- ≥ 5 cross-mapped OT UCs outside cat-22
- Gap report lists uncovered high-priority paragraphs

## References

- [`docs/no-kbf-monitoring-methodology.md`](../no-kbf-monitoring-methodology.md)
- [`data/per-regulation/no-kbf-nve-coverage-expansion.json`](../../data/per-regulation/no-kbf-nve-coverage-expansion.json)
- [`data/no-kbf-nve-source-map.json`](../../data/no-kbf-nve-source-map.json)
- [`data/no-kbf-nis2-dual-mapping.json`](../../data/no-kbf-nis2-dual-mapping.json)
