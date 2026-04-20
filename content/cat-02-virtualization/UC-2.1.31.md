---
id: "2.1.31"
title: "Fault Tolerance Status and Replication Lag"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.1.31 · Fault Tolerance Status and Replication Lag

## Description

VMware Fault Tolerance provides zero-downtime protection by maintaining a live secondary copy of a VM. If FT replication falls behind or becomes disabled, the VM loses its zero-downtime protection. FT lag indicates network bandwidth or CPU contention on the secondary host.

## Value

VMware Fault Tolerance provides zero-downtime protection by maintaining a live secondary copy of a VM. If FT replication falls behind or becomes disabled, the VM loses its zero-downtime protection. FT lag indicates network bandwidth or CPU contention on the secondary host.

## Implementation

Collect VM inventory and events via Splunk_TA_vmware. Monitor FT state changes (enabled, disabled, failover occurred). Alert when FT is disabled on a protected VM or when FT failover events occur. Track FT vMotion log latency counters to detect replication lag.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_vmware`.
• Ensure the following data sources are available: `sourcetype=vmware:inv:vm`, `sourcetype=vmware:events`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect VM inventory and events via Splunk_TA_vmware. Monitor FT state changes (enabled, disabled, failover occurred). Alert when FT is disabled on a protected VM or when FT failover events occur. Track FT vMotion log latency counters to detect replication lag.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=vmware sourcetype="vmware:inv:vm" ftInfo_role=*
| stats latest(ftInfo_role) as ft_role, latest(ftInfo_instanceUuid) as ft_pair by vm_name, host
| eval ft_status=if(isnotnull(ft_role), ft_role, "Not Configured")
| table vm_name, host, ft_status, ft_pair
| append [search index=vmware sourcetype="vmware:events" event_type="*FaultTolerance*" | stats count by event_type, vm_name | table event_type, vm_name, count]
```

Understanding this SPL

**Fault Tolerance Status and Replication Lag** — VMware Fault Tolerance provides zero-downtime protection by maintaining a live secondary copy of a VM. If FT replication falls behind or becomes disabled, the VM loses its zero-downtime protection. FT lag indicates network bandwidth or CPU contention on the secondary host.

Documented **Data sources**: `sourcetype=vmware:inv:vm`, `sourcetype=vmware:events`. **App/TA** (typical add-on context): `Splunk_TA_vmware`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: vmware; **sourcetype**: vmware:inv:vm. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=vmware, sourcetype="vmware:inv:vm". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by vm_name, host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **ft_status** — often to normalize units, derive a ratio, or prepare for thresholds.
• Pipeline stage (see **Fault Tolerance Status and Replication Lag**): table vm_name, host, ft_status, ft_pair
• Appends rows from a subsearch with `append`.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Status grid (FT-protected VMs), Events timeline (FT state changes), Table (FT configuration).

## SPL

```spl
index=vmware sourcetype="vmware:inv:vm" ftInfo_role=*
| stats latest(ftInfo_role) as ft_role, latest(ftInfo_instanceUuid) as ft_pair by vm_name, host
| eval ft_status=if(isnotnull(ft_role), ft_role, "Not Configured")
| table vm_name, host, ft_status, ft_pair
| append [search index=vmware sourcetype="vmware:events" event_type="*FaultTolerance*" | stats count by event_type, vm_name | table event_type, vm_name, count]
```

## Visualization

Status grid (FT-protected VMs), Events timeline (FT state changes), Table (FT configuration).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
