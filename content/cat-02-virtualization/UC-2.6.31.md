<!-- AUTO-GENERATED from UC-2.6.31.json — DO NOT EDIT -->

---
id: "2.6.31"
title: "Citrix Zone Topology and Zone Preference Failover"
criticality: "high"
splunkPillar: "Observability"
---

# UC-2.6.31 · Citrix Zone Topology and Zone Preference Failover

## Description

Multi-zone CVAD sites route users to preferred zones; controllers and resources must register and broker in the right order. Unplanned failover traffic, inter-zone brokering storms, or machines registering outside their zone hint at network partitions, site misconfiguration, or loss of a preferred data path. Tracking zone-related broker events and preferred versus failover path selection shows topology stress before end-user latency spikes.

## Value

Multi-zone CVAD sites route users to preferred zones; controllers and resources must register and broker in the right order. Unplanned failover traffic, inter-zone brokering storms, or machines registering outside their zone hint at network partitions, site misconfiguration, or loss of a preferred data path. Tracking zone-related broker events and preferred versus failover path selection shows topology stress before end-user latency spikes.

## Implementation

Standardize `ZoneName` and delivery group in broker events. Create lookups for expected zone–delivery-group mappings. Alert when failover_path volume exceeds baseline, when zone membership churn appears, or when a zone has zero registered workers during business hours. Enrich with NetScaler or WAN metrics if you need proof of network cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Template for Citrix XenDesktop 7 (TA-XD7-Broker), optional Citrix Monitor Service OData API for `Zones`.
• Ensure the following data sources are available: `sourcetype="citrix:broker:events"` with zone and registration fields; optional `citrix:netscaler:syslog` for ADC.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Verify broker event extractions for zone, registration, and failover terms. Add baseline searches for “normal” preferred-path volume per time-of-day. Document zone architecture and maintenance windows in a lookup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; tune `event_type` and regex for your build):

```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)zone|failover|preferred|registration|chassis|data.?store|inter.?zone") OR event_type IN ("Zone*", "Registration", "Configuration"))
| eval zone=coalesce(ZoneName, zone_name, Zone)
| eval path=if(match(_raw, "(?i)failover|secondary|not.?preferred|alternate"), "failover_path", if(match(_raw, "(?i)preferred|primary|home.?zone"), "preferred_path", "other"))
| where isnotnull(zone) OR path!="other"
| bin _time span=5m
| stats count, values(event_type) as event_types, dc(host) as controller_count by _time, zone, path, delivery_group
| sort -_time, zone, path
```

Step 3 — Validate
Compare a known DR exercise or forced failover in lab to ensure events classify into preferred_path vs failover_path. Adjust regex if your logs use different wording.

Step 4 — Operationalize
Set adaptive thresholds; route zone-wide anomalies to the platform team. Add drilldowns to the Citrix and network dashboards for the affected zone.

## SPL

```spl
index=xd sourcetype="citrix:broker:events" (match(_raw, "(?i)zone|failover|preferred|registration|chassis|data.?store|inter.?zone") OR event_type IN ("Zone*", "Registration", "Configuration"))
| eval zone=coalesce(ZoneName, zone_name, Zone)
| eval path=if(match(_raw, "(?i)failover|secondary|not.?preferred|alternate"), "failover_path", if(match(_raw, "(?i)preferred|primary|home.?zone"), "preferred_path", "other"))
| where isnotnull(zone) OR path!="other"
| bin _time span=5m
| stats count, values(event_type) as event_types, dc(host) as controller_count by _time, zone, path, delivery_group
| sort -_time, zone, path
```

## Visualization

Sankey or flow (preferred vs failover), Timeline (zone events), Table (anomalous delivery groups by zone).

## References

- [Zones in Citrix Virtual Apps and Desktops](https://docs.citrix.com/en-us/citrix-virtual-apps-desktops/221/manage-deployment/zones.html)
