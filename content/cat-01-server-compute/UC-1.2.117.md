---
id: "1.2.117"
title: "NIC Teaming & Network Adapter Failures (Windows)"
criticality: "high"
splunkPillar: "Security"
---

# UC-1.2.117 · NIC Teaming & Network Adapter Failures (Windows)

## Description

NIC teaming provides network redundancy for servers. Adapter failures reduce redundancy and can cause outages if the remaining NIC also fails.

## Value

NIC teaming provides network redundancy for servers. Adapter failures reduce redundancy and can cause outages if the remaining NIC also fails.

## Implementation

Monitor System event log for network adapter events from NIC drivers (e1cexpress for Intel, mlx4_bus for Mellanox, vmxnet3ndis6 for VMware). Track link-down events, adapter resets, and errors. For NIC teams, monitor Microsoft-Windows-MsLbfoProvider events. Alert on: team degradation (standby adapter now active), both adapters down, and frequent adapter resets (hardware failure). Include Perfmon Network Interface counters for bandwidth and error monitoring.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_windows`.
• Ensure the following data sources are available: `sourcetype=WinEventLog:Microsoft-Windows-NlbMgr/Operational`, `sourcetype=WinEventLog:System`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Monitor System event log for network adapter events from NIC drivers (e1cexpress for Intel, mlx4_bus for Mellanox, vmxnet3ndis6 for VMware). Track link-down events, adapter resets, and errors. For NIC teams, monitor Microsoft-Windows-MsLbfoProvider events. Alert on: team degradation (standby adapter now active), both adapters down, and frequent adapter resets (hardware failure). Include Perfmon Network Interface counters for bandwidth and error monitoring.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=wineventlog source="WinEventLog:System" SourceName IN ("Microsoft-Windows-NDIS", "e1cexpress", "mlx4_bus", "vmxnet3ndis6", "Tcpip")
| eval Issue=case(match(Message, "(?i)disconnect"), "Link_Down", match(Message, "(?i)reset"), "Adapter_Reset", match(Message, "(?i)error"), "Adapter_Error", 1=1, "Other")
| stats count latest(_time) as LastEvent by host, SourceName, Issue
| sort -LastEvent
```

Understanding this SPL

**NIC Teaming & Network Adapter Failures (Windows)** — NIC teaming provides network redundancy for servers. Adapter failures reduce redundancy and can cause outages if the remaining NIC also fails.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-NlbMgr/Operational`, `sourcetype=WinEventLog:System`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: wineventlog.

**Pipeline walkthrough**

• Scopes the data: index=wineventlog. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **Issue** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by host, SourceName, Issue** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

Understanding this CIM / accelerated SPL

**NIC Teaming & Network Adapter Failures (Windows)** — NIC teaming provides network redundancy for servers. Adapter failures reduce redundancy and can cause outages if the remaining NIC also fails.

Documented **Data sources**: `sourcetype=WinEventLog:Microsoft-Windows-NlbMgr/Operational`, `sourcetype=WinEventLog:System`. **App/TA** (typical add-on context): `Splunk_TA_windows`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Endpoint.Services` — enable acceleration for that model.
• Applies an explicit `search` filter to narrow the current result set.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (adapter events), Status dashboard (team health), Alert on degradation.

## SPL

```spl
index=wineventlog source="WinEventLog:System" SourceName IN ("Microsoft-Windows-NDIS", "e1cexpress", "mlx4_bus", "vmxnet3ndis6", "Tcpip")
| eval Issue=case(match(Message, "(?i)disconnect"), "Link_Down", match(Message, "(?i)reset"), "Adapter_Reset", match(Message, "(?i)error"), "Adapter_Error", 1=1, "Other")
| stats count latest(_time) as LastEvent by host, SourceName, Issue
| sort -LastEvent
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Endpoint.Services
  by Services.dest Services.name Services.status span=5m
| search Services.status!="running"
```

## Visualization

Table (adapter events), Status dashboard (team health), Alert on degradation.

## References

- [Splunk_TA_windows](https://splunkbase.splunk.com/app/742)
- [CIM: Endpoint](https://docs.splunk.com/Documentation/CIM/latest/User/Endpoint)
