<!-- AUTO-GENERATED from UC-5.11.6.json — DO NOT EDIT -->

---
id: "5.11.6"
title: "QoS Queue Depth and Drop Streaming"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.11.6 · QoS Queue Depth and Drop Streaming

## Description

SNMP-polled QoS counters miss microbursts entirely — a 100ms queue overflow causes packet loss that a 5-minute poll never sees. gNMI SAMPLE subscriptions to `/qos/interfaces/interface/output/queues/queue/state` at 10-second intervals capture queue depth and transmit/drop counters at a granularity that reveals microburst patterns, misclassified traffic, and under-provisioned queues.

## Value

SNMP-polled QoS counters miss microbursts entirely — a 100ms queue overflow causes packet loss that a 5-minute poll never sees. gNMI SAMPLE subscriptions to `/qos/interfaces/interface/output/queues/queue/state` at 10-second intervals capture queue depth and transmit/drop counters at a granularity that reveals microburst patterns, misclassified traffic, and under-provisioned queues.

## Implementation

Subscribe to QoS queue state at 10-30s intervals. Focus on high-priority queues (voice, video, control-plane) where any drops indicate a problem. For best-effort queues, baseline normal drop rates and alert on 2x deviation. Correlate drops with interface utilization (UC-5.11.1) to distinguish congestion drops from policy drops. Use `drop_pct` to identify queues with systematic under-provisioning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/qos/interfaces/interface/output/queues/queue/state` (transmit-pkts, dropped-pkts); Telegraf metric: `openconfig_qos`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to QoS queue state at 10-30s intervals. Focus on high-priority queues (voice, video, control-plane) where any drops indicate a problem. For best-effort queues, baseline normal drop rates and alert on 2x deviation. Correlate drops with interface utilization (UC-5.11.1) to distinguish congestion drops from policy drops. Use `drop_pct` to identify queues with systematic under-provisioning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats rate_avg("openconfig_qos.dropped_pkts") AS drops_per_sec, rate_avg("openconfig_qos.transmit_pkts") AS tx_per_sec WHERE index=gnmi_metrics BY host, interface_id, queue_name span=1m
| eval drop_pct=if(tx_per_sec>0, round(drops_per_sec*100/(drops_per_sec+tx_per_sec), 2), 0)
| where drops_per_sec > 0
| table _time, host, interface_id, queue_name, drops_per_sec, tx_per_sec, drop_pct
| sort -drop_pct
```

Understanding this SPL

**QoS Queue Depth and Drop Streaming** — SNMP-polled QoS counters miss microbursts entirely — a 100ms queue overflow causes packet loss that a 5-minute poll never sees. gNMI SAMPLE subscriptions to `/qos/interfaces/interface/output/queues/queue/state` at 10-second intervals capture queue depth and transmit/drop counters at a granularity that reveals microburst patterns, misclassified traffic, and under-provisioned queues.

Documented **Data sources**: gNMI path: `/qos/interfaces/interface/output/queues/queue/state` (transmit-pkts, dropped-pkts); Telegraf metric: `openconfig_qos`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• `eval` defines or adjusts **drop_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where drops_per_sec > 0` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **QoS Queue Depth and Drop Streaming**): table _time, host, interface_id, queue_name, drops_per_sec, tx_per_sec, drop_pct
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

CIM and metrics: QoS drops use **mstats**; there is no default CIM QoS queue data model in most estates.


Step 3 — Validate
Compare drop counters in Splunk to queue-depth CLI or platform QoS show commands on a busy port; mark known congestion links before tuning thresholds.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (drops by queue class), Line chart (drop rate over time per queue), Table (queues with active drops), Heatmap (drop severity across fabric).

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

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
