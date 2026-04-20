---
id: "5.1.8"
title: "Device CPU/Memory Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.8 · Device CPU/Memory Utilization

## Description

CPU exhaustion causes packet drops, routing failures, management unresponsiveness.

## Value

CPU exhaustion causes packet drops, routing failures, management unresponsiveness.

## Implementation

Poll CISCO-PROCESS-MIB and CISCO-MEMORY-POOL-MIB every 300s. Alert CPU >80% or memory >85%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP, CISCO-PROCESS-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=snmp:cpu`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll CISCO-PROCESS-MIB and CISCO-MEMORY-POOL-MIB every 300s. Alert CPU >80% or memory >85%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:cpu"
| timechart span=5m avg(cpmCPUTotal5minRev) as cpu_pct by host | where cpu_pct > 80
```

Understanding this SPL

**Device CPU/Memory Utilization** — CPU exhaustion causes packet drops, routing failures, management unresponsiveness.

Documented **Data sources**: `sourcetype=snmp:cpu`. **App/TA** (typical add-on context): SNMP, CISCO-PROCESS-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:cpu. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:cpu". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where cpu_pct > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart, Gauge, Table of high-utilization devices.

## SPL

```spl
index=network sourcetype="snmp:cpu"
| timechart span=5m avg(cpmCPUTotal5minRev) as cpu_pct by host | where cpu_pct > 80
```

## Visualization

Line chart, Gauge, Table of high-utilization devices.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
