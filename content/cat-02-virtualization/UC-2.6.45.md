<!-- AUTO-GENERATED from UC-2.6.45.json — DO NOT EDIT -->

---
id: "2.6.45"
title: "Machine Boot Storm Detection and Mitigation"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.45 · Machine Boot Storm Detection and Mitigation

## Description

A boot storm is a sudden, correlated surge of machine start and registration activity — for example at shift change or after maintenance — that can flood the hypervisor, storage, and broker queues. It causes long queue times, failed registrations, and slow logon even when per-machine health is good. You need a detection that works on the rate of starts per minute per catalog and delivery group, not only on a static machine count, plus a view of whether staggered start configurations are honored. The goal is to trigger proactive throttling, schedule spreading, and communications before users pile into failures.

## Value

A boot storm is a sudden, correlated surge of machine start and registration activity — for example at shift change or after maintenance — that can flood the hypervisor, storage, and broker queues. It causes long queue times, failed registrations, and slow logon even when per-machine health is good. You need a detection that works on the rate of starts per minute per catalog and delivery group, not only on a static machine count, plus a view of whether staggered start configurations are honored. The goal is to trigger proactive throttling, schedule spreading, and communications before users pile into failures.

## Implementation

Ingest broker events with consistent `machine_name`, `catalog_name`, and `delivery_group` fields. Set absolute thresholds (e.g. more than 20 unique machines starting per minute) and relative thresholds (Z-score on the per-catalog rate versus the same time-of-day baseline). Add a secondary search that lists scheduled start tags or autoscale events if you model them. Integrate the alert with power-management policy owners so they can lengthen stagger windows or cap concurrent power operations. For proof, compare to hypervisor CPU ready time and storage latency dashboards.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (`TA-XD7-Broker`); optional uberAgent for guest boot times.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:broker:events"` with `machine_name`, `catalog_name`, and power or registration event types; optional `index=hypervisor` if you correlate host load.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Normalize event types and timestamps across controller versions. If you use only OData, a scripted poll that emits synthetic `citrix:broker:events` rows is acceptable. Enrich with `catalog_name` via lookup from machine to catalog if the field is missing. Define business hours and maintenance windows in a lookup for scheduled suppression of boot-storm alerts when you intentionally start many machines.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; replace `event_type` values to match your extractions):

```spl
index=xd sourcetype="citrix:broker:events" (event_type="VmPowerOn" OR event_type="MachineStart" OR event_type="MachineRegistration")
| bin _time span=1m
| stats dc(machine_name) as machines_in_min, count as events_in_min, values(delivery_group) as dgs by _time, catalog_name
| eventstats median(machines_in_min) as med_boots, stdev(machines_in_min) as stdev_boots by catalog_name
| eval z_score=if(isnull(stdev_boots) OR stdev_boots=0, 0, (machines_in_min - med_boots) / stdev_boots)
| where machines_in_min > 20 OR z_score > 3
| table _time, catalog_name, dgs, machines_in_min, events_in_min, z_score
```

**Machine Boot Storm Detection and Mitigation** — Tune the static threshold to your environment size. Small sites may use a lower per-minute value; very large sites may raise it. The Z-score needs several buckets of history in the time window: schedule the alert on a 15- to 30-minute window for stability.

Step 3 — Validate
After a known maintenance that starts many hosts, compare maximum machines per minute to this search. Confirm false positives are low during expected bulk starts by using a suppression lookup tied to change tickets.

Step 4 — Operationalize
Document actions: increase stagger in the delivery group, delay user communications, and engage virtualization team if storage latency spikes. Revisit autoscale and peak time definitions quarterly.

## SPL

```spl
index=xd sourcetype="citrix:broker:events" (event_type="VmPowerOn" OR event_type="MachineStart" OR event_type="MachineRegistration" OR match(_raw, "(power.?on|start|registration|boot)", "i"))
| eval boot_phase=coalesce(power_state, event_type, "Unknown")
| bin _time span=1m
| stats dc(machine_name) as machines_in_min, count as events_in_min, values(delivery_group) as dgs by _time, catalog_name
| eventstats median(machines_in_min) as med_boots, stdev(machines_in_min) as stdev_boots by catalog_name
| eval z_score=if(isnull(stdev_boots) OR stdev_boots=0, 0, (machines_in_min - med_boots) / stdev_boots)
| where machines_in_min > 20 OR z_score > 3
| sort - machines_in_min
| table _time, catalog_name, dgs, machines_in_min, events_in_min, z_score
```

## Visualization

Overlay timechart: machines started per minute by catalog, optional second axis for failed registrations, table of top peaks with z-score, Sankey or flow optional for maintenance window correlation.

## References

- [Citrix autoscale and scheduled actions](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops-service/manage-deployments/citrix-autoscale/about-autoscale.html)
- [Load management — brokering context](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/manage-load-balancing.html)
