<!-- AUTO-GENERATED from UC-5.2.29.json — DO NOT EDIT -->

---
id: "5.2.29"
title: "Threat Intelligence Correlation and IoC Matching (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.29 · Threat Intelligence Correlation and IoC Matching (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We line up your threat indicators with what the small office already saw so you can see known bad addresses without waiting on a manual list.*

---

## Description

Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.

## Value

Security teams correlate Meraki MX firewall traffic against threat intelligence IoC feeds, prioritizing unblocked connections to high-confidence indicators of compromise.

## Implementation

Create threat intelligence lookup table. Correlate with network events.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: `sourcetype=meraki type=security_event OR type=urls OR type=flows OR type=firewall OR type=ids-alerts` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Create threat intelligence lookup table. Correlate with network events.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=security_event OR type=urls OR type=flows OR type=firewall OR type=ids-alerts)
| lookup threat_intelligence_list src as src OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src, dest, threat_name
| sort - hit_count
```

#### Understanding this SPL

**Threat Intelligence Correlation and IoC Matching (Meraki MX)** — Security teams correlate Meraki MX firewall traffic against threat intelligence IoC feeds, prioritizing unblocked connections to high-confidence indicators of compromise.

Documented **Data sources**: `sourcetype=meraki type=security_event OR type=urls OR type=flows OR type=firewall OR type=ids-alerts` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
- Filters the current rows with `where threat_severity="high" OR threat_severity="critical"` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by src, dest, threat_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: IoC match timeline; threat severity breakdown; affected hosts table.

## SPL

```spl
index=meraki sourcetype="meraki" (type=security_event OR type=urls OR type=flows OR type=firewall OR type=ids-alerts)
| lookup threat_intelligence_list src as src OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src, dest, threat_name
| sort - hit_count
```

## Visualization

IoC match timeline; threat severity breakdown; affected hosts table.

## Known False Positives

New cloud ranges, fast-flux, and short-lived goodware can overlap threat feeds; tune age and scope of feeds you trust.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
