<!-- AUTO-GENERATED from UC-6.1.28.json — DO NOT EDIT -->

---
id: "6.1.28"
title: "MDS Slow Drain Detection"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.28 · MDS Slow Drain Detection

## Description

Slow drain occurs when a target device (storage or host) cannot accept frames fast enough, exhausting buffer-to-buffer credits and stalling the entire FC path. A single slow-drain device can impact hundreds of hosts sharing the same ISL. Early detection via TxWait and B2B credit metrics is essential.

## Value

Slow drain occurs when a target device (storage or host) cannot accept frames fast enough, exhausting buffer-to-buffer credits and stalling the entire FC path. A single slow-drain device can impact hundreds of hosts sharing the same ISL. Early detection via TxWait and B2B credit metrics is essential.

## Implementation

Enable port-monitor policies on MDS switches with appropriate TxWait thresholds. Forward syslog to Splunk. Poll SNMP slow-drain counters. Alert immediately on sustained TxWait. Cross-reference with FLOGI database (UC-6.1.30) to identify the offending host or storage port.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `cisco:mds` syslog, SNMP TA, Cisco DC Networking Application (Splunkbase 7777).
• Ensure the following data sources are available: MDS syslog (PORT-MONITOR, SLOW-DRAIN events), SNMP counters (TxWait, B2B credit zeros).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable port-monitor policies on MDS switches with appropriate TxWait thresholds. Forward syslog to Splunk. Poll SNMP slow-drain counters. Alert immediately on sustained TxWait. Cross-reference with FLOGI database (UC-6.1.30) to identify the offending host or storage port.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:mds" "SLOW_DRAIN" OR "PORT-5-IF_TXWAIT" OR "PORT-MONITOR"
| rex "port (?<port>\S+).*txwait=(?<txwait>\d+)"
| stats max(txwait) as max_txwait count by switch, port, _time
| where max_txwait > 100
| sort -max_txwait
```

Understanding this SPL

**MDS Slow Drain Detection** — Slow drain occurs when a target device (storage or host) cannot accept frames fast enough, exhausting buffer-to-buffer credits and stalling the entire FC path. A single slow-drain device can impact hundreds of hosts sharing the same ISL. Early detection via TxWait and B2B credit metrics is essential.

Documented **Data sources**: MDS syslog (PORT-MONITOR, SLOW-DRAIN events), SNMP counters (TxWait, B2B credit zeros). **App/TA** (typical add-on context): `cisco:mds` syslog, SNMP TA, Cisco DC Networking Application (Splunkbase 7777). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:mds. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:mds". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `stats` rolls up events into metrics; results are split **by switch, port, _time** so each row reflects one combination of those dimensions.
• Filters the current rows with `where max_txwait > 100` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Compare port and error counters with the switch CLI (`show interface`, `porterrshow`) or DCNM for the same switch, port, and interval.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Point on-call to the ONTAP or array runbook, Cisco SAN references, and SNMP/REST credentials already used in production—not generic platform steps only. Consider visualizations: Table (ports with slow drain), Line chart (TxWait over time), Topology (affected path highlighting).

## SPL

```spl
index=network sourcetype="cisco:mds" "SLOW_DRAIN" OR "PORT-5-IF_TXWAIT" OR "PORT-MONITOR"
| rex "port (?<port>\S+).*txwait=(?<txwait>\d+)"
| stats max(txwait) as max_txwait count by switch, port, _time
| where max_txwait > 100
| sort -max_txwait
```

## Visualization

Table (ports with slow drain), Line chart (TxWait over time), Topology (affected path highlighting).

## References

- [Cisco DC Networking Application](https://splunkbase.splunk.com/app/7777)
