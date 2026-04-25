<!-- AUTO-GENERATED from UC-5.3.9.json — DO NOT EDIT -->

---
id: "5.3.9"
title: "Connection Queue Depth (F5 BIG-IP)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.3.9 · Connection Queue Depth (F5 BIG-IP)

## Description

Growing connection queues indicate backend saturation. Users experience timeouts before the server actually fails.

## Value

Growing connection queues indicate backend saturation. Users experience timeouts before the server actually fails.

## Implementation

Monitor LTM connection queue statistics via iControl REST or SNMP. Alert when queue depth exceeds 0 persistently (>5 min). Correlate with backend pool member health.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler.
• Ensure the following data sources are available: `sourcetype=f5:bigip:ltm`, SNMP.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor LTM connection queue statistics via iControl REST or SNMP. Alert when queue depth exceeds 0 persistently (>5 min). Correlate with backend pool member health.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:ltm"
| stats latest(curConns) as connections, latest(connqDepth) as queue_depth by virtual_server
| where queue_depth > 0 | sort -queue_depth
```

Understanding this SPL

**Connection Queue Depth (F5 BIG-IP)** — Growing connection queues indicate backend saturation. Users experience timeouts before the server actually fails.

Documented **Data sources**: `sourcetype=f5:bigip:ltm`, SNMP. **App/TA** (typical add-on context): F5 TA (`Splunk_TA_f5-bigip`), Splunk_TA_citrix-netscaler. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:ltm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:ltm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by virtual_server** so each row reflects one combination of those dimensions.
• Filters the current rows with `where queue_depth > 0` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Step 3 — Validate
In tmsh or the F5 LTM view, read connection and queue depth for the same virtual server, pool, and slot Splunk is reporting.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (queue depth over time), Table (virtual server, connections, queue), Gauge.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm"
| stats latest(curConns) as connections, latest(connqDepth) as queue_depth by virtual_server
| where queue_depth > 0 | sort -queue_depth
```

## Visualization

Line chart (queue depth over time), Table (virtual server, connections, queue), Gauge.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
