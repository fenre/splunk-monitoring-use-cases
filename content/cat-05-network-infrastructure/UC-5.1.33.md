---
id: "5.1.33"
title: "Half-Duplex Negotiation Anomaly"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.33 · Half-Duplex Negotiation Anomaly

## Description

Half/full duplex mismatches causing performance degradation.

## Value

Half/full duplex mismatches causing performance degradation.

## Implementation

Poll EtherLike-MIB dot3StatsDuplexStatus; ingest syslog for duplex mismatch messages. Alert on half-duplex on gigabit uplinks or explicit mismatch events.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: IF-MIB (ifSpeed), EtherLike-MIB (dot3StatsDuplexStatus), syslog.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll EtherLike-MIB dot3StatsDuplexStatus; ingest syslog for duplex mismatch messages. Alert on half-duplex on gigabit uplinks or explicit mismatch events.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network (sourcetype=snmp:interface OR sourcetype="cisco:ios") ("duplex" OR "Duplex" OR "dot3StatsDuplexStatus" OR "halfDuplex" OR "fullDuplex")
| rex "duplex mismatch|(?<duplex_status>halfDuplex|fullDuplex|unknown)"
| where match(_raw,"mismatch|halfDuplex") OR duplex_status="halfDuplex"
| stats count by host, ifDescr, duplex_status
| table host ifDescr duplex_status count
```

Understanding this SPL

**Half-Duplex Negotiation Anomaly** — Half/full duplex mismatches causing performance degradation.

Documented **Data sources**: IF-MIB (ifSpeed), EtherLike-MIB (dot3StatsDuplexStatus), syslog. **App/TA** (typical add-on context): SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:interface, cisco:ios. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:interface. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• Filters the current rows with `where match(_raw,"mismatch|halfDuplex") OR duplex_status="halfDuplex"` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host, ifDescr, duplex_status** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **Half-Duplex Negotiation Anomaly**): table host ifDescr duplex_status count


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (host, interface, duplex), Status grid, Single value.

## SPL

```spl
index=network (sourcetype=snmp:interface OR sourcetype="cisco:ios") ("duplex" OR "Duplex" OR "dot3StatsDuplexStatus" OR "halfDuplex" OR "fullDuplex")
| rex "duplex mismatch|(?<duplex_status>halfDuplex|fullDuplex|unknown)"
| where match(_raw,"mismatch|halfDuplex") OR duplex_status="halfDuplex"
| stats count by host, ifDescr, duplex_status
| table host ifDescr duplex_status count
```

## Visualization

Table (host, interface, duplex), Status grid, Single value.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
