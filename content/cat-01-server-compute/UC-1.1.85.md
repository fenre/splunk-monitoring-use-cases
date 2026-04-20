---
id: "1.1.85"
title: "Memory Hog Detection"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.85 · Memory Hog Detection

## Description

Memory-consuming processes can cause OOM conditions affecting all applications on the host.

## Value

Memory-consuming processes can cause OOM conditions affecting all applications on the host.

## Implementation

Monitor per-process memory percentage from top input. Create alerts for processes consistently exceeding 40% of system memory. Include growth trend and suggest right-sizing or memory limit enforcement.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=top`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor per-process memory percentage from top input. Create alerts for processes consistently exceeding 40% of system memory. Include growth trend and suggest right-sizing or memory limit enforcement.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=top host=*
| stats avg(mem_pct) as avg_mem by host, process
| where avg_mem > 40
```

Understanding this SPL

**Memory Hog Detection** — Memory-consuming processes can cause OOM conditions affecting all applications on the host.

Documented **Data sources**: `sourcetype=top`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: top. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=top. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, process** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_mem > 40` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Gauge

## SPL

```spl
index=os sourcetype=top host=*
| stats avg(mem_pct) as avg_mem by host, process
| where avg_mem > 40
```

## Visualization

Table, Gauge

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
