<!-- AUTO-GENERATED from UC-5.13.78.json — DO NOT EDIT -->

---
id: "5.13.78"
title: "Catalyst Center License Utilization Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.13.78 · Catalyst Center License Utilization Tracking

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity, Inventory &middot; **Wave:** Walk

*We track how many of your Catalyst Center licenses are being used and warn you before you run out, so new devices can always be added.*

---

## Description

Tracks Catalyst Center license utilization by type, alerting when license consumption approaches capacity limits.

## Value

Running out of licenses prevents onboarding new devices. Proactive tracking ensures license procurement happens before capacity is exhausted.

## Implementation

Catalyst Center license data requires polling the Intent API.

API endpoint:
• `GET /dna/intent/api/v1/licenses/summary` — license counts by type
• `GET /dna/intent/api/v1/licenses/device/count` — per-device license usage

Create a custom scripted input:

```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_license/bin/collect_licenses.py]
interval = 86400
sourcetype = cisco:dnac:license
index = catalyst
disabled = 0
```

The script polls license summary data daily and outputs fields: `licenseType`, `totalLicenses`, `consumedLicenses`, `availableLicenses`, `expirationDate`.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk (Splunkbase 7538) installed as a base for connectivity.
- **Custom scripted input** required — the TA does not include a built-in license modular input. Deploy a scripted input that polls `GET /dna/intent/api/v1/licenses/device/count` and `GET /dna/intent/api/v1/licenses/device/summary` (see `docs/guides/catalyst-center.md` § Custom Scripted Inputs).
- Catalyst Center **2.3.5+** with Cisco Smart Licensing configured and active.
- RBAC: service account with **SUPER-ADMIN-ROLE** or **NETWORK-ADMIN-ROLE** for license data access.
- Understanding of your Catalyst Center licensing model: DNA Essentials, DNA Advantage, DNA Premier tiers, and their respective feature sets.

### Step 1 — Configure data collection
The Cisco Catalyst TA does **not** ship a license input. Deploy a custom scripted input that polls the Intent API license endpoints and writes to `index=catalyst`, `sourcetype=cisco:dnac:license`.

**Scripted input stanza (inputs.conf):**
```ini
[script://$SPLUNK_HOME/etc/apps/TA_catalyst_license/bin/collect_licenses.py]
interval = 86400
sourcetype = cisco:dnac:license
index = catalyst
disabled = 0
```

**API endpoints polled:** `GET /dna/intent/api/v1/licenses/device/count` and `GET /dna/intent/api/v1/licenses/device/summary`.
**Default interval:** 86400s (24 hours) — license counts change slowly; daily polling is sufficient.
**Volume:** ~1 event per license type per poll. Most deployments have 3–10 license types.

Key fields emitted by the script:
- `licenseType`: license tier name (e.g., "DNA Advantage", "DNA Essentials").
- `totalLicenses`: total number of licenses purchased/available.
- `consumedLicenses`: number of licenses currently in use.
- `availableLicenses`: remaining unused licenses.
- `expirationDate`: when the license term expires.

### Step 2 — Create the search and alert

```spl
index=catalyst sourcetype="cisco:dnac:license"
| stats latest(totalLicenses) as total latest(consumedLicenses) as consumed latest(availableLicenses) as available by licenseType
| eval utilization_pct=round(consumed*100/total,1)
| eval status=case(utilization_pct>90,"Critical",utilization_pct>75,"Warning",1==1,"Healthy")
| sort -utilization_pct
```

#### Understanding this SPL:
- **`latest(totalLicenses)` / `latest(consumedLicenses)`**: Takes the most recent snapshot per license type, avoiding double-counting from multiple poll events.
- **`utilization_pct`**: License consumption as a percentage of entitlement — the primary metric for capacity planning.
- **`status`**: Traffic-light classification — >90% is critical (immediate procurement needed), >75% is warning (plan procurement), otherwise healthy.
- Extend this with expiry tracking: add `latest(expirationDate) as expiry` and `eval days_to_expiry=round((strptime(expiry,"%Y-%m-%d")-now())/86400,0)` to flag licenses approaching renewal.

### Step 3 — Validate
- **Vendor UI parity:** open **Catalyst Center > System > Licensing** and compare the consumed/entitled counts and utilization percentages with the Splunk results.
- **Smart Account cross-reference:** log into the Cisco Smart Account portal and verify the license entitlements match the Splunk `total` values.
- **Expiry date check:** verify the `expirationDate` field is parseable and produces correct day counts.
- Run `| fieldsummary` on the raw events to confirm all expected fields (`licenseType`, `totalLicenses`, `consumedLicenses`, `availableLicenses`) are populated.

### Step 4 — Operationalize
- **Dashboard:** License utilization gauges (one per license type), expiry countdown tiles, and a 30-day utilization trend timechart showing consumption growth.
- **Alert:** Two alert types: (1) Utilization >90% → immediate procurement action. (2) Days to expiry ≤30 → renewal action. Route both to the licensing/procurement team.
- **Budget planning:** Use the 30-day utilization trend to project when licenses will be exhausted and generate procurement lead time estimates.

### Step 5 — Troubleshoot
- **Utilization shows 0% for all licenses:** The custom scripted input may not be deployed or is disabled. Check `inputs.conf` on the collection host and verify the script runs without errors.
- **`consumedLicenses` field not populated:** The API response format may differ across Catalyst Center versions. Run `| fieldsummary` on the raw events to identify the correct field name.
- **License synchronization delay:** There may be a delay (up to 24 hours) between Cisco Smart Account changes and Catalyst Center reflecting them.
- **Utilization fluctuating near threshold:** Device onboarding/decommissioning causes natural license fluctuation. Alert only on sustained upward trends, not transient spikes.
- If data is not arriving for `cisco:dnac:license`, check that the `license` input is enabled in the TA configuration and that the Catalyst Center API credentials have not expired.

Additional operational context for Catalyst Center License Utilization Tracking:

For month-over-month comparison:
- Export the primary search results monthly as CSV to a `catalyst_monthly_snapshots` directory. Compare current month vs previous month to identify trends, improvements, and regressions.
- Track the key metric from this UC over 90 days with `| timechart span=1w` for the quarterly operations review.

For SLA alignment:
- Define the acceptable threshold for this UC's primary metric in your SLA documentation.
- Schedule a weekly check against the SLA target. Breaches should generate tickets in your ITSM with a link to this UC's dashboard panel for investigation context.

Cross-reference with related UCs:
- When this UC flags an issue, always cross-reference with UC-5.13.1 (Device Health) and UC-5.13.16 (Network Health) to assess the broader impact.
- For compliance-related findings, connect to UC-5.13.28-33 for the compliance posture context.
- For security-related findings, connect to UC-5.13.34-39 for PSIRT advisory exposure.

Runbook integration:
- Document the response procedure for each alert from this UC in your operations runbook.
- Include: who to contact, what to check first, typical root causes, and escalation criteria.
- Review and update the runbook quarterly based on actual alert outcomes (was the runbook helpful? did it miss common scenarios?).

Additional troubleshooting:
- If the search returns unexpected results, check `| fieldsummary` on the base data to verify field names and types match the SPL.
- If data is not arriving for the expected sourcetype, verify the TA input is enabled and check `index=_internal sourcetype=splunkd component=ExecProcessor "TA_cisco_catalyst"` for errors from the modular input.
- If field values changed after a Catalyst Center upgrade, compare `| fieldsummary` from before and after the upgrade to identify renamed or restructured fields.
- If the search is slow, narrow the time range to `earliest=-20m` for a real-time snapshot, or use summary indexing for historical analysis.
- For vendor UI parity, cross-reference the Splunk results with the corresponding **Catalyst Center > Assurance** page for the same time window to confirm counts and values match.


## SPL

```spl
index=catalyst sourcetype="cisco:dnac:license" | stats latest(totalLicenses) as total latest(consumedLicenses) as consumed latest(availableLicenses) as available by licenseType | eval utilization_pct=round(consumed*100/total,1) | eval status=case(utilization_pct>90,"Critical",utilization_pct>75,"Warning",1==1,"Healthy") | sort -utilization_pct
```

## Visualization

Table: licenseType, total, consumed, available, utilization_pct, status; gauge or single value per license type; trend of utilization_pct over 90 days if stored in summary or indexed daily snapshots.

## Known False Positives

**License utilization naturally fluctuating near the threshold without action required.** License utilization in the 75-90% range is common for well-sized deployments. This range may persist for months without requiring additional licenses. Distinguish by checking the trend — is utilization steadily increasing toward 100%, or oscillating within a stable band? Suppress by alerting only on a sustained upward trend (7-day linear regression showing projected breach within 30 days) rather than a static threshold.

**Device decommissioning temporarily reducing license consumption.** When devices are removed from Catalyst Center, license consumption drops temporarily. If devices are being migrated, consumption will increase again when replacement devices are onboarded. Distinguish by correlating with inventory changes — check whether `dc(deviceId)` is decreasing. No suppression needed — track as a legitimate utilization change.

**License type not applicable to the Catalyst Center deployment.** Some license features (e.g., DNA Advantage, SD-Access) may show 0% utilization if the corresponding features are not deployed. These zero-utilization licenses should not appear in the utilization tracking dashboard. Distinguish by checking whether the license `type` corresponds to features actually deployed. Suppress by filtering `| where license_consumed>0` for active license utilization tracking.

**License synchronization delay between Cisco Smart Account and Catalyst Center.** There may be a delay between purchasing additional licenses in the Cisco Smart Account and those licenses appearing in Catalyst Center's license pool. During this delay, utilization may appear higher than actual. Distinguish by checking the Cisco Smart Account for recent license additions. No SPL suppression — wait for the synchronization to complete (typically within 24 hours).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Cisco Smart Licensing Using Policy — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!get-license-usage)
