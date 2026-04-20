---
id: "6.4.12"
title: "DFS Replication Backlog and Connectivity Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.4.12 · DFS Replication Backlog and Connectivity Health

## Description

Backlog size and partner connectivity state predict replication stalls before user-visible file divergence. Complements event-only monitoring with quantitative backlog trending.

## Value

Backlog size and partner connectivity state predict replication stalls before user-visible file divergence. Complements event-only monitoring with quantitative backlog trending.

## Implementation

Ingest backlog count from PowerShell `Get-DfsrState` or scheduled dfsrdiag output every 15m. Alert on rising backlog trend or disconnected partners.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`, scripted `dfsrdiag` / WMI.
• Ensure the following data sources are available: DFS-R backlog metrics per replicated folder, Event ID 4012/5002.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest backlog count from PowerShell `Get-DfsrState` or scheduled dfsrdiag output every 15m. Alert on rising backlog trend or disconnected partners.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage sourcetype="dfsr:backlog"
| where backlog_files > 100 OR connected=0
| timechart span=15m max(backlog_files) as backlog by replication_group, member
| where backlog > 500
```

Understanding this SPL

**DFS Replication Backlog and Connectivity Health** — Backlog size and partner connectivity state predict replication stalls before user-visible file divergence. Complements event-only monitoring with quantitative backlog trending.

Documented **Data sources**: DFS-R backlog metrics per replicated folder, Event ID 4012/5002. **App/TA** (typical add-on context): `Splunk_TA_windows`, scripted `dfsrdiag` / WMI. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: dfsr:backlog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype="dfsr:backlog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where backlog_files > 100 OR connected=0` — typically the threshold or rule expression for this monitoring goal.
• `timechart` plots the metric over time using **span=15m** buckets with a separate series **by replication_group, member** — ideal for trending and alerting on this use case.
• Filters the current rows with `where backlog > 500` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (backlog files over time), Table (RG, member, backlog), Single value (max backlog).

## SPL

```spl
index=storage sourcetype="dfsr:backlog"
| where backlog_files > 100 OR connected=0
| timechart span=15m max(backlog_files) as backlog by replication_group, member
| where backlog > 500
```

## Visualization

Line chart (backlog files over time), Table (RG, member, backlog), Single value (max backlog).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
