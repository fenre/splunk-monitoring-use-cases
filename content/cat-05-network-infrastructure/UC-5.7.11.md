<!-- AUTO-GENERATED from UC-5.7.11.json — DO NOT EDIT -->

---
id: "5.7.11"
title: "sFlow Sampling Rate Validation and Collector Health"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.11 · sFlow Sampling Rate Validation and Collector Health

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Data Quality, Operations, Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch whether our traffic sampling stays steady over time. When the equipment quietly changes how much it samples or stops sending numbers, we notice quickly so our charts and alarms stay honest.*

---

## Description

Compares observed sFlow sampling metadata and record cadence per agent and time bucket against expectations so gaps, wild swings in declared sampling rate, or silent collectors surface before capacity or security views drift.

## Value

Capacity and observability owners keep normalized byte and packet estimates trustworthy for trending and chargeback, reduce blind spots when agents reboot or templates change, and shorten mean time to detect collector saturation or misconfigured sampling.

## Implementation

Land sFlow in Splunk with sampling-related information elements preserved; chart sampling_rate variance per agent; alert on missing buckets or conflicting rates across interfaces.

## Detailed Implementation

### Prerequisites
- Heavy Forwarder or intermediate collector running the Splunk Add-on for NetFlow (1838) with sFlow enabled on UDP ports documented for your deployment; agents on switches and routers exporting sFlow version 5.
- Documented target sampling policy per site (for example 1:512 on edge, 1:4096 on core) and list of agent management addresses expected to send datagrams.
- Baseline understanding that sFlow exports packet samples and counter samples; byte totals are statistical estimates—health checks focus on consistency of sampling metadata and steady datagram arrival, not absolute precision.

### Step 1 — Configure data collection
Verify agents resolve to stable `agent` or `exporter` fields and that `sampling_rate` (or equivalent) is extracted from counter-sample records. Enable DEBUG temporarily on the forwarder if templates omit sampling attributes; confirm firewall paths allow bidirectional UDP from every agent subnet to the collector cluster.

### Step 2 — Create the search
Clone the primary SPL into a scheduled report per collector `host`. Extend with `lookup sflow_policy.csv agent OUTPUT expected_rate` and flag `abs(avg_sampling_rate-expected_rate)>expected_rate*0.25`. Add a companion search `| timechart span=15m count by agent` for volume collapse detection.

### Step 3 — Validate
During a maintenance window, change sampling on one lab switch and confirm the dashboard reflects the new `sampling_rate` within two buckets. Simulate collector downtime and verify the missing-bucket alert fires.

### Step 4 — Operationalize
Publish a dashboard row for agents over threshold, a single-value tile for collectors with zero events in the prior hour, and weekly CSV exports for auditors proving sampling metadata continuity.

### Step 5 — Troubleshooting
If `sampling_rate` is always null, inspect IPFIX/sFlow template decoding logs from the add-on and upgrade to a build that includes your vendor enterprise fields. Bursts of duplicate agents often indicate network address translation in front of the collector—normalize using syslog or DHCP correlation.

## SPL

```spl
index=netflow sourcetype="stream:netflow" OR sourcetype="netflow"
| bin _time span=15m
| stats count dc(agent) as agents dc(src) as uniq_src dc(dest) as uniq_dest,
    values(sampling_rate) as sampling_rates,
    avg(if(isnum(sampling_rate), sampling_rate, null())) as avg_sampling_rate,
    sum(bytes) as total_bytes
  by _time, host
| eval sampling_rates_mv=mvjoin(sampling_rates, ",")
| where isnull(avg_sampling_rate) OR mvcount(sampling_rates)>3 OR count<10
| sort _time
| head 200
```

## Visualization

Row 1: timechart of record count per collector host; Row 2: table of agent, avg_sampling_rate, sampling_rates_mv, total_bytes; Row 3: scatter of uniq_src vs count to spot starvation.

## Known False Positives

Short maintenance windows, SNMP polling storms, or intermittent routing asymmetry can suppress samples without a faulty collector. Agents that export only counter samples may lack `sampling_rate` on every record. Burst traffic can legitimately change effective sampling when hardware buffers fill.

## References

- [Splunk Documentation: Get Started with NetFlow](https://docs.splunk.com/Documentation/NetFlow/)
- [RFC 3176 — InMon Corporation's sFlow](https://www.rfc-editor.org/rfc/rfc3176)
