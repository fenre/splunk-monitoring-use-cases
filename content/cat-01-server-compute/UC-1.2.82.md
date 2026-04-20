---
id: "1.2.82"
title: "Credential Guard Status Monitoring"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.82 · Credential Guard Status Monitoring

## Description

Credential Guard protects NTLM hashes and Kerberos tickets in an isolated container. Monitoring ensures it remains enabled and isn't bypassed.

## Value

Credential Guard protects NTLM hashes and Kerberos tickets in an isolated container. Monitoring ensures it remains enabled and isn't bypassed.

## Implementation

Device Guard/Credential Guard Operational log reports VBS (Virtualization Based Security) status. EventCode 13=VBS running with Credential Guard, 14=stopped, 15=not configured. All domain-joined Windows 10/11 and Server 2016+ should have Credential Guard enabled. Alert when any previously-enabled host reports stopped or not configured. Requires UEFI Secure Boot, TPM 2.0, and compatible hardware.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-DeviceGuard/Operational` (EventCode 13, 14, 15).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Device Guard/Credential Guard Operational log reports VBS (Virtualization Based Security) status. EventCode 13=VBS running with Credential Guard, 14=stopped, 15=not configured. All domain-joined Windows 10/11 and Server 2016+ should have Credential Guard enabled. Alert when any previously-enabled host reports stopped or not configured. Requires UEFI Secure Boot, TPM 2.0, and compatible hardware.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-DeviceGuard*"
| stats latest(EventCode) as status by host
| eval cg_status=case(status=13,"Running",status=14,"Stopped",status=15,"Not configured",1=1,"Unknown")
| table host, cg_status
| where cg_status!="Running"
```

Understanding this SPL

**Credential Guard Status Monitoring** — Credential Guard protects NTLM hashes and Kerberos tickets in an isolated container. Monitoring ensures it remains enabled and isn't bypassed.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-DeviceGuard/Operational` (EventCode 13, 14, 15). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **cg_status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Credential Guard Status Monitoring**): table host, cg_status
• Filters the current rows with `where cg_status!="Running"` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

Understanding this CIM / accelerated SPL

**Credential Guard Status Monitoring** — Credential Guard protects NTLM hashes and Kerberos tickets in an isolated container. Monitoring ensures it remains enabled and isn't bypassed.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-DeviceGuard/Operational` (EventCode 13, 14, 15). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (fleet CG status), Table (non-compliant hosts), Single value (% compliant).

## SPL

```spl
index=wineventlog source="WinEventLog:Microsoft-Windows-DeviceGuard*"
| stats latest(EventCode) as status by host
| eval cg_status=case(status=13,"Running",status=14,"Stopped",status=15,"Not configured",1=1,"Unknown")
| table host, cg_status
| where cg_status!="Running"
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

## Visualization

Pie chart (fleet CG status), Table (non-compliant hosts), Single value (% compliant).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
