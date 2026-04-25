<!-- AUTO-GENERATED from UC-1.2.109.json — DO NOT EDIT -->

---
id: "1.2.109"
title: "Windows Time Service (W32Time) Drift"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.109 · Windows Time Service (W32Time) Drift

## Description

Kerberos authentication fails when clock skew exceeds 5 minutes. Time drift breaks authentication, log correlation, and forensic timelines.

## Value

Clock skew breaks Kerberos and TLS in hard-to-debug ways. Tracking w32time stability on member servers and DCs avoids mystery auth failures and duplicate log entries across the estate.

## Implementation

Monitor W32Time events for time provider errors (134), skew warnings (142), and NTP unreachable (129). On DCs, the PDC Emulator must sync to an external NTP source — all other DCs sync to the domain hierarchy. Alert on any DC time skew >2 minutes. Monitor w32tm /query /status output via scripted input for continuous drift tracking. Time-critical for Kerberos (5-min max skew) and forensic log correlation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor W32Time events for time provider errors (134), skew warnings (142), and NTP unreachable (129). On DCs, the PDC Emulator must sync to an external NTP source — all other DCs sync to the domain hierarchy. Alert on any DC time skew >2 minutes. Monitor w32tm /query /status output via scripted input for continuous drift tracking. Time-critical for Kerberos (5-min max skew) and forensic log correlation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:System" SourceName="Microsoft-Windows-Time-Service" EventCode IN (134, 142, 129)
| eval Issue=case(EventCode=134,"Time_Provider_Error", EventCode=142,"Time_Skew_Too_Large", EventCode=129,"NTP_Unreachable", 1=1,"Warning")
| stats count latest(_time) as LastSeen by host, Issue, EventCode
| sort -count
```

Understanding this SPL

**Windows Time Service (W32Time) Drift** — Kerberos authentication fails when clock skew exceeds 5 minutes. Time drift breaks authentication, log correlation, and forensic timelines.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Issue** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, Issue, EventCode** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

Understanding this CIM / accelerated SPL

**Windows Time Service (W32Time) Drift** — Kerberos authentication fails when clock skew exceeds 5 minutes. Time drift breaks authentication, log correlation, and forensic timelines.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (time offset), Table (time errors), Alert on >2min drift.

Scripted input (generic example)
This use case relies on a scripted input. In the app's local/inputs.conf add a stanza such as:

```ini
[script://$SPLUNK_HOME/etc/apps/YourApp/bin/collect.sh]
interval = 300
sourcetype = your_sourcetype
index = main
disabled = 0
```

The script should print one event per line (e.g. key=value). Example minimal script (bash):

```bash
#!/usr/bin/env bash
# Output metrics or events, one per line
echo "metric=value timestamp=$(date +%s)"
```

For full details (paths, scheduling, permissions), see the Implementation guide: docs/implementation-guide.md

## SPL

```spl
index=wineventlog source="WinEventLog:System" SourceName="Microsoft-Windows-Time-Service" EventCode IN (134, 142, 129)
| eval Issue=case(EventCode=134,"Time_Provider_Error", EventCode=142,"Time_Skew_Too_Large", EventCode=129,"NTP_Unreachable", 1=1,"Warning")
| stats count latest(_time) as LastSeen by host, Issue, EventCode
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change.All_Changes
  by All_Changes.user All_Changes.dest span=1h
| where count > 0
```

## Visualization

Timechart (time offset), Table (time errors), Alert on >2min drift.

## References

- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
