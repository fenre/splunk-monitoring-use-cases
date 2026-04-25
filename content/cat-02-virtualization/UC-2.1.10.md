<!-- AUTO-GENERATED from UC-2.1.10.json — DO NOT EDIT -->

---
id: "2.1.10"
title: "vSAN Health Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.1.10 · vSAN Health Monitoring

## Description

vSAN is the storage fabric for many VMware clusters. Degraded vSAN health can cause VM data loss and cluster-wide outages.

## Value

vSAN is the storage fabric for many VMware clusters. Degraded vSAN health can cause VM data loss and cluster-wide outages.

## Implementation

Splunk_TA_vmware collects vSAN metrics. Also enable vSAN health checks in vCenter. Monitor disk group health, resync progress, and capacity. Alert on any non-green health status.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`, vSAN health service.
• Ensure the following data sources are available: `sourcetype=vmware:perf:vsan`, vSAN health checks.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Splunk_TA_vmware collects vSAN metrics. Also enable vSAN health checks in vCenter. Monitor disk group health, resync progress, and capacity. Alert on any non-green health status.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:perf:vsan"
| stats latest(health_status) as health by cluster, disk_group
| where health!="green"
| table cluster disk_group health
```

Understanding this SPL

**vSAN Health Monitoring** — vSAN is the storage fabric for many VMware clusters. Degraded vSAN health can cause VM data loss and cluster-wide outages.

Documented **Data sources**: `sourcetype=vmware:perf:vsan`, vSAN health checks. **App/TA** (typical add-on context): `Splunk_TA_vmware`, vSAN health service. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:perf:vsan. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:perf:vsan". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by cluster, disk_group** so each row reflects one combination of those dimensions.
• Filters the current rows with `where health!="green"` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **vSAN Health Monitoring**): table cluster disk_group health

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status indicator per cluster, Table of health issues, Gauge (capacity).

## SPL

```spl
index=vmware sourcetype="vmware:perf:vsan"
| stats latest(health_status) as health by cluster, disk_group
| where health!="green"
| table cluster disk_group health
```

## Visualization

Status indicator per cluster, Table of health issues, Gauge (capacity).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
