<!-- AUTO-GENERATED from UC-5.2.23.json — DO NOT EDIT -->

---
id: "5.2.23"
title: "Firewall Rule Hit Analysis and Top Denied Flows (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.23 · Firewall Rule Hit Analysis and Top Denied Flows (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We list top denied flows on the small office device so you can see scanning, bad apps, and policy gaps without digging through raw logs by hand.*

---

## Description

Identifies top denied flows to optimize firewall rules and detect policy violations.

## Value

Security teams analyze Meraki MX firewall rule hit patterns, identifying top denied flows and validating rule effectiveness against security policy.

## Implementation

Analyze firewall deny events from flow logs. Correlate with rules.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: `sourcetype=meraki (type=flows OR type=firewall) action="deny"` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Analyze firewall deny events from flow logs. Correlate with rules.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) action="deny"
| stats count as deny_count by firewall_rule, src, dest, dest_port
| sort - deny_count
| head 20
```

#### Understanding this SPL

**Firewall Rule Hit Analysis and Top Denied Flows (Meraki MX)** — Security teams analyze Meraki MX firewall rule hit patterns, identifying top denied flows and validating rule effectiveness against security policy.

Documented **Data sources**: `sourcetype=meraki (type=flows OR type=firewall) action="deny"` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by firewall_rule, src, dest, dest_port** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action IN ("deny","denied","drop","dropped","blocked","block")
  by All_Traffic.src All_Traffic.dest span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Firewall Rule Hit Analysis and Top Denied Flows (Meraki MX)** — Security teams analyze Meraki MX firewall rule hit patterns, identifying top denied flows and validating rule effectiveness against security policy.

Documented **Data sources**: `sourcetype=meraki (type=flows OR type=firewall) action="deny"` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Top denied flows table; denial timeline; source/dest distribution heatmap.

## SPL

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) action="deny"
| stats count as deny_count by firewall_rule, src, dest, dest_port
| sort - deny_count
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Traffic.All_Traffic
  where All_Traffic.action IN ("deny","denied","drop","dropped","blocked","block")
  by All_Traffic.src All_Traffic.dest span=1h
| sort -count
```

## Visualization

Top denied flows table; denial timeline; source/dest distribution heatmap.

## Known False Positives

Port scans, misconfigured clients, and noisy default-deny rules can flood deny counts without a targeted attack.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
