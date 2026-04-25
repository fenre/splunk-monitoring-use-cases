<!-- AUTO-GENERATED from UC-1.1.46.json — DO NOT EDIT -->

---
id: "1.1.46"
title: "Slab Cache Growth Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-1.1.46 · Slab Cache Growth Monitoring

## Description

Detects unusual day-over-day growth in the kernel slab allocator footprint so we can catch memory pressure from slab bloat or leaks before the host runs out of usable memory.

## Value

Catching runaway slab growth early protects services that depend on a healthy page cache and spare RAM, and it shortens time-to-triage for driver or app leaks hidden in the kernel allocator.

## Implementation

Ingest messages that include slab sizing (or build a `custom:slabinfo` input that prints total slab size). Require numeric `slab_size` extraction. Use the daily `stats` and `streamstats` rollups for a host-specific baseline, then alert when totals exceed the upper band.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_nix` (and a small scripted input if you are shipping `/proc/slabinfo` as structured events).
• Ensure the following data sources are available: as documented under **Data sources**.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Send syslog (or a periodic scripted snapshot) that includes a numeric **slab_size** field per host, or switch the SPL to the field names your script emits. The search expects daily bins and at least a few weeks of history for `streamstats` to learn a normal band.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=os sourcetype=syslog "slab"
| bin _time span=1d
| stats sum(slab_size) as total_slab by host, _time
| streamstats window=30 avg(total_slab) as baseline stdev(total_slab) as stddev by host
| eval upper=baseline+(2*stddev)
| where total_slab > upper
```

Understanding this SPL

**Slab Cache Growth Monitoring** — Detects when total slab size on a host rises above a rolling two-sigma band, which often precedes hard-to-explain free-memory shrinkage on busy servers.

The query scopes **index=os** and a syslog-class feed, then **bins** to one day, **stats** a daily `total_slab` per host, and uses **streamstats** for a 30-observation rolling mean and spread before comparing to the eval’d upper control limit.


Step 3 — Validate
On a Linux host, compare the alert time with `slabtop` and `cat /proc/slabinfo` to see which caches grew. Re-run a short time-range search and confirm the extracted `slab_size` values match what you see in `/proc/slabinfo` (or your scripted input output).

Step 4 — Operationalize
Add the search to a dashboard, route alerts to the platform team, and document how to capture a slab snapshot in the runbook. Consider visualizations: Timechart, Anomaly Chart



## SPL

```spl
index=os sourcetype=syslog "slab"
| bin _time span=1d
| stats sum(slab_size) as total_slab by host, _time
| streamstats window=30 avg(total_slab) as baseline stdev(total_slab) as stddev by host
| eval upper=baseline+(2*stddev)
| where total_slab > upper
```

## Visualization

Timechart, Anomaly Chart

## References

- [Splunk Add-on for Unix and Linux](https://splunkbase.splunk.com/app/833)
- [Splunk Lantern — use case library](https://lantern.splunk.com/)
