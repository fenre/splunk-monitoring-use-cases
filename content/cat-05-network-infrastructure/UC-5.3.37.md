<!-- AUTO-GENERATED from UC-5.3.37.json — DO NOT EDIT -->

---
id: "5.3.37"
title: "Citrix ADC Pooled Licensing Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.37 · Citrix ADC Pooled Licensing Utilization

## Description

Pooled licensing ties multiple instances to a shared consumption meter (vCPUs, throughput, or other entitlements on supported platforms). Approaching the pool cap or entering grace or violation states risks forced throttling, feature loss, or audit findings where license position must be provable. Monitoring utilization versus entitlement is both a capacity and a compliance control.

## Value

Pooled licensing ties multiple instances to a shared consumption meter (vCPUs, throughput, or other entitlements on supported platforms). Approaching the pool cap or entering grace or violation states risks forced throttling, feature loss, or audit findings where license position must be provable. Monitoring utilization versus entitlement is both a capacity and a compliance control.

## Implementation

Ingest NITRO license and pooled-capacity output via TA scripted input into `citrix:netscaler:perf` and capture syslog warnings from `ns` `license` `pool`. Set thresholds at 80% (planning) and 90% (urgent) for pool use. Log proof-of-use reports with Splunk for quarterly true-ups. Add alerts for grace-period entry or license server connectivity loss (where applicable).

## Detailed Implementation

Prerequisites: Stable access to the license service or NITRO; pool_name labels aligned to procurement. Step 1: Configure data collection — Schedule citrix:netscaler:perf poll hourly or every 15 minutes; capture syslog for grace/violation; props EXTRACT for license_pool_use_pct, allocated_vcpus, throughput_mbps. Step 2: Create the search and alert — Open capacity ticket at 80% pool use, page at 90%, sev-1 for grace or implied denial; join asset lookup adcpool_owners.csv for routing. Step 3: Validate — `index=netscaler (sourcetype="citrix:netscaler:perf" OR sourcetype="citrix:netscaler:syslog") (pool OR license) earliest=-2h | stats max(pool_pct) by pool_name, host` and reconcile to Citrix license portal or CLI. Step 4: Operationalize — Monthly CSV/scheduled report to procurement and finance; if grace repeats or counters stall, escalate to Citrix licensing administrators; alert threshold tuning: start at 80/90% and document baseline delta weekly.

## SPL

```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("pooled" OR "license pool" OR vCPU OR throughput OR entitlement OR CBM OR "ceiling" OR grace OR expir)
| eval pool_pct=coalesce(license_pool_use_pct, pooled_license_use_pct, 0), vcpu=coalesce(allocated_vcpus, 0), thr_mbps=coalesce(throughput_mbps, 0)
| eval capacity_flag=if(pool_pct>90 OR match(_raw,"(?i)grace|violation|denied"),1,0)
| bin _time span=1h
| stats max(pool_pct) as max_pool, max(vcpu) as peak_vcpu, max(thr_mbps) as peak_thr, max(capacity_flag) as risk by _time, host, pool_name
| where max_pool>80 OR risk=1
| table _time, host, pool_name, max_pool, peak_vcpu, peak_thr, risk
```

## Visualization

Gauge: pool use percent, line chart: vCPU and throughput, table: top consumers by `host` and `pool_name`.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix — Licensing and pooled capacity](https://www.citrix.com/support/licensing/)
