---
id: "5.11.1"
title: "Interface Utilization via gNMI Streaming Counters"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.11.1 · Interface Utilization via gNMI Streaming Counters

## Description

SNMP polls interface counters every 5 minutes at best — microbursts and sub-minute congestion are invisible. gNMI SAMPLE subscriptions stream `/interfaces/interface/state/counters` at 10-30 second intervals, giving you near-real-time ingress/egress byte and packet rates. This catches congestion events that SNMP misses and enables capacity planning based on true peak utilization rather than averaged-out polling data.

## Value

SNMP polls interface counters every 5 minutes at best — microbursts and sub-minute congestion are invisible. gNMI SAMPLE subscriptions stream `/interfaces/interface/state/counters` at 10-30 second intervals, giving you near-real-time ingress/egress byte and packet rates. This catches congestion events that SNMP misses and enables capacity planning based on true peak utilization rather than averaged-out polling data.

## Implementation

Deploy Telegraf on a dedicated collector. Configure `inputs.gnmi` with device addresses (port 57400 for IOS XR, 6030 for Arista EOS, 32767 for Junos). Subscribe to `/interfaces/interface/state/counters` at `sample_interval = "30s"`. Output to Splunk HEC using `splunkmetric` format into a metrics index. Use `mstats` with `rate_avg()` to compute per-second rates from cumulative counters.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/interfaces/interface/state/counters` (OpenConfig), Telegraf metric: `openconfig_interfaces`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy Telegraf on a dedicated collector. Configure `inputs.gnmi` with device addresses (port 57400 for IOS XR, 6030 for Arista EOS, 32767 for Junos). Subscribe to `/interfaces/interface/state/counters` at `sample_interval = "30s"`. Output to Splunk HEC using `splunkmetric` format into a metrics index. Use `mstats` with `rate_avg()` to compute per-second rates from cumulative counters.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats rate_avg("openconfig_interfaces.in_octets") AS in_bps, rate_avg("openconfig_interfaces.out_octets") AS out_bps WHERE index=gnmi_metrics BY host, name span=1m
| eval in_mbps=round(in_bps*8/1000000, 1), out_mbps=round(out_bps*8/1000000, 1)
| where in_mbps > 800 OR out_mbps > 800
| table _time, host, name, in_mbps, out_mbps
| sort -in_mbps
```

Understanding this SPL

**Interface Utilization via gNMI Streaming Counters** — SNMP polls interface counters every 5 minutes at best — microbursts and sub-minute congestion are invisible. gNMI SAMPLE subscriptions stream `/interfaces/interface/state/counters` at 10-30 second intervals, giving you near-real-time ingress/egress byte and packet rates. This catches congestion events that SNMP misses and enables capacity planning based on true peak utilization rather than averaged-out polling data.

Documented **Data sources**: gNMI path: `/interfaces/interface/state/counters` (OpenConfig), Telegraf metric: `openconfig_interfaces`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• `eval` defines or adjusts **in_mbps** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where in_mbps > 800 OR out_mbps > 800` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Interface Utilization via gNMI Streaming Counters**): table _time, host, name, in_mbps, out_mbps
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (Mbps in/out per interface), Heatmap (utilization % across fabric), Single value (peak utilization).

## SPL

```spl
| mstats rate_avg("openconfig_interfaces.in_octets") AS in_bps, rate_avg("openconfig_interfaces.out_octets") AS out_bps WHERE index=gnmi_metrics BY host, name span=1m
| eval in_mbps=round(in_bps*8/1000000, 1), out_mbps=round(out_bps*8/1000000, 1)
| where in_mbps > 800 OR out_mbps > 800
| table _time, host, name, in_mbps, out_mbps
| sort -in_mbps
```

## Visualization

Line chart (Mbps in/out per interface), Heatmap (utilization % across fabric), Single value (peak utilization).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
