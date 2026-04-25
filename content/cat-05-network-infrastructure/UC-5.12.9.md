<!-- AUTO-GENERATED from UC-5.12.9.json — DO NOT EDIT -->

---
id: "5.12.9"
title: "Roaming Usage Anomaly"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.12.9 · Roaming Usage Anomaly

## Description

Sudden data/voice roaming volume from HLR/VLR or TAP records may indicate SIM box, cloned IMSI, or billing leakage.

## Value

Sudden data/voice roaming volume from HLR/VLR or TAP records may indicate SIM box, cloned IMSI, or billing leakage.

## Implementation

Privacy: only hashed IMSI in Splunk; correlate with HLR IMEI change for SIM swap fraud.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: TAP files (TD.35), roaming analytics.
• Ensure the following data sources are available: `sourcetype="tap:cdr"`, `sourcetype="roaming:usage"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Privacy: only hashed IMSI in Splunk; correlate with HLR IMEI change for SIM swap fraud.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=telco sourcetype="roaming:usage"
| bin _time span=1d
| stats sum(charge_units) as units, sum(charge_amount) as rev by imsi_hash, visited_country, _time
| eventstats avg(units) as baseline by visited_country
| where units > 10*baseline
| sort -units
```

Understanding this SPL

**Roaming Usage Anomaly** — Sudden data/voice roaming volume from HLR/VLR or TAP records may indicate SIM box, cloned IMSI, or billing leakage.

Documented **Data sources**: `sourcetype="tap:cdr"`, `sourcetype="roaming:usage"`. **App/TA** (typical add-on context): TAP files (TD.35), roaming analytics. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: telco; **sourcetype**: roaming:usage. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=telco, sourcetype="roaming:usage". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by imsi_hash, visited_country, _time** so each row reflects one combination of those dimensions.
• `eventstats` rolls up events into metrics; results are split **by visited_country** so each row reflects one combination of those dimensions.
• Filters the current rows with `where units > 10*baseline` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Telephony CDRs and signaling are not in CIM; this search does not use CIM data model acceleration.


Step 3 — Validate
Match a roaming spike in CDRs to the billing or roaming broker file for a day; confirm rating metadata (MCC/MNC) maps correctly from your SBC/MSC export.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Map (visited countries), Table (suspicious subscribers), Line chart (roaming $ trend).

## SPL

```spl
index=telco sourcetype="roaming:usage"
| bin _time span=1d
| stats sum(charge_units) as units, sum(charge_amount) as rev by imsi_hash, visited_country, _time
| eventstats avg(units) as baseline by visited_country
| where units > 10*baseline
| sort -units
```

## Visualization

Map (visited countries), Table (suspicious subscribers), Line chart (roaming $ trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
