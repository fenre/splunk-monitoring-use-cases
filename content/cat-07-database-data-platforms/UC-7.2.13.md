---
id: "7.2.13"
title: "MongoDB Atlas Cluster Alerts"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-7.2.13 · MongoDB Atlas Cluster Alerts

## Description

Atlas project alerts (CPU, connections, replication) forwarded to Splunk provide a single pane with on-prem MongoDB. Rapid correlation during incidents.

## Value

Atlas project alerts (CPU, connections, replication) forwarded to Splunk provide a single pane with on-prem MongoDB. Rapid correlation during incidents.

## Implementation

Configure Atlas to send alerts to HTTPS endpoint (Splunk HEC) or poll Alerts API every minute. Normalize fields. Page on CRITICAL OPEN alerts.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: MongoDB Atlas API / Atlas App Services webhook, HEC.
• Ensure the following data sources are available: Atlas alert payloads (clusterId, alertType, status, metric values).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Configure Atlas to send alerts to HTTPS endpoint (Splunk HEC) or poll Alerts API every minute. Normalize fields. Page on CRITICAL OPEN alerts.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=database sourcetype="mongodb:atlas:alert"
| where status="OPEN" OR severity IN ("CRITICAL","WARNING")
| stats latest(_time) as last_alert, values(alertType) as types by cluster_name, project_id
| sort -last_alert
```

Understanding this SPL

**MongoDB Atlas Cluster Alerts** — Atlas project alerts (CPU, connections, replication) forwarded to Splunk provide a single pane with on-prem MongoDB. Rapid correlation during incidents.

Documented **Data sources**: Atlas alert payloads (clusterId, alertType, status, metric values). **App/TA** (typical add-on context): MongoDB Atlas API / Atlas App Services webhook, HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: database; **sourcetype**: mongodb:atlas:alert. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=database, sourcetype="mongodb:atlas:alert". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where status="OPEN" OR severity IN ("CRITICAL","WARNING")` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by cluster_name, project_id** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timeline (Atlas alerts), Table (cluster, alert type, status), Single value (open critical count).

## SPL

```spl
index=database sourcetype="mongodb:atlas:alert"
| where status="OPEN" OR severity IN ("CRITICAL","WARNING")
| stats latest(_time) as last_alert, values(alertType) as types by cluster_name, project_id
| sort -last_alert
```

## Visualization

Timeline (Atlas alerts), Table (cluster, alert type, status), Single value (open critical count).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
