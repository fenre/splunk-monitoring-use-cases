<!-- AUTO-GENERATED from UC-2.6.32.json — DO NOT EDIT -->

---
id: "2.6.32"
title: "Hypervisor Connection Health Monitoring"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.32 · Hypervisor Connection Health Monitoring

## Description

Delivery Controllers use hypervisor connections to start, stop, and snapshot virtual machines. VMware vCenter loss, Hyper-V/SCVMM permission errors, certificate trust issues, and storage path failures surface as brokering or power-management failures. Early detection from broker `hosting connection` events, combined with a thin layer of hypervisor health, prevents large-scale session capacity loss during certificate rotations or vCenter maintenance.

## Value

Delivery Controllers use hypervisor connections to start, stop, and snapshot virtual machines. VMware vCenter loss, Hyper-V/SCVMM permission errors, certificate trust issues, and storage path failures surface as brokering or power-management failures. Early detection from broker `hosting connection` events, combined with a thin layer of hypervisor health, prevents large-scale session capacity loss during certificate rotations or vCenter maintenance.

## Implementation

Map hosting connection event fields from your broker TA. For each `hosting_connection_name`, maintain a lookup for owner team and service window. Add optional append searches from `vmware` and `hyperv` indexes to enrich with upstream platform state. Alert on any new critical error type or sustained connection_state not `OK`.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (TA-XD7-Broker), Splunk Add-on for VMware, Splunk Add-on for Microsoft Windows for Hyper-V.
• Ensure the following data sources are available: `index=xd` `sourcetype="citrix:broker:events"`; optional `index=vmware` / `index=hyperv` health feeds.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Confirm that hosting connection and error fields are present; add CIM-agnostic extractions as needed. Onboard vCenter/SCVMM summary health if the Citrix log alone is insufficient for root cause. Nutanix can be added via a parallel sourcetype if you run AHV connections.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; match field names in your data):

```spl
index=xd sourcetype="citrix:broker:events" match(_raw, "(?i)host(ing)?\s*connection|hypervisor|vCenter|Nutanix|XenServer|scvmm|cert|ssl|storage|connectivity")
| eval conn_state=coalesce(connection_state, ConnectionState, hypervisor_state, State)
| eval hc_name=coalesce(hosting_connection_name, HostingUnitName, HostConnection, catalog_hosting_unit)
| where match(coalesce(conn_state, ""), "(?i)unknown|unavail|error|down|loss|denied|auth|fail|cert|ssl") OR match(coalesce(ErrorMessage, Message, _raw), "(?i)ssl|cert|permission|unauthorized|down|unreachable|storage")
| stats earliest(_time) as first_evt, latest(_time) as last_evt, count, values(ErrorMessage) as last_errors by hc_name, host, conn_state
| sort - count
```

Step 3 — Validate
Induce a controlled disconnect in test (firewall to vCenter) and verify broker error patterns. Trivial noise from one-off blips: require two consecutive intervals before paging.

Step 4 — Operationalize
Integrate with hypervisor and certificate renewal calendars. Document rollback for broken trust or expired API accounts.

## SPL

```spl
index=xd sourcetype="citrix:broker:events" match(_raw, "(?i)host(ing)?\s*connection|hypervisor|vCenter|Nutanix|XenServer|scvmm|cert|ssl|storage|connectivity")
| eval conn_state=coalesce(connection_state, ConnectionState, hypervisor_state, State)
| eval hc_name=coalesce(hosting_connection_name, HostingUnitName, HostConnection, catalog_hosting_unit)
| where match(coalesce(conn_state, ""), "(?i)unknown|unavail|error|down|loss|denied|auth|fail|cert|ssl") OR match(coalesce(ErrorMessage, Message, _raw), "(?i)ssl|cert|permission|unauthorized|down|unreachable|storage")
| stats earliest(_time) as first_evt, latest(_time) as last_evt, count, values(ErrorMessage) as last_errors by hc_name, host, conn_state
| sort - count
```

## Visualization

Table (connection, state, first/last event), Map or swimlane (by hosting unit and hypervisor), Single value (count of bad connections).

## References

- [Citrix - Connections and management interfaces](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/221/install-configure/connections-hypervisor.html)
