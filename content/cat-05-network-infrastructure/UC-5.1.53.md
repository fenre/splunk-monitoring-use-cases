<!-- AUTO-GENERATED from UC-5.1.53.json — DO NOT EDIT -->

---
id: "5.1.53"
title: "Cellular Data Usage and Overage Monitoring (Meraki MG)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.53 · Cellular Data Usage and Overage Monitoring (Meraki MG)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with cellular data usage and overage monitoring so the team can act before it grows into a bigger outage.*

---

## Description

Tracks cellular data consumption to manage carrier costs and prevent overages.

## Value

Operations teams monitor Meraki MG cellular data usage against plan limits, preventing overage charges by alerting before data caps are reached and identifying high-consumption patterns.

## Implementation

1. Enable the Summary Top Devices by Usage input (TA v3+, polls GET /organizations/{orgId}/summary/top/devices/byUsage daily, OAuth scope dashboard:general:telemetry:read). 2. Filter to MG devices via a left join on the Devices input where productType=cellularGateway. 3. The 'usage.total' field is in kB; convert to GB for plan-quota comparison. 4. Per-SIM monthly billing data must be pulled from the carrier (AT&T, Verizon) directly; the Meraki API does not expose it.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Summary Top Devices by Usage input (sourcetype=meraki:summarytopdevicesbyusage, daily) and Devices input (sourcetype=meraki:devices). NOTE: the TA does NOT expose per-SIM data plan consumption or carrier billing data. For real overage/quota tracking, use the Meraki Dashboard cellular billing UI export or the carrier portal API..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Summary Top Devices by Usage input (TA v3+, polls GET /organizations/{orgId}/summary/top/devices/byUsage daily, OAuth scope dashboard:general:telemetry:read). 2. Filter to MG devices via a left join on the Devices input where productType=cellularGateway. 3. The 'usage.total' field is in kB; convert to GB for plan-quota comparison. 4. Per-SIM monthly billing data must be pulled from the carrier (AT&T, Verizon) directly; the Meraki API does not expose it.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:summarytopdevicesbyusage" earliest=-30d
| join type=left serial [
    search index=meraki sourcetype="meraki:devices" productType="cellularGateway"
    | stats latest(model) as model, latest(name) as device_name, latest(network.name) as network_name by serial
  ]
| where isnotnull(model)
| stats latest(usage.total) as total_kb,
        latest(usage.percentage) as pct_of_org
         by serial, device_name, model, network_name
| eval total_gb = round(total_kb/1024/1024, 2)
| where total_gb > 0
| sort - total_gb
```

#### Understanding this SPL

**Cellular Data Usage and Overage Monitoring (Meraki MG)** — Operations teams monitor Meraki MG cellular data usage against plan limits, preventing overage charges by alerting before data caps are reached and identifying high-consumption patterns.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Summary Top Devices by Usage input (sourcetype=meraki:summarytopdevicesbyusage, daily) and Devices input (sourcetype=meraki:devices). NOTE: the TA does NOT expose per-SIM data plan consumption or carrier billing data. For real overage/quota tracking, use the Meraki Dashboard cellular billing UI export or the carrier portal API. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:summarytopdevicesbyusage. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:summarytopdevicesbyusage", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Joins to a subsearch with `join` — set `max=` to match cardinality and avoid silent truncation.
- Filters the current rows with `where isnotnull(model)` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by serial, device_name, model, network_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **total_gb** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where total_gb > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Data usage gauge per gateway; consumption timeline; overage alert table.

## SPL

```spl
index=meraki sourcetype="meraki:summarytopdevicesbyusage" earliest=-30d
| join type=left serial [
    search index=meraki sourcetype="meraki:devices" productType="cellularGateway"
    | stats latest(model) as model, latest(name) as device_name, latest(network.name) as network_name by serial
  ]
| where isnotnull(model)
| stats latest(usage.total) as total_kb,
        latest(usage.percentage) as pct_of_org
         by serial, device_name, model, network_name
| eval total_gb = round(total_kb/1024/1024, 2)
| where total_gb > 0
| sort - total_gb
```

## Visualization

Data usage gauge per gateway; consumption timeline; overage alert table.

## Known False Positives

Carrier testing, local SIM swaps, and planned tower work can look like a connectivity fault. Compare the Meraki event log to the same window in Splunk.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
