---
id: "8.1.13"
title: "IIS Worker Process Recycling"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.13 · IIS Worker Process Recycling

## Description

Frequent `w3wp` recycles cause session loss and latency spikes. Event Log IDs 5074, 5002, 1011 indicate config, memory, or crash-driven recycles.

## Value

Frequent `w3wp` recycles cause session loss and latency spikes. Event Log IDs 5074, 5002, 1011 indicate config, memory, or crash-driven recycles.

## Implementation

Enable WAS/W3SVC auditing. Alert when recycles per app pool exceed baseline. Correlate with private bytes and GC from perfmon.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: System/Application Event Log (WAS, W3SVC).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable WAS/W3SVC auditing. Alert when recycles per app pool exceed baseline. Correlate with private bytes and GC from perfmon.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" SourceName=WAS EventCode=5074
| bucket _time span=5m
| stats count as recycles by ComputerName, AppPoolName, _time
| where recycles > 3
```

Understanding this SPL

**IIS Worker Process Recycling** — Frequent `w3wp` recycles cause session loss and latency spikes. Event Log IDs 5074, 5002, 1011 indicate config, memory, or crash-driven recycles.

Documented **Data sources**: System/Application Event Log (WAS, W3SVC). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by ComputerName, AppPoolName, _time** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where recycles > 3` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - count
```

Understanding this CIM / accelerated SPL

**IIS Worker Process Recycling** — Frequent `w3wp` recycles cause session loss and latency spikes. Event Log IDs 5074, 5002, 1011 indicate config, memory, or crash-driven recycles.

Documented **Data sources**: System/Application Event Log (WAS, W3SVC). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (recycle events), Table (app pool, recycle count), Line chart (recycles per hour).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" SourceName=WAS EventCode=5074
| bucket _time span=5m
| stats count as recycles by ComputerName, AppPoolName, _time
| where recycles > 3
```

## CIM SPL

```spl
| tstats summariesonly=t count from datamodel=Web.Web by Web.status, Web.http_method, Web.dest | sort - count
```

## Visualization

Timeline (recycle events), Table (app pool, recycle count), Line chart (recycles per hour).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
