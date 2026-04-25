<!-- AUTO-GENERATED from UC-2.6.75.json — DO NOT EDIT -->

---
id: "2.6.75"
title: "End-to-End Citrix Session Launch Time"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-2.6.75 · End-to-End Citrix Session Launch Time

## Description

End-to-end session launch is the user-perceived time from initial click in Workspace through brokering, host start, logon, and HDX connect until a usable session is ready. Splunking all phases in one time series exposes whether delays sit in the broker, the hypervisor, the profile, the identity stack, or the client—so teams do not guess where to invest tuning effort.

## Value

End-to-end session launch is the user-perceived time from initial click in Workspace through brokering, host start, logon, and HDX connect until a usable session is ready. Splunking all phases in one time series exposes whether delays sit in the broker, the hypervisor, the profile, the identity stack, or the client—so teams do not guess where to invest tuning effort.

## Implementation

Prefer uberAgent for automatic phase split on the VDA; supplement with broker events for the brokering and VM start portions. Clock-sync all tiers. Set SLOs per delivery group. Create drill-down dashboards from the same search as phase-specific panels. For cloud services, add Citrix DaaS connector latency where exposed in logs. Pair with a synthetic transaction from a test account for continuous proof.

## Detailed Implementation

Prerequisites
• `index=xd`: broker `SessionLogon` with `logon_duration_ms`, uberAgent `Logon:LogonDetail` phases, `citrix:hdx:connect` for handshake. NTP: broker, VDA, domain within 1s. Join key: `session_id` or `correlation_id` across sources.

Step 1 — Configure data collection
`props` EVAL- for numeric if strings. Pilot uberAgent on one delivery group. If mixing Director ODATA export, use same `delivery_group` string as broker. `FIELDALIAS-` to collapse `total_logon_ms` variants.

Step 2 — Create the search and alert
Set SLO ms per `delivery_group` in lookup; replace 90000. Alert on p95 breach 3x consecutive 15m bins. Add synthetic login every 15m (service account) for control channel. Excluded: scheduled maintenance DGs in lookup.

Step 3 — Validate
For one p95: Director logon phase breakdown same minute as Splunk `values(phase)`. If only broker total, uberAgent should attribute profile vs GPO delay.

Step 4 — Operationalize
Dashboard: stacked by phase, single-value p95, compare regions. EUC QBR: overlay with image/VDA/GPO change markers. Escalation: long `Group Policy` to AD team; `Profile` to FS/FSLogix; `ICA/HDX` to network; TAC if broker/DaaS service gap isolated.

## SPL

```spl
index=xd (sourcetype="citrix:broker:events" event_type="SessionLogon" OR sourcetype="uberAgent:Logon:LogonDetail" OR sourcetype="citrix:hdx:connect") earliest=-4h
| eval total_ms=tonumber(coalesce(logon_duration_ms, total_logon_ms, 0)), phase=coalesce(phase, "e2e")
| bin _time span=15m
| stats median(total_ms) as p50, perc95(total_ms) as p95, count as n, values(phase) as phases by _time, delivery_group
| where p95>90000
| table _time, delivery_group, p50, p95, n, phases
```

## Visualization

Stacked time by phase, Sankey of phase share for p95, single value SLO, compare regions or delivery groups side by side.

## References

- [uberAgent — Logon and session performance](https://splunkbase.splunk.com/app/1448)
- [Citrix — Session launch and logon process](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/technical-overview/logon-processes.html)
