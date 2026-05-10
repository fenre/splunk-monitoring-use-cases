<!-- AUTO-GENERATED from UC-5.8.12.json — DO NOT EDIT -->

---
id: "5.8.12"
title: "License Expiration Tracking and Renewal Alerts (Meraki)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.8.12 · License Expiration Tracking and Renewal Alerts (Meraki)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know before Meraki licenses slip past their date, so renewals are planned instead of a surprise cut-off.*

---

## Description

Ensures licenses don't expire unexpectedly and features remain available.

## Value

Network operations teams track Meraki license expiration dates across all license types, projecting renewal costs and detecting expired or soon-to-expire licenses before devices lose cloud management capabilities.

## Implementation

1. Enable both Licenses Overview and Licenses Coterm Licenses inputs (TA v3+). Licenses Overview returns the org-wide expirationDate and status; Licenses Coterm Licenses returns one event per individual license key with claimDate, expirationDate, licenseType, state. 2. Compute days-until-expire from the ISO-8601 expirationDate. 3. Trigger Splunk alerts at 90 days, 60 days, and 30 days before expiry. 4. For PDL (Per-Device Licensing) tenancies, also enable the Licenses Subscriptions input (meraki:licensessubscriptions).

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Licenses Overview input (sourcetype=meraki:licensesoverview, daily) for org-level license summary, and Licenses Coterm Licenses input (sourcetype=meraki:licensescotermlicenses, daily) for per-key co-term license detail. OAuth scope dashboard:licensing:config:read..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable both Licenses Overview and Licenses Coterm Licenses inputs (TA v3+). Licenses Overview returns the org-wide expirationDate and status; Licenses Coterm Licenses returns one event per individual license key with claimDate, expirationDate, licenseType, state. 2. Compute days-until-expire from the ISO-8601 expirationDate. 3. Trigger Splunk alerts at 90 days, 60 days, and 30 days before expiry. 4. For PDL (Per-Device Licensing) tenancies, also enable the Licenses Subscriptions input (meraki…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:licensesoverview" earliest=-1d
| stats latest(licensedDeviceCounts) as licensed_counts,
        latest(expirationDate) as expiry_iso,
        latest(status) as license_status
         by organizationId, organizationName
| eval days_until_expire = round((strptime(expiry_iso,"%Y-%m-%dT%H:%M:%SZ") - now())/86400, 0)
| where days_until_expire <= 90
| append [
    search index=meraki sourcetype="meraki:licensescotermlicenses" earliest=-1d
    | stats latest(claimDate) as claimed,
            latest(expirationDate) as expiry_iso,
            latest(licenseType) as license_type,
            latest(state) as state
             by licenseKey, organizationId
    | eval days_until_expire = round((strptime(expiry_iso,"%Y-%m-%dT%H:%M:%SZ") - now())/86400, 0)
    | where days_until_expire <= 90
  ]
| sort days_until_expire
```

#### Understanding this SPL

**License Expiration Tracking and Renewal Alerts (Meraki)** — Network operations teams track Meraki license expiration dates across all license types, projecting renewal costs and detecting expired or soon-to-expire licenses before devices lose cloud management capabilities.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Licenses Overview input (sourcetype=meraki:licensesoverview, daily) for org-level license summary, and Licenses Coterm Licenses input (sourcetype=meraki:licensescotermlicenses, daily) for per-key co-term license detail. OAuth scope dashboard:licensing:config:read. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:licensesoverview. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:licensesoverview", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by organizationId, organizationName** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **days_until_expire** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where days_until_expire <= 90` — typically the threshold or rule expression for this monitoring goal.
- Appends rows from a subsearch with `append`.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: License expiration countdown; renewal timeline; license detail table.

## SPL

```spl
index=meraki sourcetype="meraki:licensesoverview" earliest=-1d
| stats latest(licensedDeviceCounts) as licensed_counts,
        latest(expirationDate) as expiry_iso,
        latest(status) as license_status
         by organizationId, organizationName
| eval days_until_expire = round((strptime(expiry_iso,"%Y-%m-%dT%H:%M:%SZ") - now())/86400, 0)
| where days_until_expire <= 90
| append [
    search index=meraki sourcetype="meraki:licensescotermlicenses" earliest=-1d
    | stats latest(claimDate) as claimed,
            latest(expirationDate) as expiry_iso,
            latest(licenseType) as license_type,
            latest(state) as state
             by licenseKey, organizationId
    | eval days_until_expire = round((strptime(expiry_iso,"%Y-%m-%dT%H:%M:%SZ") - now())/86400, 0)
    | where days_until_expire <= 90
  ]
| sort days_until_expire
```

## Visualization

License expiration countdown; renewal timeline; license detail table.

## Known False Positives

Co-term vs per-device licensing and co-termination renewals can confuse expiring tiles; match Splunk to Organization > License in Dashboard.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
