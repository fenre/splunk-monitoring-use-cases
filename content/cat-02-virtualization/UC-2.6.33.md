<!-- AUTO-GENERATED from UC-2.6.33.json — DO NOT EDIT -->

---
id: "2.6.33"
title: "Citrix Autoscale Capacity Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.33 · Citrix Autoscale Capacity Events

## Description

Autoscale adjusts powered-on machine counts against load and time schedules. Stuck scale-out, aggressive scale-in, schedule drift, or throttled power actions create either idle unassigned capacity (cost) or under-provisioned pools (poor user experience). Aggregating autoscale- and power-related broker events and comparing with powered-on session counts from Monitor highlights drift and failed automation.

## Value

Autoscale adjusts powered-on machine counts against load and time schedules. Stuck scale-out, aggressive scale-in, schedule drift, or throttled power actions create either idle unassigned capacity (cost) or under-provisioned pools (poor user experience). Aggregating autoscale- and power-related broker events and comparing with powered-on session counts from Monitor highlights drift and failed automation.

## Implementation

Confirm event strings for your CVAD/Cloud version. Build baselines of scale_out vs load per delivery group. Join OData `InUse*`, `Registered*`, and `Unassigned*`-style fields when available. Alert on high fail_hits, zero scale_out during a ramp when usage rises, and sustained unassigned high-water marks outside policy.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (TA-XD7-Broker), Citrix Monitor Service OData API for capacity counters.
• Ensure the following data sources are available: `sourcetype="citrix:broker:events"` and optional `sourcetype="citrix:monitor:odata"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Ingest all broker subsystems that log power and autoscale. Align delivery group and machine name fields. Load business-hours schedules from a CSV to compare actual scale actions to the intended plan.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust match strings for your site):

```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)autoscale|power.?on|turn.?on|turn.?off|scale.?in|scale.?out|power.?action|capaci") OR event_type=Power* OR event_type=Autoscale*)
| eval direction=if(match(_raw, "(?i)scale.?out|turn.?on|add.*machine|increase"), "scale_out", if(match(_raw, "(?i)scale.?in|turn.?off|remove.*reduce"), "scale_in", "other"))
| eval dg=coalesce(delivery_group, DeliveryGroup, CatalogName)
| eval success=if(match(coalesce(result, action_result, state), "(?i)success|complete"), 1, if(match(coalesce(result, action_result, state), "(?i)fail|error|throttl|denied|pending"), 0, null()))
| bin _time span=15m
| stats count, sum(eval(if(success=1,1,0))) as success_hits, sum(eval(if(success=0,1,0))) as fail_hits, dc(machine_name) as machine_moves by _time, dg, direction
| where fail_hits>0 OR count>100
| table _time, dg, direction, count, success_hits, fail_hits, machine_moves
```

Step 3 — Validate
Reconcile counts with the Citrix admin console. Tune high `count` filter for large environments. Exclude maintenance windows with lookups.

Step 4 — Operationalize
Feed capacity reports to finops. Pair alerts with queue-depth UCs to separate broker from hypervisor bottlenecks.

## SPL

```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)autoscale|power.?on|turn.?on|turn.?off|scale.?in|scale.?out|power.?action|capaci") OR event_type=Power* OR event_type=Autoscale*)
| eval direction=if(match(_raw, "(?i)scale.?out|turn.?on|add.*machine|increase"), "scale_out", if(match(_raw, "(?i)scale.?in|turn.?off|remove.*reduce"), "scale_in", "other"))
| eval dg=coalesce(delivery_group, DeliveryGroup, CatalogName)
| eval success=if(match(coalesce(result, action_result, state), "(?i)success|complete"), 1, if(match(coalesce(result, action_result, state), "(?i)fail|error|throttl|denied|pending"), 0, null()))
| bin _time span=15m
| stats count, sum(eval(if(success=1,1,0))) as success_hits, sum(eval(if(success=0,1,0))) as fail_hits, dc(machine_name) as machine_moves by _time, dg, direction
| where fail_hits>0 OR count>100
| table _time, dg, direction, count, success_hits, fail_hits, machine_moves
```

## Visualization

Column chart (scale events by direction), Timechart (in-use vs registered machines), Table (failed power actions with delivery group).

## References

- [Autoscale in Citrix DaaS](https://docs.citrix.com/en-us/citrix-daas-service/monitor/health-data/autoscale.html)
