<!-- AUTO-GENERATED from UC-5.11.1.json — DO NOT EDIT -->

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

CIM and metrics: the gNMI search above uses a **metrics** index with `mstats`. The `cimSpl` field is an optional `tstats` over `Network_Traffic.All_Traffic` if that CIM data model is mapped and accelerated.


Step 3 — Validate
On the device CLI or element manager, read interface bit rates for the same second interface name and check they track with the `mstats` `openconfig_*` series after unit conversion. Confirm the metrics index, Telegraf host, and `name` (interface) dimension line up with inventory.

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

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| eval total_bytes=bytes_in+bytes_out
| sort -total_bytes
```

## Visualization

Line chart (Mbps in/out per interface), Heatmap (utilization % across fabric), Single value (peak utilization).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
