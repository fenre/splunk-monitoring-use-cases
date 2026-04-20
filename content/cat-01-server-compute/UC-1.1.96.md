---
id: "1.1.96"
title: "NUMA Hit/Miss Ratio Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.96 · NUMA Hit/Miss Ratio Tracking

## Description

Tracking NUMA hit/miss ratio identifies opportunities for workload optimization on NUMA systems.

## Value

Tracking NUMA hit/miss ratio identifies opportunities for workload optimization on NUMA systems.

## Implementation

Parse /proc/zoneinfo for NUMA statistics per zone. Calculate hit ratio monthly. Alert when ratio drops below 90%, suggesting memory allocation pattern misalignment with NUMA topology.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:numa_zone`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse /proc/zoneinfo for NUMA statistics per zone. Calculate hit ratio monthly. Alert when ratio drops below 90%, suggesting memory allocation pattern misalignment with NUMA topology.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:numa_zone host=*
| stats sum(numa_hit) as hits, sum(numa_miss) as misses by host
| eval hit_ratio=hits/(hits+misses)
| where hit_ratio < 0.9
```

Understanding this SPL

**NUMA Hit/Miss Ratio Tracking** — Tracking NUMA hit/miss ratio identifies opportunities for workload optimization on NUMA systems.

Documented **Data sources**: `sourcetype=custom:numa_zone`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:numa_zone. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:numa_zone. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **hit_ratio** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where hit_ratio < 0.9` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Timechart

## SPL

```spl
index=os sourcetype=custom:numa_zone host=*
| stats sum(numa_hit) as hits, sum(numa_miss) as misses by host
| eval hit_ratio=hits/(hits+misses)
| where hit_ratio < 0.9
```

## Visualization

Gauge, Timechart

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
