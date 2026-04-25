<!-- AUTO-GENERATED from UC-5.3.3.json — DO NOT EDIT -->

---
id: "5.3.3"
title: "Connection and Throughput Trending (F5 BIG-IP)"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.3.3 · Connection and Throughput Trending (F5 BIG-IP)

## Description

Reveals application demand patterns. Useful for capacity planning and DDoS detection.

## Value

Reveals application demand patterns. Useful for capacity planning and DDoS detection.

## Implementation

Poll F5 via SNMP or iControl REST for VIP statistics. Baseline patterns and alert on anomalies.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_f5-bigip`, SNMP.
• Ensure the following data sources are available: SNMP F5-BIGIP-LTM-MIB.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll F5 via SNMP or iControl REST for VIP statistics. Baseline patterns and alert on anomalies.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:f5"
| timechart span=5m sum(clientside_curConns) as connections by virtual_server
```

Understanding this SPL

**Connection and Throughput Trending (F5 BIG-IP)** — Reveals application demand patterns. Useful for capacity planning and DDoS detection.

Documented **Data sources**: SNMP F5-BIGIP-LTM-MIB. **App/TA** (typical add-on context): `Splunk_TA_f5-bigip`, SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:f5. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:f5". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `timechart` plots the metric over time using **span=5m** buckets with a separate series **by virtual_server** — ideal for trending and alerting on this use case.


Step 3 — Validate
If you collect SNMP in Splunk, compare the same OIDs, peers, and time range with device graphs in the F5 Configuration utility or third-party NMS for that appliance.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart per VIP, Area chart (throughput), Table.

## SPL

```spl
index=network sourcetype="snmp:f5"
| timechart span=5m sum(clientside_curConns) as connections by virtual_server
```

## Visualization

Line chart per VIP, Area chart (throughput), Table.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
