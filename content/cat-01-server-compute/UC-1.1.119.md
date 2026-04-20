---
id: "1.1.119"
title: "Defunct (Zombie) Process Accumulation"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-1.1.119 · Defunct (Zombie) Process Accumulation

## Description

Accumulating zombie processes indicate application resource leaks causing process table exhaustion risk.

## Value

Accumulating zombie processes indicate application resource leaks causing process table exhaustion risk.

## Implementation

Monitor ps output for Z (zombie) state processes. Create alerts when zombie count exceeds 10. Include parent process information to identify resource leak culprit.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix`.
• Ensure the following data sources are available: `sourcetype=ps`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor ps output for Z (zombie) state processes. Create alerts when zombie count exceeds 10. Include parent process information to identify resource leak culprit.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=ps host=* state="Z"
| stats count as zombie_count by host
| where zombie_count > 10
```

Understanding this SPL

**Defunct (Zombie) Process Accumulation** — Accumulating zombie processes indicate application resource leaks causing process table exhaustion risk.

Documented **Data sources**: `sourcetype=ps`. **App/TA** (typical add-on context): `Splunk_TA_nix`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: os; **sourcetype**: ps. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=os, sourcetype=ps. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where zombie_count > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge, Table

## SPL

```spl
index=os sourcetype=ps host=* state="Z"
| stats count as zombie_count by host
| where zombie_count > 10
```

## Visualization

Gauge, Table

## References

- [Splunk_TA_nix](https://splunkbase.splunk.com/app/833)
