<!-- AUTO-GENERATED from UC-5.1.75.json — DO NOT EDIT -->

---
id: "5.1.75"
title: "Network Topology Discovery and Source-of-Truth Reconciliation"
status: "community"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.75 · Network Topology Discovery and Source-of-Truth Reconciliation

> **Criticality:** Medium &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Inventory, Configuration &middot; **Wave:** Run &middot; **Status:** Community

*We compare the official list of all our network gear against what we actually see talking on the network each day. When the official list says we have a device but Splunk has not heard from it in 24 hours, the team gets alerted to investigate — either the device is broken, the monitoring is broken, or the list is wrong. All three are problems worth knowing.*

---

## Description

Reconciles the network source-of-truth (NetBox / IP Fabric / Nautobot) against live Splunk telemetry. The query lists every device that the inventory says exists but that has not sent any logs in the last 24 hours — those are the devices Splunk is supposed to be monitoring but is not.

## Value

Most networks have at least three competing answers to the question 'how many switches do we have?' — the spreadsheet, the asset-management system, and what the network actually has. The source-of-truth movement (NetBox, IP Fabric, Nautobot) collapses the spreadsheet and asset-management systems into one canonical record. This UC compares that canonical record against what Splunk is observing in production and surfaces three separate failure modes: (a) devices that exist on the network but no monitoring is collecting from them, (b) devices that monitoring expects to see but the device has been removed and the inventory was never updated, (c) silent monitoring failures where a device's syslog forwarder broke and nobody noticed because the device never went offline. All three are invisible without explicit reconciliation.

## Implementation

Export the device inventory from NetBox / IP Fabric / Nautobot via REST API on a daily schedule. Land the result in a Splunk lookup (CSV for small fleets, KV Store for large fleets with frequent updates). Schedule a daily reconciliation search comparing the source-of-truth inventory against devices actively sending syslog or SNMP to Splunk. Alert on devices present in the source of truth but not reporting to Splunk — those are the gaps. Reverse the join to also catch the rarer 'reporting to Splunk but not in inventory' case (rogue devices, decommissioned-but-not-removed switches).

## SPL

```spl
| inputlookup netbox_devices.csv
| join type=left hostname [search index=network sourcetype="cisco:ios" earliest=-24h | stats latest(_time) as last_seen by host | rename host as hostname]
| eval status=if(isnull(last_seen),"NOT_REPORTING","OK")
| where status="NOT_REPORTING"
| table hostname, site, role, status
```

## Visualization

Table (missing devices, sortable by site / role), Single-value (overall coverage percentage — the headline number for the asset-management dashboard), Bar chart (reporting status by site, useful for spotting site-wide collector failures).

## Known False Positives

**Maintenance-mode devices.** Devices that are intentionally powered off for maintenance will show as NOT_REPORTING but should not page on-call. Add a `maintenance=true` flag to the inventory lookup and filter the alert.

**Brand-new devices in inventory but not yet provisioned.** Devices that have just been added to NetBox but have not yet been racked will appear as NOT_REPORTING for hours or days. Use a `provisioning_status` column from the source of truth to suppress unfinished items.

**Stale inventory entries for decommissioned devices.** The reverse problem: the source of truth has a device that was decommissioned six months ago and nobody removed the record. The alert is correct — escalate to the network-inventory owner, not the network-operations team.

## References

- [NetBox documentation](https://docs.netbox.dev/)
- [IP Fabric documentation](https://ipfabric.io/docs/)
- [Nautobot documentation](https://docs.nautobot.com/)
