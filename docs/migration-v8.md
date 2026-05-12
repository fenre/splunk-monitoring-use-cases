# Migration Guide: v7.x → v8.0

> **Audience:** anyone running the `splunk-uc-recommender` Splunk app, any
> downstream client of `/api/v1/recommender/*`, and any contributor who has
> automation that reads UC sidecars from `content/`.
>
> v8.0 is a **major** release. The catalogue itself stays additive (every
> previously-valid UC still validates against `uc.schema.json`), but the
> Splunk app surface and the on-disk layout under `splunk-apps/` collapse
> from "recommender + 12 per-regulation apps + helper TA" down to one
> unified app. That collapse is the breaking change.
>
> Note: this release was originally drafted as v9.0. v8.x was reserved for
> a parallel workstream that was deprioritised, so the major bump moves
> straight from 7.4.x to 8.0.0 and the previously-published "v9.0"
> release-notes draft has been folded into v8.0.

## TL;DR

| Concern | Before (v7.x) | After (v8.0) |
|---|---|---|
| Splunk apps shipped from this repo | 14 (`splunk-uc-recommender`, `splunk-uc-recommender-ta`, 12 `*-compliance-pack-*`) | **1** (`splunk-uc-recommender`) |
| Schema version | 1.6.x | **1.7.0** |
| New optional UC field | — | `splunkbaseApps[]` (forward-compat stub; not yet populated on shipped UCs — see *Known gaps* below) |
| New API endpoints | — | `/api/v1/recommender/splunkbase-index.json`, `/api/v1/recommender/fingerprints.csv` |
| New KV collections | — | `uc_recommender_implementations`, `uc_recommender_audit`, `uc_recommender_scan_runs` |
| New capability | — | `edit_uc_implementations` |
| Deployment posture | Search-tier only | Splunk Cloud-safe (Cloud Gold) |
| Auto-detection | Manual lookup matching | Saved-search fingerprinting + inventory signals + manual override |

## Known gaps in v8.0

The schema field `splunkbaseApps[]` is accepted by the validator and the
recommender dashboard renders an empty "No Splunkbase apps required"
state when a UC carries no entries. The 7,364-UC migration that
populates this array on every UC is **deferred to v8.x**. The shipped
`/api/v1/recommender/splunkbase-index.json` carries the Splunkbase app
metadata for the four apps the recommender itself depends on, so the
endpoint resolves and the dashboard does not show an upstream-error
banner. UC-level "Required Splunkbase apps" panels are stubs that will
fill in incrementally as `splunkbaseApps[]` is added to sidecars.

## What got deleted

The following directories and files **no longer exist** in v8.0. If your CI
or deployment pipeline references them, update it before pulling v8.0:

```
splunk-apps/cmmc-compliance-pack/                 # folded into splunk-uc-recommender
splunk-apps/dora-compliance-pack/
splunk-apps/gdpr-compliance-pack/
splunk-apps/hipaa-compliance-pack/
splunk-apps/iso27001-compliance-pack/
splunk-apps/nis2-compliance-pack/
splunk-apps/nist-800-53-compliance-pack/
splunk-apps/nist-csf-compliance-pack/
splunk-apps/pci-dss-compliance-pack/
splunk-apps/soc2-compliance-pack/
splunk-apps/sox-itgc-compliance-pack/
splunk-apps/uk-gdpr-compliance-pack/
splunk-apps/splunk-uc-recommender-ta/             # helper TA folded into the app
scripts/generate_splunk_app.py                    # only the recommender generator remains
```

The unified app now ships every tier-1 compliance saved search (CMMC, DORA<sup class="ref">[<a href="#ref-3">3</a>]</sup>,
GDPR<sup class="ref">[<a href="#ref-2">2</a>]</sup>, HIPAA<sup class="ref">[<a href="#ref-10">10</a>]</sup>, ISO 27001, NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup>, NIST 800-53, NIST CSF, PCI DSS, SOC 2,
SOX ITGC, UK GDPR<sup class="ref">[<a href="#ref-11">11</a>]</sup>) **disabled by default** plus the `uc_compliance_mappings`
lookup, so operators install one app and enable per regulation from the
*Compliance* view. Nothing schedules until enabled.

`scripts/backup_legacy_app_state.sh` snapshots the deleted directory tree
before the deletion lands, in case a downstream consumer needs the old
shape for diffing.

## Splunk operators — upgrade path

1. **Backup KV state** if you have any `splunk_uc_*` lookups or KV
   collections from the legacy apps:
   ```bash
   curl -ksS -u admin:<pw> -X POST \
     "https://<splunk>:8089/services/data/lookup-table-files" >/tmp/legacy-kv.json
   ```
2. **Uninstall every legacy app** in the table above. The unified app
   carries the same compliance content and reads-from / writes-to its own
   namespace, so coexistence is **not supported** — you'll get noisy
   duplicates if you leave a legacy compliance-pack installed.
3. **Install `splunk-uc-recommender` v8.0** (`.spl` artefact built on every
   push to `main`; download from the latest `validate.yml` workflow run, or
   from a tagged release).
4. **Re-enable just the saved searches you want.** Every saved search
   ships `disabled = 1, enableSched = 0` except for the four inventory
   probes (sourcetype / index / CIM acceleration / installed apps), which
   ship enabled because the recommender needs them to populate the KV
   collections on first install.
5. **Grant the new capability** to the roles that should be able to mark
   UCs as implemented or decommissioned:
   ```spl
   | rest /services/authorization/roles
   | search rolename IN ("admin", "power", "soc_lead")
   ```
   The unified app includes `default/authorize.conf` granting
   `edit_uc_implementations` to `admin` and `power` out of the box; map
   any custom roles in `local/authorize.conf` on your search head.
6. **Verify the implementations dashboard renders.** Navigate to
   `/app/splunk-uc-recommender/implementations`. If it shows
   "Inventory not populated yet", wait one scheduled cycle (~30 minutes)
   for the auto-detect saved searches to populate the KV collections.

## Schema consumers — what's new

`schemas/uc.schema.json` v1.7.0 adds **one** optional top-level array,
`splunkbaseApps[]`. Every previously-valid UC remains valid; existing
consumers can ignore the new field unless they want to surface "Required
Splunkbase apps" UI.

### Field shape

```jsonc
{
  "splunkbaseApps": [
    {
      "id": "1621",                                   // required, numeric Splunkbase app id
      "name": "Splunk Add-on for Microsoft Windows",  // required, human-readable
      "role": "data-source",                          // required: primary | data-source | premium | optional
      "url": "https://splunkbase.splunk.com/app/1621",// optional, regex-locked to splunkbase.splunk.com
      "minVersion": "8.6.0",                          // optional, MAJOR.MINOR(.PATCH)?
      "setupSkill": "splunk-input-apps",              // optional, kebab-case Cursor agent skill id
      "requiresSmeReview": false                      // optional, true while pending SME signoff
    }
  ]
}
```

### Tolerant-consumer rule still applies

If you read UC sidecars or `/api/v1/...` endpoints, you must continue to
parse unknown fields with a default branch (per
[`api-versioning.md`](api-versioning.md#tolerant-consumer-rule)). Adding
`splunkbaseApps[]` cannot break a tolerant consumer; it can break a
strict-shape consumer that asserts `additionalProperties: false`. Such
consumers should regenerate their typed bindings from
`@splunk-uc/schemas` v1.7.0 / `splunk-uc-schemas` v1.7.0.

### MCP consumers

`mcp/src/splunk_uc_mcp/tools/use_case.py` already declares
`splunkbaseApps[]` in `GET_USE_CASE_OUTPUT_SCHEMA` and coerces the compact
`sb` field from `uc-thin.json` into the rich shape when a UC has not yet
been migrated. No action required for MCP clients on v8.0+ servers.

## API consumers — what's new

Two new endpoints under `/api/v1/recommender/`:

| Path | Purpose | Cache hint |
|---|---|---|
| `/api/v1/recommender/splunkbase-index.json` | Splunkbase app metadata indexed by app id; consumed by the recommender's "Required Splunkbase apps" UI | ETag + `Cache-Control: public, max-age=3600` |
| `/api/v1/recommender/fingerprints.csv` | SHA-256 fingerprints of every UC's canonicalised SPL; consumed by the *Saved-search fingerprint* saved search to auto-detect implementations | ETag + `Cache-Control: public, max-age=3600` |

Both are **additive**. The existing `/api/v1/recommender/uc-thin.json`
gains an optional `sb` field per UC (compact form of `splunkbaseApps[]`)
under the same tolerant-consumer rule.

## CI consumers — what's new

`.github/workflows/validate.yml` gains:

* A package-recommender-on-push step (the `.spl` artefact ships from
  every push, not just from tagged releases).
* An AppInspect job that runs `splunk-appinspect` against the .spl with
  `--included-tags cloud,private_app` so Splunk Cloud admission failures
  surface in PRs.

`.github/workflows/uc-tests.yml` gains:

* A Playwright-based recommender e2e suite that boots Splunk
  ({9.4.1, 10.2.1}) with the unified app mounted and runs
  `tests/e2e/recommender.spec.ts`. Gated on the existing
  `UC_TEST_SPLUNK_PASSWORD` secret — forks without secrets stay green.

A new dashboard-SPL audit (`python3 -m splunk_uc audit-dashboard-spl`) extracts
every `<query>` from every Simple XML view in the recommender app,
expands `$tokens$` from `<input>` defaults, and dispatches each
panel against a live splunkd in `exec_mode=blocking`, asserting
`isFailed=False`. Wired into `scripts/deploy_to_splunk.sh` so every
local deploy validates that no panel will 400 on first paint.

## Local development

A new helper script, `scripts/deploy_to_splunk.sh`, deploys the packaged
`.spl` to a remote Splunk Enterprise instance using a bearer token
defined in `secrets.env`. The script tries URL-fetch first (spinning up
a local HTTP server splunkd dials back to) and falls back to SSH-staging
because Splunk's `/services/apps/local` REST endpoint **does not accept
multipart uploads** (the `.spl` must already exist on the server's
filesystem before splunkd will ingest it). See the
`splunk-remote-app-deploy` Cursor skill for the full background and the
working install patterns.

If the runner cannot reach the host or SSH to it, the script falls back
to clear manual instructions and exits with code 6 so CI can react.

## Rollback

Roll back to v7.x by:

1. Uninstalling `splunk-uc-recommender` v8.0.
2. Restoring the legacy app tree from
   `data/v7-app-snapshot/` (created by `scripts/backup_legacy_app_state.sh`
   on the v7.x → v8.0 cleanup commit).
3. Pinning your `requirements.txt` / `package.json` references to the
   pre-v8.0 schema version (`@splunk-uc/schemas@^1.6` /
   `splunk-uc-schemas==1.6.*`).

The catalogue content is fully forward-compatible — UCs added in v8.0
still validate against the v1.6 schema as long as you ignore the new
`splunkbaseApps[]` field.

## Questions

* MCP / API behaviour — see [`api-versioning.md`](api-versioning.md).
* Schema lifecycle — see [`schema-versioning.md`](schema-versioning.md).
* Deployment patterns — see the `splunk-remote-app-deploy` Cursor skill.
* Cloud admission — see [`splunk-cloud-compat.md`](splunk-cloud-compat.md).

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** European Parliament and Council of the European Union. (2016, April). *Regulation (EU) 2016/679 — General Data Protection Regulation*. Official Journal of the European Union, L 119. ELI: reg/2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj

<a id="ref-3"></a>**[3]** European Parliament and Council of the European Union. (2022, December). *Regulation (EU) 2022/2554 — Digital Operational Resilience Act (DORA)*. Official Journal of the European Union, L 333. ELI: reg/2022/2554. https://eur-lex.europa.eu/eli/reg/2022/2554/oj

<a id="ref-4"></a>**[4]** Payment Card Industry Security Standards Council. (2018). *Payment Card Industry Data Security Standard v3.2.1* (v3.2.1). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-5"></a>**[5]** Payment Card Industry Security Standards Council. (2022). *Payment Card Industry Data Security Standard v4.0* (v4.0). PCI SSC. https://www.pcisecuritystandards.org/document_library/?category=pcidss

<a id="ref-6"></a>**[6]** Splunk Inc. (2026). *Splunk Cloud Platform App Vetting requirements*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud/latest/Service/SplunkCloudservice

<a id="ref-7"></a>**[7]** Splunk Inc. (2026). *Splunk Cloud Platform Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/SplunkCloud

<a id="ref-8"></a>**[8]** Splunk Inc. (2026). *Splunk Enterprise Documentation*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk

<a id="ref-9"></a>**[9]** U.S. Department of Health & Human Services. (2002). *HIPAA Privacy Rule (45 CFR Parts 160 and 164, Subparts A and E)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/privacy/index.html

<a id="ref-10"></a>**[10]** U.S. Department of Health & Human Services. (2013). *HIPAA Security Rule (45 CFR Parts 160 and 164, Subparts A and C)*. Office for Civil Rights, HHS. 45 CFR 160, 164. https://www.hhs.gov/hipaa/for-professionals/security/index.html

<a id="ref-11"></a>**[11]** United Kingdom Parliament. (2018). *Data Protection Act 2018 (UK GDPR, retained EU law)*. The Stationery Office. 2018 c. 12. https://www.legislation.gov.uk/ukpga/2018/12/contents

<!-- END-AUTOGENERATED-SOURCES -->
