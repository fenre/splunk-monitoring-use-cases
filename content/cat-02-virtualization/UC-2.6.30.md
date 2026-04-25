<!-- AUTO-GENERATED from UC-2.6.30.json — DO NOT EDIT -->

---
id: "2.6.30"
title: "MCS Provisioning and Identity Disk Health"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.30 · MCS Provisioning and Identity Disk Health

## Description

MCS relies on correct identity disk creation, image preparation queues, and healthy snapshot or differencing disk chains. Symptoms include rising provisioning task failures, deep snapshot chains, machines stuck in preparation, and mismatches between on-demand and power-managed capacity that stress storage and identity state. Correlating broker and Monitor data with platform metrics isolates whether Citrix, hypervisor, or storage is the bottleneck.

## Value

MCS relies on correct identity disk creation, image preparation queues, and healthy snapshot or differencing disk chains. Symptoms include rising provisioning task failures, deep snapshot chains, machines stuck in preparation, and mismatches between on-demand and power-managed capacity that stress storage and identity state. Correlating broker and Monitor data with platform metrics isolates whether Citrix, hypervisor, or storage is the bottleneck.

## Implementation

Ingest broker provisioning and OData machine rows. Normalize `machine_name`, `catalog_name`, and task outcome fields. For snapshot chain bloat, use hypervisor or storage feeds if available; otherwise track prep duration percentiles. Alert on sustained fail rate, queue depth, or `identity`/`prep` error strings. Segment by delivery group to assign ownership.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Citrix Monitor Service OData API, Template for Citrix XenDesktop 7 (TA-XD7-Broker).
• Ensure the following data sources are available: `sourcetype="citrix:broker:events"`, `sourcetype="citrix:monitor:odata"`, optional VDA and hypervisor indexes.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Map provisioning events and machine inventory fields. Add tagging for on-demand and power-managed delivery groups. If you use Nutanix or VMware linked clones, add relevant inventory or performance inputs for chain depth where supported.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust event_type and field names to your environment):

```spl
index=xd (sourcetype="citrix:broker:events" event_type=Provisioning* OR match(_raw, "(?i)identity|prep|snapshot|MCS|Provision"))
     OR (sourcetype="citrix:monitor:odata" (ODataEntity=Machines OR ODataEntity=Machine) match(_raw, "(?i)identity|disk|provisioning|task"))
| eval fail=if(match(coalesce(result, ProvisioningState, State), "(?i)fail|error") OR match(_raw, "(?i)identity.*(fail|error)|disk.*(fail|error)"), 1, 0)
| bin _time span=15m
| stats count as evts, sum(fail) as fail_cnt, dc(host) as hosts, values(machine_name) as sample_machines by _time, catalog_name, delivery_group
| eval fail_rate=if(evts>0, round(100*fail_cnt/evts,2), 0)
| where fail_cnt>0 OR fail_rate > 5
| table _time, catalog_name, delivery_group, evts, fail_cnt, fail_rate, hosts, sample_machines
```

Step 3 — Validate
Reproduce a failed prep in test and ensure events appear. Tune regex noise from non-MCS subsystems.

Step 4 — Operationalize
Create tiered alerts: warning on sporadic prep fails, major incident on high fail_rate across multiple hosts. Add runbook steps for storage and identity disk recovery.

## SPL

```spl
index=xd (sourcetype="citrix:broker:events" event_type=Provisioning* OR match(_raw, "(?i)identity|prep|snapshot|MCS|Provision"))
     OR (sourcetype="citrix:monitor:odata" (ODataEntity=Machines OR ODataEntity=Machine) match(_raw, "(?i)identity|disk|provisioning|task"))
| eval fail=if(match(coalesce(result, ProvisioningState, State), "(?i)fail|error") OR match(_raw, "(?i)identity.*(fail|error)|disk.*(fail|error)"), 1, 0)
| bin _time span=15m
| stats count as evts, sum(fail) as fail_cnt, dc(host) as hosts, values(machine_name) as sample_machines by _time, catalog_name, delivery_group
| eval fail_rate=if(evts>0, round(100*fail_cnt/evts,2), 0)
| where fail_cnt>0 OR fail_rate > 5
| table _time, catalog_name, delivery_group, evts, fail_cnt, fail_rate, hosts, sample_machines
```

## Visualization

Stacked area (fail count over time by catalog), Table (top failing prep reasons), Bar chart (on-demand vs power-managed pool sizes).

## References

- [Machine Creation Services (Citrix) - Provisioning](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-service/install-configure/mcs.html)
