---
id: "5.5.18"
title: "vManage Cluster Health"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.5.18 · vManage Cluster Health

## Description

vManage is the single management plane for the entire SD-WAN fabric. If the vManage cluster is unhealthy — high CPU, disk full, database replication lag, or services down — operators lose visibility and policy push capability across all sites.

## Value

vManage is the single management plane for the entire SD-WAN fabric. If the vManage cluster is unhealthy — high CPU, disk full, database replication lag, or services down — operators lose visibility and policy push capability across all sites.

## Implementation

Poll vManage cluster health API. Monitor CPU, memory, disk usage, NMS database replication status, and running services. For clustered deployments, verify all nodes are in sync. Alert when any node exceeds 70% CPU, 80% memory, or 75% disk, or when database replication falls behind. Schedule regular config database backups independently.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API.
• Ensure the following data sources are available: vManage cluster status API, `sourcetype=cisco:sdwan:vmanage`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll vManage cluster health API. Monitor CPU, memory, disk usage, NMS database replication status, and running services. For clustered deployments, verify all nodes are in sync. Alert when any node exceeds 70% CPU, 80% memory, or 75% disk, or when database replication falls behind. Schedule regular config database backups independently.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=sdwan sourcetype="cisco:sdwan:vmanage"
| stats latest(cpu_load) as cpu, latest(mem_util) as mem_pct, latest(disk_util) as disk_pct, latest(db_status) as db_status, latest(services_running) as services by vmanage_ip
| where cpu > 70 OR mem_pct > 80 OR disk_pct > 75 OR db_status!="healthy"
| table vmanage_ip cpu mem_pct disk_pct db_status services
```

Understanding this SPL

**vManage Cluster Health** — vManage is the single management plane for the entire SD-WAN fabric. If the vManage cluster is unhealthy — high CPU, disk full, database replication lag, or services down — operators lose visibility and policy push capability across all sites.

Documented **Data sources**: vManage cluster status API, `sourcetype=cisco:sdwan:vmanage`. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), vManage API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: sdwan; **sourcetype**: cisco:sdwan:vmanage. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=sdwan, sourcetype="cisco:sdwan:vmanage". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vmanage_ip** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where cpu > 70 OR mem_pct > 80 OR disk_pct > 75 OR db_status!="healthy"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **vManage Cluster Health**): table vmanage_ip cpu mem_pct disk_pct db_status services


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Single value panels (CPU, memory, disk per node), Status indicator (cluster health), Table (services status).

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:vmanage"
| stats latest(cpu_load) as cpu, latest(mem_util) as mem_pct, latest(disk_util) as disk_pct, latest(db_status) as db_status, latest(services_running) as services by vmanage_ip
| where cpu > 70 OR mem_pct > 80 OR disk_pct > 75 OR db_status!="healthy"
| table vmanage_ip cpu mem_pct disk_pct db_status services
```

## Visualization

Single value panels (CPU, memory, disk per node), Status indicator (cluster health), Table (services status).

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
