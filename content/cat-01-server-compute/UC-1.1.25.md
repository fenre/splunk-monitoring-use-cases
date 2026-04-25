<!-- AUTO-GENERATED from UC-1.1.25.json — DO NOT EDIT -->

---
id: "1.1.25"
title: "NUMA Imbalance Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.25 · NUMA Imbalance Detection

## Description

NUMA imbalance causes memory locality issues and performance degradation on multi-socket systems.

## Value

NUMA imbalance causes memory locality issues and performance degradation on multi-socket systems.

## Implementation

Create a custom script that reads /proc/zoneinfo or numactl output and monitors NUMA hit/miss ratios. Alert when local NUMA hits drop below 90% on systems with multiple sockets, indicating memory is being accessed remotely.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix, custom scripted input`.
• Ensure the following data sources are available: `sourcetype=custom:numa_stats`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Create a custom script that reads /proc/zoneinfo or numactl output and monitors NUMA hit/miss ratios. Alert when local NUMA hits drop below 90% on systems with multiple sockets, indicating memory is being accessed remotely.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=custom:numa_stats
| stats avg(numa_hit) as avg_hits, avg(numa_miss) as avg_misses by host
| eval miss_pct=(avg_misses/(avg_hits+avg_misses))*100
| where miss_pct > 10
```

Understanding this SPL

**NUMA Imbalance Detection** — NUMA imbalance causes memory locality issues and performance degradation on multi-socket systems.

Documented **Data sources**: `sourcetype=custom:numa_stats`. **App/TA** (typical add-on context): `Splunk_TA_nix, custom scripted input`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: custom:numa_stats. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=custom:numa_stats. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **miss_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where miss_pct > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
On the host, compare with `top`, `htop`, `vmstat`, `iostat`, or `sar` as appropriate to this use case. For log-only detections, compare with the relevant file under `/var/log` (or `journalctl`) on a test host. Confirm that indexed event counts and field values line up with what you see on the system and that your role can search the right indexes and fields.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single Value, Gauge

## SPL

```spl
index=os sourcetype=custom:numa_stats
| stats avg(numa_hit) as avg_hits, avg(numa_miss) as avg_misses by host
| eval miss_pct=(avg_misses/(avg_hits+avg_misses))*100
| where miss_pct > 10
```

## Visualization

Single Value, Gauge

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
