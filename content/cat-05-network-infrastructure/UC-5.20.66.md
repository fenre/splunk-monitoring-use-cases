<!-- AUTO-GENERATED from UC-5.20.66.json — DO NOT EDIT -->

---
id: "5.20.66"
title: "IPv6 NetFlow/IPFIX Template Validation and Exporter Health"
status: "verified"
criticality: "high"
splunkPillar: "ITSI"
---

# UC-5.20.66 · IPv6 NetFlow/IPFIX Template Validation and Exporter Health

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** ITSI &middot; **Type:** Availability, Compliance &middot; **Wave:** Walk &middot; **Status:** Verified

*Imagine we have security cameras (flow exporters) watching traffic going through our building. Some of the older cameras (NetFlow v5) can only see regular-sized visitors (IPv4) but cannot see visitors entering through the new taller doors (IPv6). We check which cameras can see both types of visitors, and which ones have a blind spot for the taller doors — because anyone who knows about the blind spot can walk right in without being recorded.*

---

## Description

Validates that all NetFlow/IPFIX exporters are sending IPv6 flow records and detects exporters with zero or minimal IPv6 visibility. NetFlow v5 (the most common version in legacy deployments) does not support IPv6 at all. Even on v9/IPFIX deployments, IPv6 templates and interface-level monitors must be explicitly configured. Without IPv6 flow data, security and capacity analyses are blind to all IPv6 traffic — attackers can use IPv6 to move laterally with no flow-based detection.

## Value

Flow data is the backbone of network security and capacity monitoring. If IPv6 flows are not being exported, all IPv6 traffic is invisible to flow-based detection systems, threat hunting, and capacity planning. This creates an asymmetric blind spot — attackers who route traffic over IPv6 bypass all flow-based detections. Identifying and fixing IPv6 flow export gaps closes this critical visibility gap.

## Implementation

Audit all NetFlow/IPFIX exporters for IPv6 template support. Identify exporters sending zero IPv6 flows. Verify IPv6 flow monitors are applied to all dual-stack interfaces. Compare IPv4 and IPv6 flow export rates against expected traffic mix.

## Detailed Implementation

### Prerequisites
- NetFlow v9 or IPFIX exporters deployed on all monitored network segments.
- Splunk NetFlow collector (Splunk Add-on for NetFlow or Splunk Stream) receiving and parsing flow records.
- Inventory of all flow exporters with their NetFlow version and IPv6 configuration status.

### Step 1 — Configure data collection

**Cisco IOS-XE — IPv6 Flexible NetFlow configuration:**
```
flow record IPV6-RECORD
 match ipv6 source address
 match ipv6 destination address
 match ipv6 flow-label
 match ipv6 next-hop address
 match transport source-port
 match transport destination-port
 match interface input
 collect counter bytes long
 collect counter packets long
 collect timestamp sys-uptime first
 collect timestamp sys-uptime last

flow monitor IPV6-MONITOR
 record IPV6-RECORD
 exporter SPLUNK-EXPORTER
 cache timeout active 60

interface GigabitEthernet0/0
 ipv6 flow monitor IPV6-MONITOR input
 ipv6 flow monitor IPV6-MONITOR output
 ip flow monitor IPV4-MONITOR input
 ip flow monitor IPV4-MONITOR output
```
Note: both `ip flow monitor` and `ipv6 flow monitor` must be applied to dual-stack interfaces.

**Juniper Junos — IPv6 jFlow:**
```
set services flow-monitoring version-ipfix template IPV6-TEMPLATE ipv6-template
set forwarding-options sampling instance SAMPLE-INST family inet6 output flow-server 10.0.0.1 port 9995 version-ipfix template IPV6-TEMPLATE
set forwarding-options sampling instance SAMPLE-INST family inet6 output inline-jflow source-address 10.0.0.2
```

**Create flow exporter inventory lookup:**
```csv
exporter_ip,hostname,netflow_version,ipv6_configured,segment
10.1.1.1,rtr-core-01,v9,true,core
10.1.1.2,rtr-dist-01,v9,true,distribution
10.1.1.3,rtr-legacy-01,v5,false,legacy
```
Upload as `flow_exporters.csv`.

**Verification:**
```spl
index=network sourcetype="netflow" earliest=-1h
| stats count by exporter_ip
| lookup flow_exporters.csv exporter_ip
| table exporter_ip, hostname, netflow_version, ipv6_configured, count
```

### Step 2 — Create the search and alert

**Zero IPv6 flow detection:**
```spl
index=network sourcetype="netflow" earliest=-24h
| eval has_ipv6=if(isnotnull(sourceIPv6Address) OR match(src, ":"), 1, 0)
| stats count(eval(has_ipv6=1)) as v6_flows count(eval(has_ipv6=0)) as v4_flows by exporter_ip
| lookup flow_exporters.csv exporter_ip OUTPUT hostname, netflow_version, ipv6_configured
| where v6_flows=0 AND ipv6_configured="true"
| eval alert="Exporter " . hostname . " (" . exporter_ip . ") is configured for IPv6 but sent 0 IPv6 flows in 24h — investigate flow monitor application"
```

**NetFlow v5 inventory (no IPv6 capability):**
```spl
| inputlookup flow_exporters.csv
| where netflow_version="v5"
| eval recommendation="UPGRADE TO v9/IPFIX — NetFlow v5 provides zero IPv6 visibility. Segment '" . segment . "' is completely blind to IPv6 traffic."
| table exporter_ip, hostname, segment, recommendation
```

**IPv6 flow sampling rate parity:**
```spl
index=network sourcetype="netflow" earliest=-24h
| eval ip_version=if(isnotnull(sourceIPv6Address) OR match(src, ":"), "IPv6", "IPv4")
| stats count as flows avg(sampling_rate) as avg_sample_rate by exporter_ip, ip_version
| xyseries exporter_ip ip_version avg_sample_rate
| where IPv4 != IPv6 AND isnotnull(IPv4) AND isnotnull(IPv6)
| eval issue="Sampling rate mismatch: IPv4=" . IPv4 . " vs IPv6=" . IPv6 . " — IPv6 traffic may be under/over-represented"
```

### Step 3 — Validate
(a) **v5 detection.** Verify all known NetFlow v5 exporters appear in the v5 inventory search.

(b) **Zero-flow accuracy.** On a router with IPv6 flow monitors configured, verify IPv6 flows appear. On a router without, verify it appears in the zero-flow alert.

(c) **Interface coverage.** On a router with multiple interfaces, verify IPv6 flow monitors are applied to all interfaces (not just the primary).

### Step 4 — Operationalize

**Dashboard** ("IPv6 — Flow Visibility Audit"):
- Row 1 — Single-values: total exporters, exporters with IPv6, exporters without IPv6 (NetFlow v5), IPv6 flow gap %.
- Row 2 — Table: exporters sorted by IPv6 flow percentage (worst first).
- Row 3 — Stacked bar: IPv4 vs IPv6 flow volume per exporter.
- Row 4 — v5 upgrade candidates: exporters still running NetFlow v5.

**Scheduling:** Exporter audit daily. Zero-flow alert every 4 hours. v5 inventory weekly.

**Runbook:**
1. Zero IPv6 flows on v9/IPFIX exporter: check `show flow monitor IPV6-MONITOR cache`. If empty, verify `ipv6 flow monitor` is applied to interfaces.
2. NetFlow v5 exporter: plan upgrade to v9 or IPFIX. Document risk: IPv6 traffic on this segment is unmonitored.
3. Sampling rate mismatch: align IPv4 and IPv6 sampling rates for comparable data.

### Step 5 — Troubleshooting

- **Template export interval** — IPv6 templates are larger than IPv4. If the template refresh interval is too long (>30 minutes), the collector may not have the current IPv6 template and will drop IPv6 flow records. Set template refresh to 300 seconds.

- **IPv6 flow record size** — IPv6 flow records are approximately 24 bytes larger per record than IPv4 (128-bit vs 32-bit addresses x2). Verify that collector bandwidth and storage can handle the additional volume.

- **Flexible NetFlow vs traditional NetFlow** — On Cisco IOS-XE, Flexible NetFlow supports IPv6 natively. Traditional NetFlow (ip flow-export) may not. Verify the router supports Flexible NetFlow for IPv6.

- **Flow monitor direction** — IPv6 flow monitors must be applied in both `input` and `output` directions on each interface. Missing the output direction means only inbound traffic is exported.

## SPL

```spl
index=network sourcetype="netflow" earliest=-24h
| eval has_ipv6=if(isnotnull(sourceIPv6Address) OR match(src, ":"), 1, 0)
| stats count(eval(has_ipv6=1)) as ipv6_flows count(eval(has_ipv6=0)) as ipv4_flows by exporter_ip
| eval ipv6_pct=round(ipv6_flows / (ipv6_flows + ipv4_flows) * 100, 1)
| eval status=case(
    ipv6_flows=0, "NO IPv6 FLOWS — exporter not configured for IPv6 (NetFlow v5 or missing IPv6 template)",
    ipv6_pct < 1, "LOW — IPv6 flows present but very few; check if IPv6 monitor applied to all interfaces",
    1=1, "OK")
| sort ipv6_pct
```

## Visualization

(1) Table: exporters sorted by IPv6 flow percentage (ascending — worst first). (2) Single-value: count of exporters with zero IPv6 flows. (3) Bar chart: IPv4 vs IPv6 flow count per exporter. (4) Trend: IPv6 flow percentage over 30 days.

## Known False Positives

**IPv4-only segments.** Exporters on segments with no IPv6 deployment will legitimately show zero IPv6 flows. Tag these exporters in the exporter inventory to exclude from the alert.

**Sampled flows.** Exporters with high sampling rates (1-in-1000+) may show very few IPv6 flows on segments with low IPv6 traffic. The flows exist but are undersampled.

**Asymmetric routing.** If IPv6 traffic uses a different path than IPv4 (common in dual-stack routing), some exporters see only one version.

## References

- [RFC 7012 — Information Model for IP Flow Information Export (IPFIX IPv6 information elements)](https://www.rfc-editor.org/rfc/rfc7012)
- [RFC 9099 — Operational Security Considerations for IPv6 Networks (§2.6.1.2 — flow visibility)](https://www.rfc-editor.org/rfc/rfc9099)
