---
id: "6.1.11"
title: "Isilon Cluster and Node Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-6.1.11 · Isilon Cluster and Node Health

## Description

Dell EMC Isilon (OneFS) is a scale-out NAS platform. Monitoring node and cluster health ensures availability and early detection of hardware or software issues before data access is impacted.

## Value

Dell EMC Isilon (OneFS) is a scale-out NAS platform. Monitoring node and cluster health ensures availability and early detection of hardware or software issues before data access is impacted.

## Implementation

Configure syslog from Isilon cluster to Splunk; optionally use OneFS REST API or vendor TA for node state, drive status, and cluster events. Alert on node down, pool degradation, or OneFS readonly conditions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Add-on for Dell EMC Isilon (if available), or REST/API polling of OneFS platform API, syslog from Isilon nodes.
• Ensure the following data sources are available: OneFS platform API (cluster/node status, events), Isilon syslog, SNMP (if enabled).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure syslog from Isilon cluster to Splunk; optionally use OneFS REST API or vendor TA for node state, drive status, and cluster events. Alert on node down, pool degradation, or OneFS readonly conditions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=storage (sourcetype=isilon:syslog OR sourcetype=isilon:api) (node_down OR cluster_offline OR "degraded" OR "readonly")
| table _time, node, cluster, severity, message
```

Understanding this SPL

**Isilon Cluster and Node Health** — Dell EMC Isilon (OneFS) is a scale-out NAS platform. Monitoring node and cluster health ensures availability and early detection of hardware or software issues before data access is impacted.

Documented **Data sources**: OneFS platform API (cluster/node status, events), Isilon syslog, SNMP (if enabled). **App/TA** (typical add-on context): Splunk Add-on for Dell EMC Isilon (if available), or REST/API polling of OneFS platform API, syslog from Isilon nodes. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: storage; **sourcetype**: isilon:syslog, isilon:api. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=storage, sourcetype=isilon:syslog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Pipeline stage (see **Isilon Cluster and Node Health**): table _time, node, cluster, severity, message


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value (nodes down), Table (node/cluster status), Timeline (health events). Aligns with use cases in Splunk IT Essentials Learn (Storage – Isilon).

## SPL

```spl
index=storage (sourcetype=isilon:syslog OR sourcetype=isilon:api) (node_down OR cluster_offline OR "degraded" OR "readonly")
| table _time, node, cluster, severity, message
```

## Visualization

Single value (nodes down), Table (node/cluster status), Timeline (health events). Aligns with use cases in Splunk IT Essentials Learn (Storage – Isilon).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
