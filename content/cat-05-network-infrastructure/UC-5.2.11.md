<!-- AUTO-GENERATED from UC-5.2.11.json — DO NOT EDIT -->

---
id: "5.2.11"
title: "Firewall Resource Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.2.11 · Firewall Resource Utilization

## Description

Session table exhaustion blocks new connections. CPU saturation degrades throughput.

## Value

Session table exhaustion blocks new connections. CPU saturation degrades throughput.

## Implementation

Monitor via SNMP (vendor-specific MIB) or system logs. Alert on session table >80%, dataplane CPU >80%.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), SNMP.
• Ensure the following data sources are available: Firewall system resource logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor via SNMP (vendor-specific MIB) or system logs. Alert on session table >80%, dataplane CPU >80%.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=firewall ("session" AND "utilization") OR ("cpu" AND "dataplane")
| timechart span=5m avg(session_utilization) as session_pct by host | where session_pct > 80
```

Understanding this SPL

**Firewall Resource Utilization** — Session table exhaustion blocks new connections. CPU saturation degrades throughput.

Documented **Data sources**: Firewall system resource logs. **App/TA** (typical add-on context): `Splunk_TA_paloalto`, `TA-fortinet_fortigate`, Cisco Secure Firewall Add-on, `Splunk_TA_juniper` (SRX), SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: firewall.

**Pipeline walkthrough**

• Scopes the data: index=firewall. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by host** — ideal for trending and alerting on this use case.
• Filters the current rows with `where session_pct > 80` — typically the threshold or rule expression for this monitoring goal.

Step 3 — Validate
Sample the same time range in your firewall management console, Panorama, FortiManager, or Check Point SmartConsole and confirm that counts, usernames, and object names line up with Splunk.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (session/CPU/memory), Line chart, Table.

## SPL

```spl
index=firewall ("session" AND "utilization") OR ("cpu" AND "dataplane")
| timechart span=5m avg(session_utilization) as session_pct by host | where session_pct > 80
```

## Visualization

Gauge (session/CPU/memory), Line chart, Table.

## References

- [Splunk_TA_paloalto](https://splunkbase.splunk.com/app/2757)
