<!-- AUTO-GENERATED from UC-6.1.24.json — DO NOT EDIT -->

---
id: "6.1.24"
title: "Aggregate Space Forecasting"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.24 · Aggregate Space Forecasting

## Description

Forecasting aggregate free space prevents sudden write failures on thin-provisioned pools. Supports procurement and volume migration planning.

## Value

Forecasting aggregate free space prevents sudden write failures on thin-provisioned pools. Supports procurement and volume migration planning.

## Implementation

Daily snapshot of aggregate utilization. Use `predict` or linear regression for 30/60-day runway. Alert when forecast crosses 85% within 30 days.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, REST API.
• Ensure the following data sources are available: Aggregate used/total bytes, snapshot reserve.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Daily snapshot of aggregate utilization. Use `predict` or linear regression for 30/60-day runway. Alert when forecast crosses 85% within 30 days.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:aggregate"
| timechart span=1d latest(physical_used_pct) as used_pct by aggregate_name
| predict used_pct as forecast future_timespan=30
```

Understanding this SPL

**Aggregate Space Forecasting** — Forecasting aggregate free space prevents sudden write failures on thin-provisioned pools. Supports procurement and volume migration planning.

Documented **Data sources**: Aggregate used/total bytes, snapshot reserve. **App/TA** (typical add-on context): Vendor TA, REST API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:aggregate. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:aggregate". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=1d** buckets with a separate series **by aggregate_name** — ideal for trending and alerting on this use case.
• Pipeline stage (see **Aggregate Space Forecasting**): predict used_pct as forecast future_timespan=30


Step 3 — Validate
Compare volume, aggregate, or SnapMirror state with NetApp ONTAP System Manager, the ONTAP CLI, or NetApp Active IQ Unified Manager for the same object and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Line chart (used % with forecast band), Table (aggregates by days-to-full), Single value (soonest full date).

## SPL

```spl
index=storage sourcetype="netapp:ontap:aggregate"
| timechart span=1d latest(physical_used_pct) as used_pct by aggregate_name
| predict used_pct as forecast future_timespan=30
```

## CIM SPL

```spl
| tstats `summariesonly` max(Performance.storage_used_percent) as used_pct
  from datamodel=Performance where nodename=Performance.Storage
  by Performance.host Performance.object span=1h
| where used_pct > 80
| sort - used_pct
```

## Visualization

Line chart (used % with forecast band), Table (aggregates by days-to-full), Single value (soonest full date).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
