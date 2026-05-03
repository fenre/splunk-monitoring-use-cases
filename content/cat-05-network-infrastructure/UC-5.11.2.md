<!-- AUTO-GENERATED from UC-5.11.2.json — DO NOT EDIT -->

---
id: "5.11.2"
title: "Interface Error and Discard Streaming"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.2 · Interface Error and Discard Streaming

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Fault

*We help you catch real cable and port problems from error counters before a link fully dies, instead of only seeing trouble after the fact.*

---

## Description

CRC errors, input errors, and output discards often precede link failure or indicate a bad transceiver, duplex mismatch, or MTU issue. Streaming these counters at 30-second intervals via gNMI catches error bursts that 5-minute SNMP polls average away. A sudden spike in `in_fcs_errors` on a 100G spine link demands immediate investigation — it could be a failing optic about to take down a leaf.

## Value

Network operations teams detect physical layer problems (CRC/FCS errors from bad cables/optics) and congestion issues (output discards from full queues) in near real time via gNMI streaming, enabling proactive maintenance before application impact.

## Implementation

Subscribe to `/interfaces/interface/state/counters` at 30s sample intervals. Use `rate_avg()` to convert cumulative counters to per-second rates. Alert on any non-zero FCS error rate (indicates physical-layer problems). Alert on discard rates exceeding baseline (indicates congestion or QoS policy drops). Correlate with optic health (UC-5.11.5) for root cause.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector configured (see UC-5.11.1 prerequisites for base setup). This UC subscribes to the same OpenConfig path `/interfaces/interface/state/counters` but focuses on error and discard counter leaves: `in-errors`, `out-errors`, `in-discards`, `out-discards`, `in-fcs-errors`, `in-crc-errors` (where available).
- Understanding error types: (a) CRC/FCS errors = physical layer problems (bad cable, dirty optic, electromagnetic interference); (b) Input errors = frames received with errors (includes CRC); (c) Output errors = frames the device failed to transmit (usually indicates interface congestion or hardware fault); (d) Input discards = frames discarded due to buffer overflow or ACL drop; (e) Output discards = frames dropped because the output queue was full (QoS tail drop or congestion).
- Error thresholds vary by link speed and application sensitivity. As a starting point: any interface with > 100 errors/minute at 10G or > 10 errors/minute at 1G warrants investigation. For latency-sensitive applications (voice, video, trading), even 1 error/minute may be unacceptable.
- Correlate with optical transceiver health (UC-5.11.5) — CRC errors often trace to degraded optics.

### Step 1 — Configure data collection
Verify error counter metrics in Splunk:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics host=leaf-01
| search metric_name="openconfig_interfaces*error*" OR metric_name="openconfig_interfaces*discard*"
```
You should see `openconfig_interfaces.in_errors`, `openconfig_interfaces.out_errors`, `openconfig_interfaces.in_discards`, `openconfig_interfaces.out_discards`. If missing, the device may not support these counters via OpenConfig, or they may be under a different YANG path (e.g., Cisco-specific: `Cisco-IOS-XR-infra-statsd-oper`).

### Step 2 — Create the search and alert

**Primary search — Interface error and discard rates:**
```spl
| mstats rate_avg("openconfig_interfaces.in_errors") AS in_err_rate rate_avg("openconfig_interfaces.out_errors") AS out_err_rate rate_avg("openconfig_interfaces.in_discards") AS in_disc_rate rate_avg("openconfig_interfaces.out_discards") AS out_disc_rate WHERE index=gnmi_metrics BY host, name span=1m
| eval total_errors=round((in_err_rate + out_err_rate) * 60, 0)
| eval total_discards=round((in_disc_rate + out_disc_rate) * 60, 0)
| where total_errors > 10 OR total_discards > 10
| lookup interface_capacity.csv host name OUTPUT speed_mbps role description
| eval severity=case(total_errors > 1000 OR total_discards > 1000, "CRITICAL", total_errors > 100 OR total_discards > 100, "HIGH", 1==1, "WARNING")
| eval likely_cause=case(in_err_rate > out_err_rate * 10, "Physical layer (CRC/FCS) - check cable/optic", out_disc_rate > in_disc_rate * 10, "Output congestion - check QoS/queue depth", in_disc_rate > out_disc_rate * 10, "Input buffer overflow or ACL drops", 1==1, "Mixed - investigate further")
| sort -total_errors, -total_discards
```

#### Understanding this SPL: `rate_avg()` converts cumulative error counters to per-second rates. Multiplying by 60 gives errors-per-minute for easier interpretation. The `likely_cause` field provides immediate triage guidance based on the error distribution pattern. Input errors dominating = physical layer problem. Output discards dominating = congestion/QoS issue.

**Error trending with correlation to traffic volume:**
```spl
| mstats rate_avg("openconfig_interfaces.in_errors") AS err_rate rate_avg("openconfig_interfaces.in_octets") AS traffic_rate WHERE index=gnmi_metrics host=* name=* span=5m
| eval err_per_min=round(err_rate*60, 1)
| eval traffic_mbps=round(traffic_rate*8/1000000, 1)
| where err_per_min > 1
| eval err_ratio=round(err_per_min/if(traffic_mbps>0, traffic_mbps, 0.01), 4)
| timechart span=5m avg(err_per_min) as avg_errors avg(traffic_mbps) as avg_traffic by host
```

#### Understanding this SPL: Correlates errors with traffic volume. Errors that only occur during high utilization suggest congestion (tail drops). Errors at all traffic levels suggest physical layer problems (bad cable/optic).

**Flapping interface detection — error rate spikes:**
```spl
| mstats rate_avg("openconfig_interfaces.in_errors") AS in_err rate_avg("openconfig_interfaces.out_errors") AS out_err WHERE index=gnmi_metrics BY host, name span=1m
| eval total_err=in_err + out_err
| eventstats avg(total_err) as avg_err stdev(total_err) as std_err by host, name
| where total_err > avg_err + (3 * std_err) AND total_err > 0.1
| eval spike_factor=round(total_err/if(avg_err>0, avg_err, 0.001), 1)
| sort -spike_factor
```

### Step 3 — Validate
(a) On the device, run `show interface Ethernet1/1 | include error` and compare counters. The `mstats` rate should reflect the delta between consecutive CLI readings.
(b) Simulate errors: if you have a test environment, introduce a marginal optical patch cable and verify error counters increment.
(c) Verify that interfaces with known errors (from NOC tickets) appear in the alert results.
(d) Cross-reference with UC-5.11.5 (optical health) — interfaces with CRC errors should often show degraded receive power.

### Step 4 — Operationalize
Dashboard ("Network — Interface Errors & Discards"):
- Row 1 — Single-value tiles: "Interfaces with errors (5min)", "Total error rate (all interfaces)", "Total discard rate", "CRITICAL interfaces".
- Row 2 — Table: host, interface, error_rate, discard_rate, severity, likely_cause. Color-coded by severity.
- Row 3 — Timechart: error trends for selected interface over 24h with traffic volume overlay.
- Row 4 — Heatmap: all interfaces by host, color-coded by error rate.

Alerting:
- Critical (> 1000 errors/min sustained for 5+ minutes): likely hardware failure — page NOC for immediate cable/optic replacement.
- High (> 100 errors/min): schedule maintenance window for cable/optic replacement.
- Warning (> 10 errors/min): monitor — may be intermittent and self-resolving (environmental electromagnetic interference).

Runbook (owner: Network Operations):
1. **CRC/input errors increasing**: Check the cable path and optic. Run an OTDR test if available. Check optical power levels via UC-5.11.5. If the optic is degraded, replace it.
2. **Output discards increasing**: Interface is congested. Check QoS queue configuration (UC-5.11.6). Consider upgrading the link, adding ECMP paths, or applying traffic shaping.

### Step 5 — Troubleshooting

- **Error counters always zero** — Some interfaces genuinely have no errors (healthy state). If you expect errors but see none, check whether the device reports errors under a vendor-specific YANG path instead of OpenConfig.

- **Discard rate is very high but no errors** — This is normal for QoS tail drops. When a queue is full, frames are discarded without errors. Check QoS queue configuration and consider implementing WRED (Weighted Random Early Detection).

- **Counter values are extremely large after reboot** — Counter reset during reboot can cause `rate_avg()` to produce an anomalous spike. Filter with `| where total_errors < 1000000` to exclude reset artifacts.

- **Different error types on different platforms** — OpenConfig standardizes some counters, but vendors vary. Check the YANG module on each platform: `gnmic capabilities --address <device>` lists supported models.

## SPL

```spl
| mstats rate_avg("openconfig_interfaces.in_errors") AS err_rate, rate_avg("openconfig_interfaces.in_fcs_errors") AS fcs_rate, rate_avg("openconfig_interfaces.out_discards") AS discard_rate WHERE index=gnmi_metrics BY host, name span=1m
| where err_rate > 0 OR fcs_rate > 0 OR discard_rate > 10
| table _time, host, name, err_rate, fcs_rate, discard_rate
| sort -fcs_rate
```

## Visualization

Line chart (error rates over time), Table (interfaces with active errors), Heatmap (errors across fabric).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
