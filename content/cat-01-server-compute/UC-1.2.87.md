<!-- AUTO-GENERATED from UC-1.2.87.json — DO NOT EDIT -->

---
id: "1.2.87"
title: "DPAPI Credential Backup (DC)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.87 · DPAPI Credential Backup (DC)

## Description

Data Protection API master key backup to domain controllers enables credential theft. Abnormal DPAPI backup activity from unexpected accounts indicates compromise.

## Value

Bulk or odd DPAPI master-key backup and recovery is how attackers siphon secrets tied to user data. Tight review of 4692/4693 on DCs shortens the window to reset keys and evict a foothold.

## Implementation

EventCode 4692=DPAPI master key backup, 4693=recovery. Normal during user password changes. Alert on mass backup attempts (many keys in short time) or recovery from unexpected admin accounts — indicates SharpDPAPI/Mimikatz DPAPI module usage. Correlate with DCSync events (4662) as attackers often combine both techniques.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4692, 4693).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
EventCode 4692=DPAPI master key backup, 4693=recovery. Normal during user password changes. Alert on mass backup attempts (many keys in short time) or recovery from unexpected admin accounts — indicates SharpDPAPI/Mimikatz DPAPI module usage. Correlate with DCSync events (4662) as attackers often combine both techniques.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4692, 4693)
| eval action=case(EventCode=4692,"DPAPI backup attempted",EventCode=4693,"DPAPI recovery attempted")
| table _time, host, action, SubjectUserName, SubjectDomainName, MasterKeyId
| sort -_time
```

Understanding this SPL

**DPAPI Credential Backup (DC)** — Data Protection API master key backup to domain controllers enables credential theft. Abnormal DPAPI backup activity from unexpected accounts indicates compromise.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4692, 4693). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **action** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **DPAPI Credential Backup (DC)**): table _time, host, action, SubjectUserName, SubjectDomainName, MasterKeyId
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (DPAPI backup/recovery in `Authentication` — confirm field mapping):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  by Authentication.user Authentication.src span=1h
| where count > 5
```

Enable **data model acceleration** on `Authentication`. If EventCode 4692/4693 is not in summaries, the Security log search in Step 2 is authoritative; tag `app=DPAPI` in props for tstats.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (DPAPI events), Single value (recovery count), Timeline, Alert on mass operations.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode IN (4692, 4693)
| eval action=case(EventCode=4692,"DPAPI backup attempted",EventCode=4693,"DPAPI recovery attempted")
| table _time, host, action, SubjectUserName, SubjectDomainName, MasterKeyId
| sort -_time
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where (like(Authentication.app,"%DPAPI%") OR like(Authentication.object,"%4692%") OR like(Authentication.object,"%4693%"))
  by Authentication.user Authentication.src span=1h
| where count > 5
```

## Visualization

Table (DPAPI events), Single value (recovery count), Timeline, Alert on mass operations.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
