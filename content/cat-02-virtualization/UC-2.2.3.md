<!-- AUTO-GENERATED from UC-2.2.3.json — DO NOT EDIT -->

---
id: "2.2.3"
title: "Cluster Shared Volume Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.2.3 · Cluster Shared Volume Health

## Description

CSV issues can cause VM storage access failures across the entire cluster. Redirected I/O mode significantly degrades performance.

## Value

CSV issues can cause VM storage access failures across the entire cluster. Redirected I/O mode significantly degrades performance.

## Implementation

Enable Failover Clustering operational log. Alert on CSV ownership changes, redirected I/O mode, and disk health issues. Monitor Perfmon counters for CSV latency.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows` (Hyper-V).
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable Failover Clustering operational log. Alert on CSV ownership changes, redirected I/O mode, and disk health issues. Monitor Perfmon counters for CSV latency.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" ("CSV" OR "Cluster Shared Volume") ("error" OR "redirected" OR "failed")
| table _time host Message
| sort -_time
```

Understanding this SPL

**Cluster Shared Volume Health** — CSV issues can cause VM storage access failures across the entire cluster. Redirected I/O mode significantly degrades performance.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-FailoverClustering/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows` (Hyper-V). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Microsoft-Windows-FailoverClustering/Operational. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Microsoft-Windows-FailoverClustering/Operational". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Cluster Shared Volume Health**): table _time host Message
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status panel per CSV, Events timeline, Table.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Microsoft-Windows-FailoverClustering/Operational" ("CSV" OR "Cluster Shared Volume") ("error" OR "redirected" OR "failed")
| table _time host Message
| sort -_time
```

## Visualization

Status panel per CSV, Events timeline, Table.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
