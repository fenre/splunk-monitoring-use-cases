---
id: "1.2.92"
title: "Remote Desktop Gateway Session Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-1.2.92 · Remote Desktop Gateway Session Monitoring

## Description

RD Gateway is the entry point for remote workers. Monitoring session lifecycle detects unauthorized access, session hijacking, and resource abuse.

## Value

RD Gateway is the entry point for remote workers. Monitoring session lifecycle detects unauthorized access, session hijacking, and resource abuse.

## Implementation

Collect RD Gateway Operational logs. Track connection (300), disconnect (302), authentication failures (303), and authorization failures (304). Alert on brute-force patterns (multiple 303s from same IP), connections from unusual geolocations, and access to unauthorized resources. Monitor session duration for anomalies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect RD Gateway Operational logs. Track connection (300), disconnect (302), authentication failures (303), and authorization failures (304). Alert on brute-force patterns (multiple 303s from same IP), connections from unusual geolocations, and access to unauthorized resources. Monitor session duration for anomalies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational"
| eval EventAction=case(EventCode=300,"Connected", EventCode=302,"Disconnected", EventCode=303,"AuthFailed", EventCode=304,"AuthZ_Failed", 1=1,"Other")
| stats count by host, UserName, ClientIP, ResourceName, EventAction
| where EventAction="AuthFailed" OR EventAction="AuthZ_Failed"
```

Understanding this SPL

**Remote Desktop Gateway Session Monitoring** — RD Gateway is the entry point for remote workers. Monitoring session lifecycle detects unauthorized access, session hijacking, and resource abuse.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **EventAction** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, UserName, ClientIP, ResourceName, EventAction** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where EventAction="AuthFailed" OR EventAction="AuthZ_Failed"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Geo map (client IPs), Table (session details), Timechart (connections by hour).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-TerminalServices-Gateway/Operational"
| eval EventAction=case(EventCode=300,"Connected", EventCode=302,"Disconnected", EventCode=303,"AuthFailed", EventCode=304,"AuthZ_Failed", 1=1,"Other")
| stats count by host, UserName, ClientIP, ResourceName, EventAction
| where EventAction="AuthFailed" OR EventAction="AuthZ_Failed"
```

## Visualization

Geo map (client IPs), Table (session details), Timechart (connections by hour).

## References

- [Collect RD Gateway Operational logs. Track connection](https://splunkbase.splunk.com/app/300)
