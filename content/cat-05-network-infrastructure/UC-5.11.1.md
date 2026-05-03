<!-- AUTO-GENERATED from UC-5.11.1.json — DO NOT EDIT -->

---
id: "5.11.1"
title: "Interface Utilization via gNMI Streaming Counters"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.11.1 · Interface Utilization via gNMI Streaming Counters

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We help you see how full each network port is in near real time, so bursty problems show up long before a slow, old-style poll would notice.*

---

## Description

SNMP polls interface counters every 5 minutes at best — microbursts and sub-minute congestion are invisible. gNMI SAMPLE subscriptions stream `/interfaces/interface/state/counters` at 10-30 second intervals, giving you near-real-time ingress/egress byte and packet rates. This catches congestion events that SNMP misses and enables capacity planning based on true peak utilization rather than averaged-out polling data.

## Value

Network operations teams achieve near-real-time interface utilization visibility via 30-second gNMI streaming, capturing microbursts and congestion that SNMP polling misses, enabling capacity planning based on true peak utilization.

## Implementation

Deploy Telegraf on a dedicated collector. Configure `inputs.gnmi` with device addresses (port 57400 for IOS XR, 6030 for Arista EOS, 32767 for Junos). Subscribe to `/interfaces/interface/state/counters` at `sample_interval = "30s"`. Output to Splunk HEC using `splunkmetric` format into a metrics index. Use `mstats` with `rate_avg()` to compute per-second rates from cumulative counters.

## Detailed Implementation

### Prerequisites
- Telegraf deployed on a dedicated Linux collector with the `inputs.gnmi` plugin. Minimum Telegraf 1.20+ for stable gNMI support. Install via package manager or Docker (`docker run telegraf:latest`).
- Network devices must support gNMI with OpenConfig YANG models. Supported platforms and gNMI ports: Cisco IOS-XR (57400), Cisco NX-OS 9.3+ (50051), Arista EOS 4.20+ (6030), Juniper Junos 18.3+ (32767/50051), Nokia SR Linux (57400). Enable gRPC/gNMI on each device: IOS-XR: `grpc port 57400 no-tls` (or with TLS); NX-OS: `feature grpc`; Arista: `management api gnmi transport grpc default`.
- OpenConfig path for interface counters: `/interfaces/interface/state/counters`. Key leaf nodes: `in-octets`, `out-octets`, `in-unicast-pkts`, `out-unicast-pkts`, `in-errors`, `out-errors`, `in-discards`, `out-discards`. These are cumulative 64-bit counters — Splunk `mstats rate_avg()` converts them to per-second rates.
- Splunk metrics index `gnmi_metrics` must be created (`index type = metric`). Configure Splunk HEC with a token targeting this metrics index, using the `splunkmetric` data format.
- Build an `interface_capacity.csv` lookup mapping `host` + interface `name` to link speed in Mbps: `host,name,speed_mbps,role,description` (e.g., `spine-01,Ethernet1/1,100000,fabric-uplink,Spine to Leaf-01`).
- License estimate: each interface streamed at 30s intervals generates ~2880 data points/day per metric. A 100-switch fabric with 48 interfaces each and 8 counter metrics = ~110M data points/day. Size the metrics index accordingly.

### Step 1 — Configure data collection
Telegraf `inputs.gnmi` configuration:
```toml
[[inputs.gnmi]]
  addresses = ["spine-01:57400", "leaf-01:6030"]
  username = "$GNMI_USER"
  password = "$GNMI_PASS"
  redial = "10s"
  [[inputs.gnmi.subscription]]
    name = "openconfig_interfaces"
    origin = "openconfig"
    path = "/interfaces/interface/state/counters"
    subscription_mode = "sample"
    sample_interval = "30s"
```

Verify data arrival in Splunk:
```spl
| mcatalog values(metric_name) WHERE index=gnmi_metrics host=spine-01
| search metric_name="openconfig_interfaces*"
```
You should see metric names like `openconfig_interfaces.in_octets`, `openconfig_interfaces.out_octets`, etc. If empty: check Telegraf logs (`journalctl -u telegraf`), gRPC connectivity (`grpcurl -plaintext <device>:57400 list`), and HEC token permissions.

Verify per-interface dimensions:
```spl
| mcatalog values(name) WHERE index=gnmi_metrics metric_name="openconfig_interfaces.in_octets" host=spine-01
```
The `name` dimension should list all interfaces (Ethernet1/1, Ethernet1/2, etc.).

### Step 2 — Create the search and alert

**Primary search — Interface utilization with capacity percentage:**
```spl
| mstats rate_avg("openconfig_interfaces.in_octets") AS in_bps rate_avg("openconfig_interfaces.out_octets") AS out_bps WHERE index=gnmi_metrics BY host, name span=1m
| eval in_mbps=round(in_bps*8/1000000, 1)
| eval out_mbps=round(out_bps*8/1000000, 1)
| lookup interface_capacity.csv host name OUTPUT speed_mbps role description
| eval in_util_pct=if(isnotnull(speed_mbps), round(100*in_mbps/speed_mbps, 1), null())
| eval out_util_pct=if(isnotnull(speed_mbps), round(100*out_mbps/speed_mbps, 1), null())
| eval max_util=max(in_util_pct, out_util_pct)
| where max_util > 70 OR in_mbps > 800 OR out_mbps > 800
| eval status=case(max_util > 95, "CRITICAL", max_util > 85, "WARNING", max_util > 70, "Monitor", 1==1, "OK")
| sort -max_util
```

#### Understanding this SPL: `rate_avg()` converts cumulative octet counters into per-second byte rates. Multiplying by 8 and dividing by 1M gives Mbps. The `interface_capacity.csv` lookup provides the link speed so we can calculate utilization percentage — far more meaningful than raw Mbps. A 100G link at 800 Mbps (0.8% utilization) is fine; a 1G link at 800 Mbps (80% utilization) needs attention.

**Microburst detection (sub-minute peaks):**
```spl
| mstats max("openconfig_interfaces.in_octets") AS peak_in max("openconfig_interfaces.out_octets") AS peak_out WHERE index=gnmi_metrics BY host, name span=30s
| eval peak_in_mbps=round(peak_in*8/1000000, 1)
| eval peak_out_mbps=round(peak_out*8/1000000, 1)
| lookup interface_capacity.csv host name OUTPUT speed_mbps
| eval peak_util=if(isnotnull(speed_mbps), round(100*max(peak_in_mbps, peak_out_mbps)/speed_mbps, 1), null())
| where peak_util > 90
| sort -peak_util
| head 20
```

#### Understanding this SPL: Microbursts are brief traffic spikes (milliseconds to seconds) that exceed interface capacity and cause packet drops, even when average utilization is low. 30-second gNMI streaming captures these bursts that SNMP's 5-minute polling completely misses. This is one of the primary advantages of streaming telemetry over SNMP.

**Fabric-wide utilization heatmap:**
```spl
| mstats rate_avg("openconfig_interfaces.in_octets") AS in_bps rate_avg("openconfig_interfaces.out_octets") AS out_bps WHERE index=gnmi_metrics BY host, name span=5m
| lookup interface_capacity.csv host name OUTPUT speed_mbps role
| where role="fabric-uplink" OR role="spine-link"
| eval util_pct=round(100*max(in_bps*8/1000000, out_bps*8/1000000)/speed_mbps, 1)
| chart avg(util_pct) BY host, name
```

### Step 3 — Validate
(a) On a router CLI, check interface counters: `show interface Ethernet1/1 | include rate`. Compare the displayed bit-rate with the `mstats` `in_mbps`/`out_mbps` for the same interface and time. They should be within 5-10% (differences due to counter wrap timing and sampling interval alignment).
(b) Generate a known load: run iperf3 between two hosts through a monitored link and verify the utilization appears in the search results.
(c) Verify capacity mapping: spot-check 10 interfaces in `interface_capacity.csv` against `show interface` output for speed.
(d) Check counter wrap: 64-bit counters on 100G links wrap every ~46 years, so wrap is not a practical concern. On older 32-bit counters (some legacy SNMP), wrapping occurs at ~34 seconds at 1 Gbps.

### Step 4 — Operationalize
Dashboard ("Network — gNMI Interface Utilization"):
- Row 1 — Single-value tiles: "Interfaces > 80% util", "Peak interface utilization", "Total monitored interfaces", "Active gNMI devices".
- Row 2 — Line chart: selected interface in/out Mbps over 1 hour with capacity line overlay.
- Row 3 — Heatmap: all fabric uplinks by host and interface, color-coded by utilization percentage.
- Row 4 — Microburst alerts table: host, interface, peak_util, timestamp.

Alerting:
- Critical (utilization > 95% sustained for 5+ minutes): immediate capacity review — possible packet loss impacting applications.
- Warning (utilization > 85% sustained for 15+ minutes): capacity planning trigger — schedule upgrade or traffic engineering.
- Microburst (peak > 90% in any 30s interval): investigate application traffic patterns.

Runbook (owner: Network Operations):
1. **Sustained high utilization**: Identify top talkers using flow data (UC-5.7.1). Check for hash polarization (ECMP/LAG not distributing evenly). If consistent, upgrade link speed or add parallel links.
2. **Microburst detected**: Correlate with QoS queue drops (UC-5.11.6). Microbursts often come from synchronized application behavior (database checkpoints, backup starts). Apply traffic shaping or QoS marking to smooth the bursts.

### Step 5 — Troubleshooting

- **`mstats` returns no data** — Verify: (1) the metrics index name is correct (`gnmi_metrics`), (2) Telegraf output is configured for `splunkmetric` format, (3) HEC token targets the metrics index (not an events index). Check with `| mcatalog values(metric_name) WHERE index=gnmi_metrics`.

- **Rate values are negative or extremely high** — Counter reset (device reboot) causes a discontinuity. `rate_avg()` handles most resets but may produce a single anomalous point. Add `| where in_bps >= 0 AND in_bps < 100000000000` to filter artifacts (100G maximum).

- **Interface names don't match between gNMI and CLI** — gNMI uses the OpenConfig naming (e.g., `Ethernet1/1`), which may differ from CLI output (e.g., `eth1/1` or `ge-0/0/0`). Standardize in the capacity lookup.

- **gNMI connection drops intermittently** — Check the `redial` interval in Telegraf config. Certificate expiry (if using TLS) is a common cause. Monitor Telegraf logs for `rpc error: code = Unavailable`.

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

## Known False Positives

Telemetry pauses during device reboots, cert renewals, or transport changes; subscription restarts and path renames can look like drops without a live fault.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
