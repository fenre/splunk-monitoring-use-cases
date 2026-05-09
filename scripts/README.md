# scripts/

Utility and audit scripts for the Splunk monitoring use cases catalog.
All scripts read from `content/cat-*/UC-*.json` (the v7 canonical source)
unless noted otherwise.

## Quick reference

```
make audit            # Run all audit checks
make audit-structure  # UC JSON structure
make audit-cim        # CIM ↔ SPL alignment
make audit-links      # HTTP link checks (network)
make audit-consistency # Repo consistency
make inventory        # Regenerate data/inventory/
make manifest         # Regenerate eventgen manifest
```

## Audits (CI-safe)

| Script | Reads from | Purpose |
|--------|-----------|---------|
| `audit_uc_structure.py` | `use-cases/cat-*.md` | Audit legacy markdown UC blocks (required fields, enums, SPL presence). Canonical JSON validation runs in the build pipeline via [`tools/build/parse_content.py`](../tools/build/parse_content.py). |
| `audit_cim_spl_alignment.py` | `content/**/*.json` | CIM Models vs CIM SPL datamodel alignment |
| `audit_links.py` | `content/**/*.json` | HTTP check all URLs in `references` arrays |
| `audit_repo_consistency.py` | `enrichment.py` | Cross-check CAT_GROUPS, SPLUNK_APPS, INDEX.md |
| `audit_non_technical_sync.py` | `content/**/*.json` | non-technical-view.js vs UC/category coverage |
| `audit_perf_a11y.py` | committed assets | Performance budgets + axe-core accessibility |
| `audit_catalog_schema.py` | `catalog.json` | Validate catalog JSON shape |
| `audit_prerequisites.py` | `catalog.json` | Prerequisite graph integrity |
| `audit_quality_metadata.py` | `catalog.json` | Quality metadata coverage |
| `audit_splunk_cloud_compat.py` | `catalog.json` | SPL cloud compatibility |
| `audit_gold_profile.py` | `content/**/*.json` | Gold standard field completeness |
| `audit_spl_grammar.py` | `catalog.json` | SPL syntax validation |
| `audit_spl_duplicates.py` | `catalog.json` | Detect duplicate SPL across UCs |
| `audit_spl_hallucinations.py` | `catalog.json` | Detect fabricated SPL patterns |
| `audit_placeholders.py` | `catalog.json` | Find placeholder/stub content |
| `audit_splunkbase_ids.py` | `catalog.json` | Validate Splunkbase app IDs |
| `audit_compliance_mappings.py` | sidecars | Regulation mapping completeness |
| `audit_compliance_gaps.py` | sidecars | Regulation clause coverage gaps |
| `audit_monitoring_type.py` | `catalog.json` | Monitoring type enum consistency |

## Generators

| Script | Output | Purpose |
|--------|--------|---------|
| `inventory_ucs.py` | `data/inventory/` | UC inventory (JSON + CSV) |
| `parse_uc_catalog.py` | `eventgen_data/manifest-all.json` | UC manifest for eventgen |
| `generate_md_from_json.py` | `.md` files | Generate markdown from JSON content |
| `generate_api_surface.py` | API payloads | Full API surface generation |
| `generate_scorecard.py` | scorecard report | Quality scorecard markdown |
| `generate_equipment_tags.py` | equipment tags | Equipment tag generation |
| `generate_recommender_app.py` | Splunk app | Generates the unified `splunk-uc-recommender` app (single artefact since v9.0) |
| `build_es.py` | ES conf | Enterprise Security app conf |
| `build_ta.py` | TA conf | Technology Add-on conf |
| `build_provenance.py` | provenance ledger | Per-UC source provenance |

## Shared libraries

| Module | Used by | Purpose |
|--------|---------|---------|
| `equipment_lib.py` | generators, audits | Equipment table accessor (reads from `tools/build/enrichment.py`) |

## Deprecated

| Script | Reason |
|--------|--------|
| `normalize_cim_fields.py` | Operated on `use-cases/*.md` (no longer source of truth) |
| `sync_json_to_markdown.py` | Synced JSON sidecars into legacy markdown |
| `author_phase_c_ucs.py` | One-time phase C authoring script |
| `generate_phase2_*.py` | One-time phase 2 generation scripts |
| `generate_phase3_*.py` | One-time phase 3 generation scripts |

## Archive

One-time migration and fixup scripts are preserved in `scripts/archive/`
for historical reference.
