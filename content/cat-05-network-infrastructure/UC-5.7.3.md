---
id: "5.7.3"
title: "Bandwidth by Application"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.3 · Bandwidth by Application

## Description

Application-level bandwidth breakdown helps prioritize QoS policies and justify network upgrades.

## Value

Application-level bandwidth breakdown helps prioritize QoS policies and justify network upgrades.

## Implementation

Enable NBAR (Network-Based Application Recognition) on Cisco routers to export application-tagged NetFlow. Ingest in Splunk.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for NetFlow (with NBAR).
• Ensure the following data sources are available: NetFlow with application identification.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable NBAR (Network-Based Application Recognition) on Cisco routers to export application-tagged NetFlow. Ingest in Splunk.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=netflow
| stats sum(bytes) as total_bytes by application
| sort -total_bytes | head 20 | eval GB=round(total_bytes/1073741824,2)
```

Understanding this SPL

**Bandwidth by Application** — Application-level bandwidth breakdown helps prioritize QoS policies and justify network upgrades.

Documented **Data sources**: NetFlow with application identification. **App/TA** (typical add-on context): Splunk Add-on for NetFlow (with NBAR). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: netflow.

**Pipeline walkthrough**

• Scopes the data: index=netflow. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by application** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.
• `eval` defines or adjusts **GB** — often to normalize units, derive a ratio, or prepare for thresholds.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.app span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
```

Understanding this CIM / accelerated SPL

**Bandwidth by Application** — Application-level bandwidth breakdown helps prioritize QoS policies and justify network upgrades.

Documented **Data sources**: NetFlow with application identification. **App/TA** (typical add-on context): Splunk Add-on for NetFlow (with NBAR). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Network_Traffic.All_Traffic` — enable acceleration for that model.
• `eval` defines or adjusts **bytes** — often to normalize units, derive a ratio, or prepare for thresholds.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (bandwidth by app), Bar chart, Table.

## SPL

```spl
index=netflow
| stats sum(bytes) as total_bytes by application
| sort -total_bytes | head 20 | eval GB=round(total_bytes/1073741824,2)
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

Pie chart (bandwidth by app), Bar chart, Table.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
