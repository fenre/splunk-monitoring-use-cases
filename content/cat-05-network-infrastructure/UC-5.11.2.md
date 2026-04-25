<!-- AUTO-GENERATED from UC-5.11.2.json — DO NOT EDIT -->

---
id: "5.11.2"
title: "Interface Error and Discard Streaming"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.11.2 · Interface Error and Discard Streaming

## Description

CRC errors, input errors, and output discards often precede link failure or indicate a bad transceiver, duplex mismatch, or MTU issue. Streaming these counters at 30-second intervals via gNMI catches error bursts that 5-minute SNMP polls average away. A sudden spike in `in_fcs_errors` on a 100G spine link demands immediate investigation — it could be a failing optic about to take down a leaf.

## Value

CRC errors, input errors, and output discards often precede link failure or indicate a bad transceiver, duplex mismatch, or MTU issue. Streaming these counters at 30-second intervals via gNMI catches error bursts that 5-minute SNMP polls average away. A sudden spike in `in_fcs_errors` on a 100G spine link demands immediate investigation — it could be a failing optic about to take down a leaf.

## Implementation

Subscribe to `/interfaces/interface/state/counters` at 30s sample intervals. Use `rate_avg()` to convert cumulative counters to per-second rates. Alert on any non-zero FCS error rate (indicates physical-layer problems). Alert on discard rates exceeding baseline (indicates congestion or QoS policy drops). Correlate with optic health (UC-5.11.5) for root cause.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Telegraf (`inputs.gnmi` plugin) → Splunk HEC.
• Ensure the following data sources are available: gNMI path: `/interfaces/interface/state/counters` (in-errors, out-errors, in-discards, out-discards, in-fcs-errors), Telegraf metric: `openconfig_interfaces`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Subscribe to `/interfaces/interface/state/counters` at 30s sample intervals. Use `rate_avg()` to convert cumulative counters to per-second rates. Alert on any non-zero FCS error rate (indicates physical-layer problems). Alert on discard rates exceeding baseline (indicates congestion or QoS policy drops). Correlate with optic health (UC-5.11.5) for root cause.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
| mstats rate_avg("openconfig_interfaces.in_errors") AS err_rate, rate_avg("openconfig_interfaces.in_fcs_errors") AS fcs_rate, rate_avg("openconfig_interfaces.out_discards") AS discard_rate WHERE index=gnmi_metrics BY host, name span=1m
| where err_rate > 0 OR fcs_rate > 0 OR discard_rate > 10
| table _time, host, name, err_rate, fcs_rate, discard_rate
| sort -fcs_rate
```

Understanding this SPL

**Interface Error and Discard Streaming** — CRC errors, input errors, and output discards often precede link failure or indicate a bad transceiver, duplex mismatch, or MTU issue. Streaming these counters at 30-second intervals via gNMI catches error bursts that 5-minute SNMP polls average away. A sudden spike in `in_fcs_errors` on a 100G spine link demands immediate investigation — it could be a failing optic about to take down a leaf.

Documented **Data sources**: gNMI path: `/interfaces/interface/state/counters` (in-errors, out-errors, in-discards, out-discards, in-fcs-errors), Telegraf metric: `openconfig_interfaces`. **App/TA** (typical add-on context): Telegraf (`inputs.gnmi` plugin) → Splunk HEC. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: gnmi_metrics.

**Pipeline walkthrough**

• Uses `mstats` to query metrics indexes (pre-aggregated metric data).
• Filters the current rows with `where err_rate > 0 OR fcs_rate > 0 OR discard_rate > 10` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **Interface Error and Discard Streaming**): table _time, host, name, err_rate, fcs_rate, discard_rate
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

CIM and metrics: this panel uses gNMI counter metrics in a **metrics** index. There is no standard CIM line-rate error counter; keep `cimModels` as N/A unless you add custom CIM fields.


Step 3 — Validate
Compare error and discard `mstats` series to a short SNMP walk or `show interface` counters on the same port; confirm baseline noise before alerting.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (error rates over time), Table (interfaces with active errors), Heatmap (errors across fabric).

## SPL

```spl
| mstats rate_avg("openconfig_interfaces.in_errors") AS err_rate, rate_avg("openconfig_interfaces.in_fcs_errors") AS fcs_rate, rate_avg("openconfig_interfaces.out_discards") AS discard_rate WHERE index=gnmi_metrics BY host, name span=1m
| where err_rate > 0 OR fcs_rate > 0 OR discard_rate > 10
| table _time, host, name, err_rate, fcs_rate, discard_rate
| sort -fcs_rate
```

## Visualization

Line chart (error rates over time), Table (interfaces with active errors), Heatmap (errors across fabric).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
