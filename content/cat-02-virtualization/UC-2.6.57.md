<!-- AUTO-GENERATED from UC-2.6.57.json — DO NOT EDIT -->

---
id: "2.6.57"
title: "Citrix Cloud Connector Deep Health (HealthData API)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.57 · Citrix Cloud Connector Deep Health (HealthData API)

## Description

Basic connector heartbeats (see UC-2.6.16) prove the service is up; deep health from the HealthData API exposes resource starvation, time drift, failed outbound checks to cloud dependencies, and registration edge cases that still leave the connector process running. These conditions cause intermittent brokering delays, policy refresh gaps, and mysterious registration churn on VDAs. Aggregating API snapshots per connector gives an early, concrete signal to patch, scale out, or fix DNS and TLS paths before a resource location loses effective cloud control.

## Value

Basic connector heartbeats (see UC-2.6.16) prove the service is up; deep health from the HealthData API exposes resource starvation, time drift, failed outbound checks to cloud dependencies, and registration edge cases that still leave the connector process running. These conditions cause intermittent brokering delays, policy refresh gaps, and mysterious registration churn on VDAs. Aggregating API snapshots per connector gives an early, concrete signal to patch, scale out, or fix DNS and TLS paths before a resource location loses effective cloud control.

## Implementation

Deploy a least-privilege scheduled collector on each Cloud Connector (or a shared runner that iterates member hosts) that calls the HealthData API and emits JSON events every one to five minutes. Normalize numeric CPU and map alert flags to a small enum. Create correlation searches that ignore brief CPU spikes under two minutes. Require dual-connector hot-spares: alert when the worst two hosts in a site both show dependency failures. Retain 30 days of history for post-incident review. Co-watch with 2.6.16 so disconnections and deep health anomalies appear on one dashboard.

## Detailed Implementation

Prerequisites
• Cloud Connector version supported for HealthData-style health exports; service account with rights to read local health endpoints if applicable.
• `index=xd` receiving `citrix:cloudconnector:healthdata` with stable host, connector_id, and resource_location keys.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Implement the scripted input or lightweight agent that calls the health endpoint and posts one line per snapshot. Verify clocks on collectors match domain time for meaningful NTP fields.

Step 2 — Create the search and alert
Triage with the primary SPL, then add suppressions for maintenance windows. Pair alerts with the simpler connectivity search from 2.6.16 to avoid duplicate pages for the same outage.

Step 3 — Validate
Induce a controlled outbound block in a lab and confirm failed dependency fields populate. Skew a VM clock in test and assert time_sync flips not OK.

Step 4 — Operationalize
Document escalation from connector host OS health to this deep health, and add capacity playbooks when CPU stays above threshold across polling windows.

## SPL

```spl
index=xd sourcetype="citrix:cloudconnector:healthdata"
| eval reg_ok=if(match(lower(coalesce(cloud_registration, registration_status, "")), "(registered|ok|success)"), 1, 0)
| eval sync_ok=if(match(lower(coalesce(time_sync_status, ntp_status, "")), "(synced|ok|in\ssync)"), 1, 0)
| eval dep_ok=if(tonumber(coalesce(failed_outbound, failed_dependencies, 0))=0, 1, 0)
| eval cpu=tonumber(coalesce(cpu_percent, cpu, 0))
| where reg_ok=0 OR sync_ok=0 OR dep_ok=0 OR cpu>90 OR like(lower(coalesce(alert_state, health_alert, "")), "%fail%") OR like(lower(coalesce(alert_state, health_alert, "")), "%error%")
| stats latest(cpu) as cpu_pct, latest(alert_state) as alert_state, latest(cloud_registration) as registration, latest(time_sync_status) as time_sync, max(failed_outbound) as failed_deps by host, connector_id, resource_location
| sort - cpu_pct
```

## Visualization

Connector matrix (CPU, registration, NTP, dependency failures); sparklines of failed outbound tests; overlay with VDA registration errors in the same resource location.

## References

- [Citrix Cloud Connector — system and connectivity requirements](https://docs.citrix.com/en-us/citrix-cloud/citrix-cloud-resource-locations/citrix-cloud-connector-installation.html)
- [Cloud Connector advanced functionality (troubleshooting context)](https://docs.citrix.com/en-us/citrix-cloud/citrix-cloud-resource-locations/connector-technical-details.html)
