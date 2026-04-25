<!-- AUTO-GENERATED from UC-5.3.39.json — DO NOT EDIT -->

---
id: "5.3.39"
title: "Citrix SD-WAN Application Steering and QoS Enforcement"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.39 · Citrix SD-WAN Application Steering and QoS Enforcement

## Description

Application-aware routing and queuing are core to SD-WAN value. Monitoring which path each app uses, when drops occur in a class of service, and when steering decisions change frequently exposes misconfiguration, license limits, and congestion on steered traffic that affects voice, video, and business apps.

## Value

Application-aware routing and queuing are core to SD-WAN value. Monitoring which path each app uses, when drops occur in a class of service, and when steering decisions change frequently exposes misconfiguration, license limits, and congestion on steered traffic that affects voice, video, and business apps.

## Implementation

Import application-to-QoS mapping from the orchestrator. Track drops and deep queue signs per class. For steering churn, use `path_selected` with `streamstats` to count changes per 5m for major apps. Involve the network and app teams when a critical app rides a backup path. Pair with underlay stats from the same time window to separate LAN vs WAN causes.

## Detailed Implementation

Prerequisites: Per-app routing and QoS with stable app key; reference table of primary path and expected qos_class. Step 1: Configure data collection — If very chatty, pre-aggregate on the forwarder; props [citrix:sdwan:app_route] and [citrix:sdwan:qos] with FIELDALIAS for app_name, path_selected, qos_class, and drops. Step 2: Create the search and alert — First alert on rising drops in the voice or call-control class; add a path drift report using streamstats on path_selected outside approved change windows; start with total_drops>0 and tune. Step 3: Validate — During maintenance on a reference site, compare Splunk to SD-WAN UI: `index=sdwan (sourcetype="citrix:sdwan:app_route" OR sourcetype="citrix:sdwan:qos") earliest=-1h | stats values(path_selected), sum(drops) by app, site_id`. Step 4: Operationalize — Feed steering review and carrier disputes; if drops persist post-tuning, escalate to Citrix SD-WAN and WAN architecture teams.

## SPL

```spl
index=sdwan (sourcetype="citrix:sdwan:app_route" OR sourcetype="citrix:sdwan:qos") earliest=-4h
| eval drops=tonumber(drops), app=coalesce(app_name, application, "unknown"), psel=coalesce(path_selected, selected_path, "unknown")
| bin _time span=5m
| stats sum(drops) as total_drops, count as dec_events, values(psel) as paths_used, values(qos_class) as qos by _time, app, site_id
| where total_drops>0 OR dec_events>1000
| table _time, site_id, app, total_drops, dec_events, paths_used, qos
```

## Visualization

Stacked area: drop count by `qos_class`; Sankey or table: `app` to `path_selected` distribution; timechart: steering change rate for top apps.

## References

- [Citrix — SD-WAN application quality of service](https://docs.citrix.com/en-us/citrix-sd-wan/11-4/application-qos.html)
