<!-- AUTO-GENERATED from UC-1.2.67.json — DO NOT EDIT -->

---
id: "1.2.67"
title: "Golden Ticket Detection (TGT Anomalies)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.67 · Golden Ticket Detection (TGT Anomalies)

## Description

Golden tickets are forged Kerberos TGTs that grant domain-wide access. Detecting anomalous TGT properties catches this catastrophic compromise.

## Value

Domain-wide access from a forged ticket is one of the worst cases for Active Directory. Early signals on odd Kerberos TGT patterns buy time to reset KRBTGT and contain attackers.

## Implementation

Golden tickets typically use RC4 encryption (0x17) with abnormally long lifetimes (default Kerberos max is 10 hours). EventCode 4768=TGT request, 4769=TGS request. Detect TGS requests referencing TGTs older than 10 hours, or TGT requests with RC4 in environments that enforce AES. Also monitor for EventCode 4769 with services accessed that the user normally doesn't touch. Requires KRBTGT password rotation as remediation.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4768, 4769).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Golden tickets typically use RC4 encryption (0x17) with abnormally long lifetimes (default Kerberos max is 10 hours). EventCode 4768=TGT request, 4769=TGS request. Detect TGS requests referencing TGTs older than 10 hours, or TGT requests with RC4 in environments that enforce AES. Also monitor for EventCode 4769 with services accessed that the user normally doesn't touch. Requires KRBTGT password rotation as remediation.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4768 TicketEncryptionType=0x17
| stats count by TargetUserName, IpAddress
```

Understanding this SPL

**Golden Ticket Detection (TGT Anomalies)** — Golden tickets are forged Kerberos TGTs that grant domain-wide access. Detecting anomalous TGT properties catches this catastrophic compromise.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4768, 4769). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by TargetUserName, IpAddress** so each row reflects one combination of those dimensions.

Optional CIM / accelerated variant (maps `TicketEncryptionType=0x17` to `Authentication.signature` when Windows Security events are CIM-tagged):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where (Authentication.signature="0x17" OR Authentication.signature="23")
  by Authentication.user Authentication.src span=1h
| where count > 0
```

Enable **data model acceleration** on `Authentication`. If signatures are empty, keep the primary `WinEventLog:Security` search—field aliasing for `TicketEncryptionType` may be required.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (anomalous ticket requests), Timeline, Single value (RC4 TGT count), Alert.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4768 TicketEncryptionType=0x17
| stats count by TargetUserName, IpAddress
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication.Authentication
  where (Authentication.signature="0x17" OR Authentication.signature="23")
  by Authentication.user Authentication.src span=1h
| where count > 0
```

## Visualization

Table (anomalous ticket requests), Timeline, Single value (RC4 TGT count), Alert.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Authentication](https://docs.splunk.com/Documentation/CIM/latest/User/Authentication)
