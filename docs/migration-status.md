# Migration Status: use-cases/ → content/

This document tracks the remaining dependencies on the legacy `use-cases/` tree.
The v7 pipeline uses `content/` as the canonical source; `use-cases/` is retained
only for the specific purposes listed below.

## Remaining Dependencies

| Component | File | Dependency | Target Removal |
|-----------|------|-----------|----------------|
| Equipment enrichment | `tools/build/enrichment.py` | `_load_sidecar_equipment_cache()` reads `use-cases/**/uc-*.json` as fallback | v7.5 |
| Legacy loader | `tools/build/parse_content.py` | `SPLUNK_UC_LOADER=legacy` env var activates v6 markdown loader | v8.0 |
| Non-technical sync audit | `scripts/audit_non_technical_sync.py` | Validates JS against `use-cases/cat-*.md` headings | v7.5 |
| Category markdown | `use-cases/cat-*.md` | Referenced by link-check workflow and some docs | v8.0 |
| ES/TA build scripts | `scripts/build_es.py`, `scripts/build_ta.py` | Comments reference use-cases/ paths | v7.5 |

## Completed Migrations

- [x] Primary catalog loading (v7.0): `content/` is default, `use-cases/` is fallback
- [x] grandmaExplanation (v7.1): loaded exclusively from `content/`
- [x] Equipment enrichment (v7.3): `content/` is primary, `use-cases/` is fallback (10.1)
- [x] UC-22.1.1 equipment tags (v7.3): removed nonsensical hardware tags

## Policy

- No new code should reference `use-cases/` as a primary data source
- New UCs are created only in `content/`
- The `use-cases/` tree will be archived (read-only) once all dependencies above are resolved
