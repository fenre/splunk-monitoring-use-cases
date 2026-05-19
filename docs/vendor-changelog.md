# Vendor changelog

Hand-curated, machine-readable upstream vendor product release notes that affect Splunk field names, log formats, and sourcetypes. The catalogue uses this data to warn UC authors when their SPL still references deprecated or renamed vendor fields.

## Scope (Cisco-only v1)

The original multi-vendor plan (Cisco + CrowdStrike + AWS + Microsoft) was re-scoped to **Cisco-only v1** because each vendor exposes a different release-notes ingestion surface. Follow-up PRs add one vendor each so parsing logic stays reviewable:

| PR | Vendor | Data file |
| --- | --- | --- |
| **J-5 (this)** | Cisco | `data/vendor-changelog/cisco.json` |
| J-5b | AWS | `data/vendor-changelog/aws.json` |
| J-5c | Microsoft | `data/vendor-changelog/microsoft.json` |
| J-5d | CrowdStrike | `data/vendor-changelog/crowdstrike.json` |

v1 does **not** auto-fetch vendor portals. Maintainers commit curated entries; the audit validates schema, freshness, and UC impact.

## Data layout

```
data/vendor-changelog/
  cisco.json          # vendor slug matches filename stem
  …                   # future vendors slot in additively
schemas/vendor-changelog.schema.json
```

Each file carries:

- `version` — semver of the data file itself
- `generated` — ISO date (`YYYY-MM-DD`) when the file was last refreshed
- `schema_version` — contract version (`1.0` today)
- `vendor` / `vendor_display` — slug + human label
- `entries[]` — sorted by `(release_date desc, id asc)`

Entry `product` slugs align with Cisco equipment model IDs in `tools/build/enrichment.py` (e.g. `asa`, `meraki`, `ise`, `firepower`).

## Adding an entry by hand (canonical v1 path)

1. Open `data/vendor-changelog/cisco.json`.
2. Append a new object under `entries` with a unique id (`CISCO-YYYY-NNN`).
3. Set `change_kind` to one of the closed enum values in the schema.
4. Populate field arrays (`fields_added`, `fields_removed`, `fields_renamed`, `fields_deprecated`) honestly — empty arrays are required.
5. List `affected_uc_categories` (top-level category numbers as strings, e.g. `"13"`).
6. Bump top-level `generated` to today's date.
7. Re-sort entries by release date (newest first), then id.
8. Validate:

```bash
PYTHONPATH=src python3 -m splunk_uc audit-vendor-changelog --check
```

### Optional helper

```bash
PYTHONPATH=src python3 -m splunk_uc add-vendor-changelog-entry \
  --vendor cisco \
  --product asa \
  --release 9.21 \
  --release-date 2026-06-01 \
  --change-kind field-renamed \
  --summary "…" \
  --details "…" \
  --spl-impact "…" \
  --source-url "https://www.cisco.com/…" \
  --categories 13 16 \
  --rename-from old_field \
  --rename-to new_field
```

The helper assigns the next sequential id, re-sorts entries, stamps `generated`, and re-validates against the JSON Schema.

## Audit behaviour

```bash
make audit-vendor-changelog
# or
PYTHONPATH=src python3 -m splunk_uc audit-vendor-changelog --check --max-age-days 180
PYTHONPATH=src python3 -m splunk_uc audit-vendor-changelog --out dist/audits --show-impact
```

Outputs (gitignored under `dist/audits/`):

- `vendor-changelog.json` — machine summary (freshness, category rollups, impacted UCs)
- `vendor-changelog.md` — human rollup (freshness table, top-5 recent changes, top-10 impacted UCs)

### Freshness policy

| Age of `generated` | Result |
| --- | --- |
| ≤ 90 days | OK |
| 91–180 days | WARN (stderr) |
| > 180 days (`--check`) | FAIL (exit 1) |

CI uses `--max-age-days 180` with headroom while the seed file stabilises; ratchet down as maintainers refresh the file each release.

### UC impact rules

For each UC sidecar, the audit flags changelog entries when **any** of:

- The UC's category appears in `affected_uc_categories`
- Removed or renamed (`from`) fields appear in SPL (`spl`, `cimSpl`, `rbaSpl`, `mvSpl`)
- Deprecated fields appear in SPL
- `dataSources` mentions the entry's `product` slug

Impacts are advisory for v1 — they surface review candidates, not CI hard-fails on individual UCs.

### Unknown vendors

Adding `data/vendor-changelog/aws.json` without registering `aws` in `KNOWN_VENDORS` inside `src/splunk_uc/audits/vendor_changelog.py` fails fast. Each new vendor PR must extend that registry and its allowed `schema_version` set.

## Makefile targets

- `make audit-vendor-changelog` — schema + freshness gate
- `make add-vendor-changelog-entry` — prints helper usage (pass flags as needed)

Both are included in `make audit-full`.
