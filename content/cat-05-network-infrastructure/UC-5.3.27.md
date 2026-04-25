<!-- AUTO-GENERATED from UC-5.3.27.json — DO NOT EDIT -->

---
id: "5.3.27"
title: "Citrix ADC Surge Queue and Spillover Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.27 · Citrix ADC Surge Queue and Spillover Events

## Description

When demand exceeds a virtual server capacity settings, connections queue in the surge buffer or spill to backup vservers, affecting latency and success rates. Sustained surge depth or repeated spillover indicates undersized `maxclient` values, pool exhaustion, or slow backends. Early detection keeps user-visible failures and cascade overload off backup paths.

## Value

When demand exceeds a virtual server capacity settings, connections queue in the surge buffer or spill to backup vservers, affecting latency and success rates. Sustained surge depth or repeated spillover indicates undersized `maxclient` values, pool exhaustion, or slow backends. Early detection keeps user-visible failures and cascade overload off backup paths.

## Implementation

Source spillover and surge events from `citrix:netscaler:syslog` (state change messages) and, if available, counter polls into `citrix:netscaler:perf` for queue depth. Parse vserver and backup vserver names. Set alert conditions on non-zero queue depth for more than a few intervals, and any spillover to backup, unless during known tests.

## Detailed Implementation

Prerequisites
• Syslog and/or NITRO performance feed into `index=netscaler`.
• Naming map from vserver to application and owner on-call.

Step 1 — Configure data collection
Enable state and surge-related logging on the ADC. If using perf poll, include lb vserver connection and surge statistics at 1–5 minute intervals.

Step 2 — Create the search and alert
Tighten SPL `rex` to your exact log format after review of samples. Page when spillover appears or when queue depth trends upward for 3 consecutive windows.

Step 3 — Validate
Compare vservers, services, and load-balancing state in the Citrix ADC management view or command line for the same time window and objects.
Step 4 — Operationalize
Capacity playbook: raise limits cautiously, scale pool, or add nodes; avoid masking chronic backend slowness.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("surge" OR "spillover" OR "max client" OR maxclient OR "SURGEQ")
| rex field=_raw max_match=0 "(?i)depth[\\s:=]+(?<surge_depth>\\d+)"
| eval has_spillover=if(match(_raw, "(?i)spillover"),1,0)
| eval vserver=coalesce(vserver_name, if(match(_raw, "(?i)vserver[\\s:]+(?<vs>\\S+)"), vs, null()))
| bin _time span=5m
| stats count as events, max(surge_depth) as max_depth, max(has_spillover) as spillover_flag, values(vserver) as vserver_list, latest(host) as adc by _time, host
| where spillover_flag=1 OR max_depth>0 OR events>0
| eval vserver=mvindex(vserver_list,0)
| sort - _time
| table _time, adc, vserver, max_depth, spillover_flag, events
```

## Visualization

Time chart of max surge depth by vserver, event list for spillover with backup target, link to app response-time panels.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Load balancing and surge protection](https://docs.citrix.com/en-us/citrix-adc/current-release/load-balancing.html)
