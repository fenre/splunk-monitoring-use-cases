<!-- AUTO-GENERATED from UC-5.3.37.json — DO NOT EDIT -->

---
id: "5.3.37"
title: "Citrix ADC Pooled Licensing Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.37 · Citrix ADC Pooled Licensing Utilization

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity, Compliance

*We look at shared license use over time on the same platform so a quiet threshold day does not turn into a hard stop with no warning.*

---

## Description

Pooled licensing ties multiple instances to a shared consumption meter (vCPUs, throughput, or other entitlements on supported platforms). Approaching the pool cap or entering grace or violation states risks forced throttling, feature loss, or audit findings where license position must be provable. Monitoring utilization versus entitlement is both a capacity and a compliance control.

## Value

Infrastructure teams monitor Citrix ADC pooled license bandwidth utilization and expiry dates, preventing instance provisioning failures from pool exhaustion and license lapses.

## Implementation

Ingest NITRO license and pooled-capacity output via TA scripted input into `citrix:netscaler:perf` and capture syslog warnings from `ns` `license` `pool`. Set thresholds at 80% (planning) and 90% (urgent) for pool use. Log proof-of-use reports with Splunk for quarterly true-ups. Add alerts for grace-period entry or license server connectivity loss (where applicable).

## Detailed Implementation

### Prerequisites
* Splunk Add-on for Citrix NetScaler (`Splunk_TA_citrix-netscaler`, Splunkbase 2770). Citrix ADC pooled licensing data from Citrix ADM or NITRO stats. Key fields: `license_type`, `allocated_bandwidth`, `used_bandwidth`, `available_bandwidth`, `instance_count`, `expiry_date`.
* Citrix Pooled Licensing: instead of per-appliance licenses, bandwidth is allocated from a central pool in Citrix ADM. Instances check out bandwidth on startup. If the pool is exhausted, new instances can't start or existing instances may lose bandwidth.

### Step 1 — - Configure data collection
Citrix ADM manages the license pool. Poll ADM API or collect ADM syslog. Verify:
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("license" OR "bandwidth" OR "pool" OR "expir") earliest=-7d
| where match(_raw, "(?i)(license|bandwidth|pool|allocat)")
| stats count by host
```

### Step 2 — - Create the search and alert

**Primary search -- License pool utilization:**
```spl
index=netscaler (sourcetype="citrix:netscaler:syslog" OR sourcetype="citrix:netscaler:perf") ("license" OR "bandwidth pool" OR "pooled") earliest=-4h
| eval total_bw=coalesce(allocated_bandwidth, total_pool_bandwidth)
| eval used_bw=coalesce(used_bandwidth, consumed_bandwidth)
| eval available=coalesce(available_bandwidth, remaining_bandwidth)
| eval instances=coalesce(instance_count, licensed_instances)
| eval expiry=coalesce(expiry_date, license_expiry)
| stats latest(total_bw) as total latest(used_bw) as used latest(available) as available latest(instances) as instances latest(expiry) as expiry by host
| eval utilization_pct=if(total > 0, round(100*used/total, 1), null())
| eval days_to_expiry=if(isnotnull(expiry), round((strptime(expiry, "%Y-%m-%d") - now()) / 86400, 0), null())
| eval status=case(utilization_pct > 90, "CRITICAL -- pool nearly exhausted", utilization_pct > 75, "WARNING -- high utilization", days_to_expiry < 30 AND isnotnull(days_to_expiry), "WARNING -- license expiring soon", 1==1, "OK")
| where status != "OK"
```

### Step 3 — - Validate
(a) Check Citrix ADM: Infrastructure > Pooled Licensing -- compare utilization.
(b) Verify each instance's allocated bandwidth: ADM > Infrastructure > Instances.
(c) Check license expiry dates.

### Step 4 — - Operationalize
Dashboard ("Citrix ADC -- License Pool"):
* Row 1 -- Single-value: "Pool utilization %", "Total bandwidth (Gbps)", "Available (Gbps)", "Instances", "Days to expiry".
* Row 2 -- License status with expiry alerts.

Alerting:
* Critical (pool utilization > 90%): cannot provision new instances.
* Warning (license expiring < 30 days): renewal needed.

### Step 5 — - Troubleshooting

* **Pool exhausted** -- Instances may have checked out more bandwidth than needed. Review per-instance allocation in ADM and reduce over-provisioned instances.

* **Instance can't start** -- Insufficient pool bandwidth. Either free bandwidth from another instance or purchase additional pool capacity.

* **License expired** -- Grace period typically applies. Contact Citrix for renewal. Instances will continue running but may lose features.

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

## Known False Positives

Short peaks during renewals, burst traffic, and shared pools can wobble utilization before anything is truly out of license.

## References

- [Splunk Documentation: Splunk Add-on for Citrix NetScaler](https://docs.splunk.com/Documentation/AddOns/released/CitrixNetScaler/CitrixNetScaler)
- [Citrix — Licensing and pooled capacity](https://www.citrix.com/support/licensing/)
