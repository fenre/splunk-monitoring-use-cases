---
id: "1.2.128"
title: "Service Account Logon Anomalies"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.128 · Service Account Logon Anomalies

## Description

Compromised service accounts grant persistent access and often have elevated privileges. Detecting anomalous service account behavior catches credential theft early.

## Value

Compromised service accounts grant persistent access and often have elevated privileges. Detecting anomalous service account behavior catches credential theft early.

## Implementation

Define a lookup of known service accounts. Service accounts should only log on with Type 5 (Service) or Type 3 (Network) from expected sources. Alert on interactive logons (Type 2/10/11) by service accounts — this indicates credential compromise and human use. Track source IPs and target hosts — service accounts should access a consistent set of systems. Alert on new source IPs or target hosts for any service account.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4624, 4625).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Define a lookup of known service accounts. Service accounts should only log on with Type 5 (Service) or Type 3 (Network) from expected sources. Alert on interactive logons (Type 2/10/11) by service accounts — this indicates credential compromise and human use. Track source IPs and target hosts — service accounts should access a consistent set of systems. Alert on new source IPs or target hosts for any service account.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog EventCode=4624 Logon_Type IN (2, 10, 11)
| lookup service_accounts TargetUserName OUTPUT is_service_account
| where is_service_account="yes"
| eval src=coalesce(Source_Network_Address, IpAddress)
| stats count dc(host) as TargetHosts values(Logon_Type) as LogonTypes by TargetUserName, src
| where LogonTypes!=5 AND LogonTypes!=3
| sort -count
```

Understanding this SPL

**Service Account Logon Anomalies** — Compromised service accounts grant persistent access and often have elevated privileges. Detecting anomalous service account behavior catches credential theft early.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624, 4625). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where is_service_account="yes"` — typically the threshold or rule expression for this monitoring goal.
• `eval` defines or adjusts **src** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by TargetUserName, src** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where LogonTypes!=5 AND LogonTypes!=3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where Authentication.action=failure
  by Authentication.user Authentication.src Authentication.dest span=1h
| where count > 5
```

Understanding this CIM / accelerated SPL

**Service Account Logon Anomalies** — Compromised service accounts grant persistent access and often have elevated privileges. Detecting anomalous service account behavior catches credential theft early.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4624, 4625). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Authentication.Authentication` — enable acceleration for that model.
• Filters the current rows with `where count > 5` — typically the threshold or rule expression for this monitoring goal.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (anomalous logons), Alert on interactive service account logon, Network diagram.

## SPL

```spl
index=wineventlog EventCode=4624 Logon_Type IN (2, 10, 11)
| lookup service_accounts TargetUserName OUTPUT is_service_account
| where is_service_account="yes"
| eval src=coalesce(Source_Network_Address, IpAddress)
| stats count dc(host) as TargetHosts values(Logon_Type) as LogonTypes by TargetUserName, src
| where LogonTypes!=5 AND LogonTypes!=3
| sort -count
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

Table (anomalous logons), Alert on interactive service account logon, Network diagram.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
