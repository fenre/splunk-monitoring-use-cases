<!-- AUTO-GENERATED from UC-5.3.27.json — DO NOT EDIT -->

---
id: "5.3.27"
title: "Citrix ADC Surge Queue and Spillover Events"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.27 · Citrix ADC Surge Queue and Spillover Events

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability

*We catch surge and spillover lines in the same logs so a full farm shows up in events before a whole front page goes static.*

---

## Description

When demand exceeds a virtual server capacity settings, connections queue in the surge buffer or spill to backup vservers, affecting latency and success rates. Sustained surge depth or repeated spillover indicates undersized `maxclient` values, pool exhaustion, or slow backends. Early detection keeps user-visible failures and cascade overload off backup paths.

## Value

Application delivery teams detect Citrix ADC surge queue buildup and spillover events indicating backend saturation, enabling capacity remediation before user-facing latency or failover.

## Implementation

Source spillover and surge events from `citrix:netscaler:syslog` (state change messages) and, if available, counter polls into `citrix:netscaler:perf` for queue depth. Parse vserver and backup vserver names. Set alert conditions on non-zero queue depth for more than a few intervals, and any spillover to backup, unless during known tests.

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Syslog and/or NITRO performance counters. Key fields: `surge_depth` (connections queued), `spillover` (traffic redirected to backup vserver), `vserver_name`, `maxclient`.
* Surge queue: when a vserver's backend services can't accept new connections fast enough, connections queue in a buffer. Spillover: when surge queue exceeds threshold, traffic spills to a backup vserver. Sustained surge = undersized backend or slow backends.

### Step 1 — - Configure data collection
Enable surge/spillover logging. NITRO poll: `GET /nitro/v1/stat/lbvserver` includes `surgecount` and `spilloverthreshold`. Verify:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("surge" OR "spillover" OR "maxclient" OR "SURGEQ") earliest=-4h
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- Surge queue and spillover events:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("surge" OR "spillover" OR "max client" OR "maxclient" OR "SURGEQ") earliest=-4h
| eval vs=coalesce(vserver_name, vs_name, vserver)
| eval depth=coalesce(surge_depth, surgecount, if(match(_raw, "(?i)depth[\s:=]+(\d+)"), tonumber(replace(_raw, ".*depth[\s:=]+(\d+).*", "\1")), null()))
| eval has_spillover=if(match(_raw, "(?i)spillover"), 1, 0)
| bin _time span=5m
| stats max(depth) as max_depth max(has_spillover) as spillover_flag count as events by _time, host, vs
| where spillover_flag=1 OR max_depth > 0
| lookup citrix_vserver_inventory.csv vs OUTPUT application, tier, owner
| eval severity=case(spillover_flag=1, "HIGH -- traffic spilling to backup", max_depth > 100, "HIGH -- deep surge queue", max_depth > 10, "WARNING -- surge building", 1==1, "INFO")
| sort severity, -max_depth
```

### Step 3 — - Validate
(a) On ADC CLI: `show lb vserver <vs>` -- check surge count and spillover count.
(b) Simulate backend slowness (add delay to test backend) and verify surge depth increases.
(c) If backup vserver is configured, verify spillover triggers when surge threshold is exceeded.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- Surge & Spillover"):
* Row 1 -- Single-value: "vServers with surge", "Max surge depth", "Spillovers", "Affected apps".
* Row 2 -- Surge/spillover detail table.
* Row 3 -- Surge depth trending timechart.

Alerting:
* High (spillover occurring): traffic on backup path -- investigate primary backend.
* Warning (surge depth > 50 for > 3 intervals): backends not keeping up.

### Step 5 — - Troubleshooting

* **Sustained surge** -- Backends too slow. Check: (1) backend server CPU/memory, (2) database query performance, (3) connection timeouts on ADC: `show service <svc>` for `maxClient`, `maxReq`.

* **Spillover to backup** -- Primary backend capacity exceeded. Increase backend instances or raise `spilloverThreshold`: `set lb vserver <vs> -spilloverThreshold <value>`.

* **Surge only during peak hours** -- Backend capacity insufficient for peak load. Pre-scale or implement auto-scaling.

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

## Known False Positives

Slow backends and honest flash crowds can create surge and spillover events the front door is supposed to show.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix ADC — Load balancing and surge protection](https://docs.citrix.com/en-us/citrix-adc/current-release/load-balancing.html)
