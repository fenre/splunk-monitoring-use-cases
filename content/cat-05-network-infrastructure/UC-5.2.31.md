<!-- AUTO-GENERATED from UC-5.2.31.json — DO NOT EDIT -->

---
id: "5.2.31"
title: "Application Visibility and Network Application Trending (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.31 · Application Visibility and Network Application Trending (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We trend which applications and traffic types dominate so heavy cloud use, file shares, and video do not take you by surprise.*

---

## Description

Identifies top applications and protocols on network to understand usage patterns and detect anomalies.

## Value

Operations teams trend Meraki MX application visibility data to identify bandwidth-dominant applications and track usage patterns for capacity planning and policy enforcement.

## Implementation

Extract application field from flow logs. Aggregate by app and category.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: `sourcetype=meraki (type=flows OR type=firewall) application=*`.
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Extract application field from flow logs. Aggregate by app and category.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) application=*
| stats sum(bytes) as app_bytes, count as flow_count by application, application_category
| eval app_bandwidth_pct=round(app_bytes*100/sum(app_bytes), 2)
| sort - app_bytes
| head 20
```

#### Understanding this SPL

**Application Visibility and Network Application Trending (Meraki MX)** — Operations teams trend Meraki MX application visibility data to identify bandwidth-dominant applications and track usage patterns for capacity planning and policy enforcement.

Documented **Data sources**: `sourcetype=meraki (type=flows OR type=firewall) application=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by application, application_category** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **app_bandwidth_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
- Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

Understanding this CIM / accelerated SPL

**Application Visibility and Network Application Trending (Meraki MX)** — Operations teams trend Meraki MX application visibility data to identify bandwidth-dominant applications and track usage patterns for capacity planning and policy enforcement.

Documented **Data sources**: `sourcetype=meraki (type=flows OR type=firewall) application=*`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

- Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
- `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: App bandwidth pie chart; top apps bar chart; bandwidth timeline by app.

## SPL

```spl
index=meraki sourcetype="meraki" (type=flows OR type=firewall) application=*
| stats sum(bytes) as app_bytes, count as flow_count by application, application_category
| eval app_bandwidth_pct=round(app_bytes*100/sum(app_bytes), 2)
| sort - app_bytes
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

## Visualization

App bandwidth pie chart; top apps bar chart; bandwidth timeline by app.

## Known False Positives

Releases, batch jobs, and video calls can make one application or department dominate bandwidth in a good week.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
