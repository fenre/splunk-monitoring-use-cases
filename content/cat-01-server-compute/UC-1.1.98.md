---
id: "1.1.98"
title: "TLB Shootdown Rate Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.98 · TLB Shootdown Rate Monitoring

## Description

High TLB shootdown rates indicate excessive cross-CPU cache invalidations affecting performance on multi-CPU systems.

## Value

High TLB shootdown rates indicate excessive cross-CPU cache invalidations affecting performance on multi-CPU systems.

## Implementation

Monitor TLB shootdown interrupts from /proc/interrupts. Create alerts when shootdown rate exceeds baseline. Recommend application profiling and memory access pattern optimization.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:tlb_stats, /proc/interrupts`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor TLB shootdown interrupts from /proc/interrupts. Create alerts when shootdown rate exceeds baseline. Recommend application profiling and memory access pattern optimization.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:tlb_stats host=*
| stats avg(tlb_shootdown_rate) as avg_rate by host
| where avg_rate > threshold
```

Understanding this SPL

**TLB Shootdown Rate Monitoring** — High TLB shootdown rates indicate excessive cross-CPU cache invalidations affecting performance on multi-CPU systems.

Documented **Data sources**: `sourcetype=custom:tlb_stats, /proc/interrupts`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:tlb_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:tlb_stats. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_rate > threshold` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart, Alert

## SPL

```spl
index=os sourcetype=custom:tlb_stats host=*
| stats avg(tlb_shootdown_rate) as avg_rate by host
| where avg_rate > threshold
```

## Visualization

Timechart, Alert

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
