---
id: "1.2.96"
title: "DNS Server Zone Transfer Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-1.2.96 · DNS Server Zone Transfer Monitoring

## Description

Zone transfers expose the entire DNS namespace to attackers. Unauthorized zone transfers enable reconnaissance and must be detected immediately.

## Value

Zone transfers expose the entire DNS namespace to attackers. Unauthorized zone transfers enable reconnaissance and must be detected immediately.

## Implementation

Enable DNS Server Analytical logging. Track zone transfer events (AXFR/IXFR) and correlate with authorized secondary DNS servers via lookup table. Alert on zone transfers to unauthorized IP addresses. Monitor for AXFR queries from non-DNS-server IPs. This is a high-confidence indicator of DNS reconnaissance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:DNS Server` (EventID 6001, 6002), `sourcetype=MSAD:NT6:DNS`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable DNS Server Analytical logging. Track zone transfer events (AXFR/IXFR) and correlate with authorized secondary DNS servers via lookup table. Alert on zone transfers to unauthorized IP addresses. Monitor for AXFR queries from non-DNS-server IPs. This is a high-confidence indicator of DNS reconnaissance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:DNS Server" EventCode IN (6001, 6002)
| eval TransferType=case(EventCode=6001,"AXFR_Sent", EventCode=6002,"IXFR_Sent", 1=1,"Other")
| table _time, host, Source_Network_Address, Zone, TransferType
| lookup dns_authorized_transfer_partners Source_Network_Address OUTPUT authorized
| where NOT authorized="yes"
```

Understanding this SPL

**DNS Server Zone Transfer Monitoring** — Zone transfers expose the entire DNS namespace to attackers. Unauthorized zone transfers enable reconnaissance and must be detected immediately.

Documented **Data sources**: `sourcetype=WinEventLog:DNS Server` (EventID 6001, 6002), `sourcetype=MSAD:NT6:DNS`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **TransferType** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **DNS Server Zone Transfer Monitoring**): table _time, host, Source_Network_Address, Zone, TransferType
• Enriches events using `lookup` (lookup definition + optional OUTPUT fields).
• Filters the current rows with `where NOT authorized="yes"` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (transfer details), Alert on unauthorized transfers, Geo map (requester IPs).

## SPL

```spl
index=wineventlog source="WinEventLog:DNS Server" EventCode IN (6001, 6002)
| eval TransferType=case(EventCode=6001,"AXFR_Sent", EventCode=6002,"IXFR_Sent", 1=1,"Other")
| table _time, host, Source_Network_Address, Zone, TransferType
| lookup dns_authorized_transfer_partners Source_Network_Address OUTPUT authorized
| where NOT authorized="yes"
```

## Visualization

Table (transfer details), Alert on unauthorized transfers, Geo map (requester IPs).

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
