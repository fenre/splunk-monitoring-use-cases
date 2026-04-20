---
id: "1.1.84"
title: "Runaway Process Detection (CPU Hog)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.84 · Runaway Process Detection (CPU Hog)

## Description

Runaway processes consuming excessive CPU degrade performance for all workloads on the host.

## Value

Runaway processes consuming excessive CPU degrade performance for all workloads on the host.

## Implementation

Use Splunk_TA_nix top input to track per-process CPU usage. Create alerts for processes consistently exceeding 80% CPU. Include user, parent process, and command line context. Suggest kill or scaling actions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=top`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Splunk_TA_nix top input to track per-process CPU usage. Create alerts for processes consistently exceeding 80% CPU. Include user, parent process, and command line context. Suggest kill or scaling actions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=top host=*
| stats avg(cpu_pct) as avg_cpu by host, process
| where avg_cpu > 80
```

Understanding this SPL

**Runaway Process Detection (CPU Hog)** — Runaway processes consuming excessive CPU degrade performance for all workloads on the host.

Documented **Data sources**: `sourcetype=top`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: top. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=top. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host, process** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_cpu > 80` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table, Timechart

## SPL

```spl
index=os sourcetype=top host=*
| stats avg(cpu_pct) as avg_cpu by host, process
| where avg_cpu > 80
```

## Visualization

Table, Timechart

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
