<!-- AUTO-GENERATED from UC-5.11.6.json — DO NOT EDIT -->

---
id: "5.11.6"
title: "QoS Queue Depth and Drop Streaming"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.11.6 · QoS Queue Depth and Drop Streaming

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Security &middot; **Type:** Performance

*We help you see when important traffic is piling up or getting dropped in queues, so you can fix congestion before it hits voice, video, or key apps.*

---

## Description

SNMP-polled QoS counters miss microbursts entirely — a 100ms queue overflow causes packet loss that a 5-minute poll never sees. gNMI SAMPLE subscriptions to `/qos/interfaces/interface/output/queues/queue/state` at 10-second intervals capture queue depth and transmit/drop counters at a granularity that reveals microburst patterns, misclassified traffic, and under-provisioned queues.

## Value

Network operations teams monitor QoS queue health via gNMI streaming, ensuring voice and video traffic receives priority treatment, detecting drops in real time, and validating that QoS policies are working as designed.

## Implementation

Subscribe to QoS queue state at 10-30s intervals. Focus on high-priority queues (voice, video, control-plane) where any drops indicate a problem. For best-effort queues, baseline normal drop rates and alert on 2x deviation. Correlate drops with interface utilization (UC-5.11.1) to distinguish congestion drops from policy drops. Use `drop_pct` to identify queues with systematic under-provisioning.

## Detailed Implementation

### Prerequisites
- Telegraf gNMI collector with SAMPLE subscription for QoS counters. OpenConfig path: `/qos/interfaces/interface/output/queues/queue/state`. Key metrics: `transmit-pkts`, `transmit-octets`, `dropped-pkts`, `dropped-octets`. These are cumulative counters — use `mstats rate_avg()` for per-second rates.
- QoS queue monitoring matters because modern networks use differentiated services (DSCP) to prioritize traffic: voice (EF/DSCP 46), video (AF41/DSCP 34), business-critical (AF31/DSCP 26), default (BE/DSCP 0). Drops in high-priority queues indicate misconfiguration or severe congestion. Drops in best-effort queues are expected during congestion (by design).
- Build a `qos_policy.csv` lookup: `host,name,queue_name,traffic_class,priority,drop_tolerance` (e.g., `leaf-01,Ethernet1/1,queue0,voice-EF,strict-priority,0`, `leaf-01,Ethernet1/1,queue3,default-BE,WRR-25%,medium`).
- Not all platforms expose QoS counters via OpenConfig. Vendor support: Arista EOS 4.28+ (OpenConfig QoS), Cisco NX-OS (limited — may need native YANG), Cisco IOS-XR (OpenConfig or native), Juniper (native YANG `junos-qos`). Verify with `gnmic capabilities`.

### Step 1 — Configure data collection
Telegraf subscription:
```toml
[[inputs.gnmi.subscription]]
  name = "openconfig_qos"
  origin = "openconfig"
  path = "/qos/interfaces/interface/output/queues/queue/state"
  subscription_mode = "sample"
  sample_interval = "30s"
```

Verify QoS metrics:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics
| search metric_name="openconfig_qos*"
```

### Step 2 — Create the search and alert

**Primary search — QoS queue drops by class:**
```spl
| mstats rate_avg("openconfig_qos.dropped_pkts") AS drop_rate rate_avg("openconfig_qos.transmit_pkts") AS tx_rate WHERE index=gnmi_metrics BY host, name, queue_name span=1m
| eval drops_per_min=round(drop_rate*60, 0)
| eval tx_per_min=round(tx_rate*60, 0)
| eval drop_pct=if(tx_per_min > 0, round(100*drops_per_min/(tx_per_min + drops_per_min), 3), 0)
| where drops_per_min > 0
| lookup qos_policy.csv host name queue_name OUTPUT traffic_class priority drop_tolerance
| eval severity=case(priority="strict-priority" AND drops_per_min > 0, "CRITICAL", traffic_class="voice-EF" OR traffic_class="video-AF41", "HIGH", drop_pct > 5, "HIGH", drop_pct > 1, "MEDIUM", 1==1, "LOW")
| sort severity, -drops_per_min
```

#### Understanding this SPL: Any drops in a strict-priority queue (typically voice) is critical — voice traffic should never be dropped if QoS is correctly configured. Drops in weighted queues indicate the interface is congested beyond the queue's bandwidth allocation. The `drop_pct` helps contextualize: 0.1% drops on a high-throughput queue may be acceptable, while 5% drops indicate severe congestion.

**Queue depth trending and congestion prediction:**
```spl
| mstats rate_avg("openconfig_qos.dropped_pkts") AS drop_rate rate_avg("openconfig_qos.transmit_octets") AS tx_rate WHERE index=gnmi_metrics BY host, name, queue_name span=5m earliest=-24h
| eval drops_per_min=round(drop_rate*60, 0)
| eval tx_mbps=round(tx_rate*8/1000000, 1)
| lookup qos_policy.csv host name queue_name OUTPUT traffic_class
| where drops_per_min > 0
| timechart span=5m sum(drops_per_min) as total_drops by traffic_class
```

**Priority queue health (zero-tolerance):**
```spl
| mstats rate_avg("openconfig_qos.dropped_pkts") AS drop_rate WHERE index=gnmi_metrics BY host, name, queue_name span=1m
| eval drops_per_min=round(drop_rate*60, 0)
| where drops_per_min > 0
| lookup qos_policy.csv host name queue_name OUTPUT traffic_class priority
| where priority="strict-priority"
| eval alert_msg="CRITICAL: Drops in strict-priority queue ".queue_name." on ".host.":".name." (".traffic_class.") — ".drops_per_min." drops/min"
| sort -drops_per_min
```

### Step 3 — Validate
(a) On the device, check queue counters: `show queuing interface <intf>` (NX-OS), `show platform hardware fed switch active qos queue stats interface <intf>` (Cisco), or `show qos interface <intf>` (Arista). Compare drop counts with the `mstats` rate.
(b) Verify QoS policy mapping: the `traffic_class` in the lookup should match the DSCP-to-queue mapping configured on the device.
(c) Generate a controlled test: saturate a link while sending voice traffic. Verify that best-effort drops appear but voice drops do not (if QoS is correctly configured).

### Step 4 — Operationalize
Dashboard ("Network — QoS Queue Health"):
- Row 1 — Single-value tiles: "Priority queue drops (1h)", "Interfaces with any drops", "Worst drop rate (%)", "Traffic classes affected".
- Row 2 — Table: host, interface, queue, traffic_class, drops_per_min, drop_pct, severity.
- Row 3 — Timechart: drops by traffic class over 24h (stacked area).
- Row 4 — Interface detail: selected interface showing all queues with tx rate and drop rate.

Alerting:
- Critical (any drops in strict-priority/EF queue): real-time alert — voice quality is being impacted.
- High (> 1% drops in video/AF41 queue for 5+ minutes): alert — video conferencing affected.
- Warning (> 5% drops in any queue sustained for 15+ minutes): capacity issue.

Runbook:
1. **Voice queue drops**: Verify QoS policy is correctly applied on all interfaces in the path. Check that voice traffic is correctly classified (DSCP 46/EF). If policy is correct, the link is oversubscribed — upgrade or engineer traffic away.
2. **Best-effort drops during business hours**: Expected if the link is at capacity. Consider implementing WRED to drop proactively before tail-drop. If drops are excessive, upgrade the link.

### Step 5 — Troubleshooting

- **QoS metrics not available via gNMI** — Some platforms don't expose QoS counters through OpenConfig. Try vendor-native YANG paths or fall back to SNMP (CISCO-CLASS-BASED-QOS-MIB).

- **All drops show in one queue** — If the device uses a single default queue (no QoS configured), all drops appear there. This means QoS is not enabled — all traffic classes share bandwidth equally.

- **Drop rate is zero but users report quality issues** — Drops may occur at a different point in the network (upstream, core, or WAN link). Trace the traffic path and monitor QoS at every hop.

## SPL

```spl
| mstats rate_avg("openconfig_qos.dropped_pkts") AS drops_per_sec, rate_avg("openconfig_qos.transmit_pkts") AS tx_per_sec WHERE index=gnmi_metrics BY host, interface_id, queue_name span=1m
| eval drop_pct=if(tx_per_sec>0, round(drops_per_sec*100/(drops_per_sec+tx_per_sec), 2), 0)
| where drops_per_sec > 0
| table _time, host, interface_id, queue_name, drops_per_sec, tx_per_sec, drop_pct
| sort -drop_pct
```

## Visualization

Bar chart (drops by queue class), Line chart (drop rate over time per queue), Table (queues with active drops), Heatmap (drop severity across fabric).

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
