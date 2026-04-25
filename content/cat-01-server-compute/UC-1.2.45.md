<!-- AUTO-GENERATED from UC-1.2.45.json — DO NOT EDIT -->

---
id: "1.2.45"
title: "Windows Time Service (W32Time) Issues"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.2.45 · Windows Time Service (W32Time) Issues

## Description

Time synchronization failures break Kerberos authentication (5-minute tolerance), cause log correlation issues, and invalidate audit trails.

## Value

Time drift is a silent multiplier for auth, PKI, and correlation—treat it as infrastructure health, not a footnote.

## Implementation

W32Time events log automatically. EventCode 129=NTP server unreachable, 134=time difference >5 seconds (Kerberos risk), 142=time service stopped, 36=not synced in 24 hours. Domain-joined machines sync to DC; DCs sync to PDC emulator; PDC syncs to external NTP. Alert on any DC time sync failures (Kerberos impact). Monitor non-DC servers for EventCode 36.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service, EventCode 129, 134, 142, 36).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
W32Time events log automatically. EventCode 129=NTP server unreachable, 134=time difference >5 seconds (Kerberos risk), 142=time service stopped, 36=not synced in 24 hours. Domain-joined machines sync to DC; DCs sync to PDC emulator; PDC syncs to external NTP. Alert on any DC time sync failures (Kerberos impact). Monitor non-DC servers for EventCode 36.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Microsoft-Windows-Time-Service"
  EventCode IN (129, 134, 142, 36)
| eval issue=case(EventCode=129,"NTP unreachable",EventCode=134,"Time difference too large",EventCode=142,"Time service stopped",EventCode=36,"Time not synced for 24h")
| table _time, host, issue, EventCode
| sort -_time
```

Understanding this SPL

**Windows Time Service (W32Time) Issues** — Time synchronization failures break Kerberos authentication (5-minute tolerance), cause log correlation issues, and invalidate audit trails.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service, EventCode 129, 134, 142, 36). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:System. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:System". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **issue** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Windows Time Service (W32Time) Issues**): table _time, host, issue, EventCode
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

**Windows Time Service (W32Time) Issues** — Time synchronization failures break Kerberos authentication (5-minute tolerance), cause log correlation issues, and invalidate audit trails.

Documented **Data sources**: `sourcetype=WinEventLog:System` (Source=Microsoft-Windows-Time-Service, EventCode 129, 134, 142, 36). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (time sync issues), Status grid (host × sync status), Single value (unsynced hosts).

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:System" Source="Microsoft-Windows-Time-Service"
  EventCode IN (129, 134, 142, 36)
| eval issue=case(EventCode=129,"NTP unreachable",EventCode=134,"Time difference too large",EventCode=142,"Time service stopped",EventCode=36,"Time not synced for 24h")
| table _time, host, issue, EventCode
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Change where nodename=Change.All_Changes
  by All_Changes.dest span=1h
| where count>0
```

## Visualization

Table (time sync issues), Status grid (host × sync status), Single value (unsynced hosts).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
