---
id: "8.6.19"
title: "SNMP Community String Audit"
criticality: "high"
splunkPillar: "Security"
---

# UC-8.6.19 · SNMP Community String Audit

## Description

Detects use of default `public`/`private` or unauthorized SNMP GETs to network devices for SNMPv2c exposure auditing.

## Value

Detects use of default `public`/`private` or unauthorized SNMP GETs to network devices for SNMPv2c exposure auditing.

## Implementation

Forward snmpd auth failures. Alert on default community strings in use or brute-force patterns. Migrate devices to SNMPv3.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Device syslog, SNMP proxy audit.
• Ensure the following data sources are available: `snmpd` auth failures, `community` in trap receiver logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward snmpd auth failures. Alert on default community strings in use or brute-force patterns. Migrate devices to SNMPv3.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:audit" OR (sourcetype=syslog process=snmpd)
| search "Authentication failed" OR community="public" OR community="private"
| stats count by src, device, community
| where count > 10
```

Understanding this SPL

**SNMP Community String Audit** — Detects use of default `public`/`private` or unauthorized SNMP GETs to network devices for SNMPv2c exposure auditing.

Documented **Data sources**: `snmpd` auth failures, `community` in trap receiver logs. **App/TA** (typical add-on context): Device syslog, SNMP proxy audit. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:audit, syslog. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:audit". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by src, device, community** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (src, device, community), Bar chart (failures by device), Line chart (auth failure rate).

## SPL

```spl
index=network sourcetype="snmp:audit" OR (sourcetype=syslog process=snmpd)
| search "Authentication failed" OR community="public" OR community="private"
| stats count by src, device, community
| where count > 10
```

## Visualization

Table (src, device, community), Bar chart (failures by device), Line chart (auth failure rate).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
