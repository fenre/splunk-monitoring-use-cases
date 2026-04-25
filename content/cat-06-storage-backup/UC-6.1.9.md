<!-- AUTO-GENERATED from UC-6.1.9.json — DO NOT EDIT -->

---
id: "6.1.9"
title: "Fibre Channel Port Errors"
criticality: "high"
splunkPillar: "Observability"
---

# UC-6.1.9 · Fibre Channel Port Errors

## Description

FC port errors cause storage performance degradation and potential path failovers. Early detection prevents cascading failures.

## Value

FC port errors cause storage performance degradation and potential path failovers. Early detection prevents cascading failures.

## Implementation

Forward FC switch syslog to Splunk. Poll SNMP counters for FC error rates. Alert on error rate exceeding baseline. Correlate with storage latency spikes to identify fabric issues.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP TA, FC switch syslog.
• Ensure the following data sources are available: FC switch logs (Brocade, Cisco MDS), SNMP IF-MIB.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Forward FC switch syslog to Splunk. Poll SNMP counters for FC error rates. Alert on error rate exceeding baseline. Correlate with storage latency spikes to identify fabric issues.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="brocade:syslog" OR sourcetype="cisco:mds"
| search CRC_error OR link_failure OR signal_loss OR sync_loss
| stats count by switch, port, error_type
| where count > 10
```

Understanding this SPL

**Fibre Channel Port Errors** — FC port errors cause storage performance degradation and potential path failovers. Early detection prevents cascading failures.

Documented **Data sources**: FC switch logs (Brocade, Cisco MDS), SNMP IF-MIB. **App/TA** (typical add-on context): SNMP TA, FC switch syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: brocade:syslog, cisco:mds. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="brocade:syslog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Applies an explicit `search` filter to narrow the current result set.
• `stats` rolls up events into metrics; results are split **by switch, port, error_type** so each row reflects one combination of those dimensions.
• Filters the current rows with `where count > 10` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare port and error counters with the switch CLI (`show interface`, `porterrshow`) or DCNM for the same switch, port, and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Table (ports with errors), Bar chart (error counts by type), Timeline (error events).

## SPL

```spl
index=network sourcetype="brocade:syslog" OR sourcetype="cisco:mds"
| search CRC_error OR link_failure OR signal_loss OR sync_loss
| stats count by switch, port, error_type
| where count > 10
```

## Visualization

Table (ports with errors), Bar chart (error counts by type), Timeline (error events).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
