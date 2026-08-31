# Kraftberedskapsforskriften — compliance expansion spec

Status: **Phase 1 implemented** (2026-08-31)  
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

Subcategory **22.26 remains at 20 UCs** (four Norwegian frameworks × five UCs). New KBF depth is delivered via **cross-mapping** and future **22.26.21+** or a dedicated subcategory in Phase 2.

## Phase 2 backlog

| Priority | Work |
|----------|------|
| P1 | New UCs: §6-1, §6-8, §2-3, §2-5, §4-1 (2026 amendment) |
| P2 | NIS2 dual-mapping for shared energy-sector controls |
| P3 | Dedicated evidence-pack SME review + Norwegian primer section |
| P4 | Optional `audit-no-kbf-coverage` matrix drift gate |

## Success metrics (Phase 1 target)

- Honest clause % (not 100 % on a 1-clause denominator)
- ≥ 10 distinct paragraphs with ≥ 1 UC
- ≥ 5 cross-mapped OT UCs outside cat-22
- Gap report lists uncovered high-priority paragraphs

## References

- [`docs/no-kbf-monitoring-methodology.md`](../no-kbf-monitoring-methodology.md)
- [`data/per-regulation/no-kbf-nve-coverage-expansion.json`](../../data/per-regulation/no-kbf-nve-coverage-expansion.json)
- [`data/no-kbf-nve-source-map.json`](../../data/no-kbf-nve-source-map.json)
