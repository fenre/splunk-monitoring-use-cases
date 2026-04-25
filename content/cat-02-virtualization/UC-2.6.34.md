<!-- AUTO-GENERATED from UC-2.6.34.json — DO NOT EDIT -->

---
id: "2.6.34"
title: "Maintenance Mode and Drain Operations Tracking"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.34 · Maintenance Mode and Drain Operations Tracking

## Description

Maintenance mode and drain protect users during image updates, hypervisor work, and migrations. A large, unexpected, or long-lived maintenance footprint can silently reduce session capacity, especially if paired with autoscale. Tracking machines and delivery groups in maintenance and correlating with available capacity highlights operational drains versus true outages.

## Value

Maintenance mode and drain protect users during image updates, hypervisor work, and migrations. A large, unexpected, or long-lived maintenance footprint can silently reduce session capacity, especially if paired with autoscale. Tracking machines and delivery groups in maintenance and correlating with available capacity highlights operational drains versus true outages.

## Implementation

Prefer OData or broker inventory that exposes maintenance state per machine. Add a change lookup to label known maintenance. Compare hourly capacity against baseline when `machines_in_maint` rises. Alert on maintenance outside approved windows or when drain exceeds a percentage of a delivery group without a ticket.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (TA-XD7-Broker), Citrix Monitor Service OData API.
• Ensure the following data sources are available: `sourcetype="citrix:monitor:odata"` (Machines) with maintenance fields, or broker events with equivalent flags.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Schedule frequent OData pulls for machine inventory. Map boolean maintenance fields. Load `maintenance_authorized.csv` with change IDs and time boxes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; if using broker-only events, replace the data source in the first line):

```spl
index=xd (sourcetype="citrix:monitor:odata" (ODataEntity=Machine* OR match(_raw, "(?i)Maintenance|drain|suspend")))
| eval mmode=if(match(coalesce(InMaintenanceMode, maintenance_mode, raw_flags), "(?i)true|1|yes|on"), 1, 0)
| eval dg=coalesce(delivery_group, DeliveryGroup, CatalogName)
| where mmode=1
| timechart span=1h sum(mmode) as machines_in_maint, dc(dg) as affected_groups, dc(MachineName) as affected_machines
```

Step 3 — Validate
Place a test machine in maintenance and ensure counts increment. Reconcile totals with the console. Verify change lookup join.

Step 4 — Operationalize
Add a readout to the daily NOC huddle. Integrate with capacity dashboards so a drain does not look like a mysterious outage.

## SPL

```spl
index=xd (sourcetype="citrix:monitor:odata" (ODataEntity=Machine* OR match(_raw, "(?i)Maintenance|drain|suspend")))
| eval mmode=if(match(coalesce(InMaintenanceMode, maintenance_mode, raw_flags), "(?i)true|1|yes|on"), 1, 0)
| eval dg=coalesce(delivery_group, DeliveryGroup, CatalogName)
| where mmode=1
| timechart span=1h sum(mmode) as machines_in_maint, dc(dg) as affected_groups, dc(MachineName) as affected_machines
```

## Visualization

Stacked area (machines in maintenance by group), Bar chart (duration by catalog), Table (open maintenance with owner from lookup).

## References

- [Put machines in maintenance - Citrix](https://docs.citrix.com/en-us/citrix-daas/deployment-guides/put-machines-into-maintenance.html)
