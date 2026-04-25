<!-- AUTO-GENERATED from UC-1.2.37.json — DO NOT EDIT -->

---
id: "1.2.37"
title: "Kerberoasting Detection (SPN Ticket Requests)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.37 · Kerberoasting Detection (SPN Ticket Requests)

## Description

Kerberoasting requests TGS tickets for service accounts with SPNs, then cracks them offline. Detecting anomalous TGS requests catches this before passwords are compromised.

## Value

Kerberoasting is stealthy; statistical views on who asks for which service name separate noise from a hunt lead.

## Implementation

Collect Security logs from all DCs. EventCode 4769 = TGS ticket request. Encryption type 0x17 (RC4) is the Kerberoasting indicator — modern environments should use AES (0x12). Alert when a single user requests RC4 tickets for multiple service SPNs. Exclude machine accounts ($) and krbtgt. Remediation: enforce AES-only on service accounts and use Group Managed Service Accounts (gMSAs).

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Security` (EventCode 4769).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect Security logs from all DCs. EventCode 4769 = TGS ticket request. Encryption type 0x17 (RC4) is the Kerberoasting indicator — modern environments should use AES (0x12). Alert when a single user requests RC4 tickets for multiple service SPNs. Exclude machine accounts ($) and krbtgt. Remediation: enforce AES-only on service accounts and use Group Managed Service Accounts (gMSAs).

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769
  TicketEncryptionType=0x17
  ServiceName!="krbtgt" ServiceName!="*$"
| stats count dc(ServiceName) as unique_spns by TargetUserName, IpAddress
| where unique_spns > 3
| sort -unique_spns
```

Understanding this SPL

**Kerberoasting Detection (SPN Ticket Requests)** — Kerberoasting requests TGS tickets for service accounts with SPNs, then cracks them offline. Detecting anomalous TGS requests catches this before passwords are compromised.

Documented **Data sources**: `sourcetype=WinEventLog:Security` (EventCode 4769). **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog; **sourcetype**: WinEventLog:Security. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog, sourcetype="WinEventLog:Security". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by TargetUserName, IpAddress** so each row reflects one combination of those dimensions.
• Filters the current rows with `where unique_spns > 3` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src span=1h
| where count>0
```

Understanding this CIM / accelerated SPL

CIM tstats is an approximate mirror when Windows TA field extractions and CIM tags are complete. Enable the matching data model acceleration or tstats may return no rows.



Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (suspicious requestors), Bar chart (TGS requests by encryption type), Timeline.

## SPL

```spl
index=wineventlog sourcetype="WinEventLog:Security" EventCode=4769
  TicketEncryptionType=0x17
  ServiceName!="krbtgt" ServiceName!="*$"
| stats count dc(ServiceName) as unique_spns by TargetUserName, IpAddress
| where unique_spns > 3
| sort -unique_spns
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Authentication where nodename=Authentication
  by Authentication.user Authentication.src span=1h
| where count>0
```

## Visualization

Table (suspicious requestors), Bar chart (TGS requests by encryption type), Timeline.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
