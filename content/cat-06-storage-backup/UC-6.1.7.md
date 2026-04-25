<!-- AUTO-GENERATED from UC-6.1.7.json — DO NOT EDIT -->

---
id: "6.1.7"
title: "Thin Provisioning Overcommit"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.7 · Thin Provisioning Overcommit

## Description

Over-committed thin-provisioned storage can cause sudden outages when physical capacity is exhausted. Monitoring prevents surprise failures.

## Value

Over-committed thin-provisioned storage can cause sudden outages when physical capacity is exhausted. Monitoring prevents surprise failures.

## Implementation

Poll aggregate/pool metrics showing logical vs physical capacity. Calculate overcommit ratio. Alert when physical utilization exceeds safe thresholds relative to committed capacity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Vendor TA, API polling.
• Ensure the following data sources are available: Aggregate/pool capacity metrics (logical vs physical).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll aggregate/pool metrics showing logical vs physical capacity. Calculate overcommit ratio. Alert when physical utilization exceeds safe thresholds relative to committed capacity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="netapp:ontap:aggregate"
| eval overcommit_ratio=logical_used/physical_used
| where overcommit_ratio > 1.5
| table aggregate, physical_used_pct, logical_used, overcommit_ratio
```

Understanding this SPL

**Thin Provisioning Overcommit** — Over-committed thin-provisioned storage can cause sudden outages when physical capacity is exhausted. Monitoring prevents surprise failures.

Documented **Data sources**: Aggregate/pool capacity metrics (logical vs physical). **App/TA** (typical add-on context): Vendor TA, API polling. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: netapp:ontap:aggregate. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="netapp:ontap:aggregate". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **overcommit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where overcommit_ratio > 1.5` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Thin Provisioning Overcommit**): table aggregate, physical_used_pct, logical_used, overcommit_ratio


Step 3 — Validate
Compare volume, aggregate, or SnapMirror state with NetApp ONTAP System Manager, the ONTAP CLI, or NetApp Active IQ Unified Manager for the same object and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Gauge (overcommit ratio per pool), Table (aggregates with overcommit stats), Bar chart (logical vs physical).

## SPL

```spl
index=storage sourcetype="netapp:ontap:aggregate"
| eval overcommit_ratio=logical_used/physical_used
| where overcommit_ratio > 1.5
| table aggregate, physical_used_pct, logical_used, overcommit_ratio
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

Gauge (overcommit ratio per pool), Table (aggregates with overcommit stats), Bar chart (logical vs physical).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
- [CIM: Performance](https://docs.splunk.com/Documentation/CIM/latest/User/Performance)
