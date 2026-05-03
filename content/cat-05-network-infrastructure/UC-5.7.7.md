<!-- AUTO-GENERATED from UC-5.7.7.json — DO NOT EDIT -->

---
id: "5.7.7"
title: "Protocol Distribution Analysis"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.7.7 · Protocol Distribution Analysis

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance

*We help you see what kinds of network traffic (web, video, file share, and so on) you are carrying so you can set fair rules and spot odd mixes that do not match policy.*

---

## Description

Understanding protocol mix helps validate network policies and detect unauthorized protocols (e.g., unexpected SSH, RDP, or P2P traffic).

## Value

Network and security teams monitor protocol distribution to detect unauthorized tunneling, VPN bypass attempts, protocol-based attacks, and infrastructure misconfigurations that alter the expected traffic mix.

## Implementation

Collect NetFlow/sFlow/IPFIX from routers and switches. Map port numbers to service names via lookup. Baseline protocol distribution. Alert on new protocols or significant shifts.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with `protocol` field (IP protocol number: TCP=6, UDP=17, ICMP=1, GRE=47, ESP=50, OSPF=89, etc.), `bytes`, `packets`, and traffic direction. Protocol distribution reveals the nature of network usage and can expose unauthorized tunneling or misconfigurations.
- Understand your expected protocol mix: typical enterprise networks are 70-85% TCP, 10-25% UDP, 1-5% ICMP, with small amounts of GRE, ESP (VPN), OSPF/EIGRP (routing). Significant deviations warrant investigation.
- Build a `protocol_names.csv` lookup mapping protocol numbers to names and expected usage: `protocol_num,protocol_name,expected_usage,risk_level` (e.g., `6,TCP,Normal,low`, `47,GRE,Tunneling,medium`, `50,ESP,VPN/IPsec,low`, `41,IPv6-in-IPv4,Tunneling,medium`).

### Step 1 — Configure data collection
Verify protocol field extraction:
```spl
index=netflow earliest=-15m
| stats count sum(bytes) as bytes by protocol
| sort -count
```
You should see protocol numbers (6, 17, 1 are the most common). If `protocol` is null, check your NetFlow template configuration on the exporter.

### Step 2 — Create the search and alert

**Primary search — Protocol distribution with anomaly detection:**
```spl
index=netflow earliest=-24h
| lookup protocol_names.csv protocol_num as protocol OUTPUT protocol_name expected_usage risk_level
| eval proto_label=if(isnotnull(protocol_name), protocol_name, "Proto-".protocol)
| bin _time span=1h
| stats sum(bytes) as bytes sum(packets) as pkts by _time, proto_label, risk_level
| eventstats sum(bytes) as total_bytes by _time
| eval pct=round(100*bytes/total_bytes, 2)
| eventstats avg(pct) as avg_pct stdev(pct) as std_pct by proto_label
| where pct > avg_pct + (3 * std_pct) AND pct > 1
| eval shift=round(pct - avg_pct, 1)
| sort -shift
```

#### Understanding this SPL: Tracks the percentage of each protocol relative to total traffic over 24 hours. When a protocol's share deviates by more than 3 standard deviations from its average, it's flagged. A sudden jump in GRE traffic could mean a new tunnel was established. An increase in ICMP could be a ping flood DDoS. An unexpected increase in protocol 50 (ESP) from non-VPN endpoints suggests unauthorized VPN usage.

**Unusual protocol detection — non-standard IP protocols:**
```spl
index=netflow earliest=-1h
| where NOT protocol IN (6, 17, 1, 2)
| lookup protocol_names.csv protocol_num as protocol OUTPUT protocol_name risk_level
| stats sum(bytes) as bytes sum(packets) as pkts dc(src) as sources dc(dest) as dests by protocol, protocol_name, risk_level
| eval bytes_MB=round(bytes/1048576, 1)
| sort -bytes
```

#### Understanding this SPL: Filters out the "big three" (TCP, UDP, ICMP, IGMP) to surface unusual protocols. Protocols like GRE (47), ESP (50), IPv6-in-IPv4 (41), SCTP (132), or proprietary protocols (>143) may indicate tunneling, VPN bypass, or experimental deployments that need governance.

**Protocol entropy analysis — per-source diversity:**
```spl
index=netflow earliest=-1h
| stats dc(protocol) as proto_count dc(dest_port) as port_count sum(bytes) as bytes by src
| where proto_count > 5
| lookup asset_inventory.csv ip as src OUTPUT hostname role
| eval src_label=if(isnotnull(hostname), hostname, src)
| sort -proto_count
| head 20
```

#### Understanding this SPL: Hosts that use many different IP protocols are unusual. Normal hosts use TCP, UDP, and maybe ICMP (3 protocols). A host using 5+ protocols could be running tunneling software, network tools, or could be compromised.

### Step 3 — Validate
(a) Compare protocol distribution to SNMP interface counters that break down by protocol (available on some platforms). The percentages should be similar.
(b) Verify the expected baseline: during normal business hours, TCP should dominate. If UDP > TCP consistently, you may have a VoIP-heavy or DNS-heavy network segment (which could be normal).
(c) Test: establish a GRE tunnel between two hosts and verify it appears in the unusual protocol detection results.

### Step 4 — Operationalize
Dashboard ("Network — Protocol Distribution"):
- Row 1 — Pie chart: protocol distribution by bytes (current hour).
- Row 2 — Timechart: stacked area chart of protocol percentages over 7 days.
- Row 3 — Unusual protocols table: protocol, name, risk_level, bytes, sources, destinations.
- Row 4 — Hosts with high protocol diversity: src, hostname, proto_count, protocols used.

Alerting:
- Critical (protocol 41/47 from non-network device, or unknown protocol > 100 MB): possible tunneling bypass — alert security.
- Warning (any protocol shift > 3 sigma sustained for 2+ hours): alert network operations.

Runbook:
1. **GRE/IPv6-in-IPv4 from endpoint**: Investigate for tunneling bypass (may be evading firewall inspection by encapsulating traffic). Check if the host is running tunneling software (Cloudflare Warp, Tailscale, etc.).
2. **Protocol 50 (ESP) from non-VPN endpoint**: Unauthorized IPsec VPN. Identify the remote endpoint and determine if it's a corporate-approved connection.
3. **Sudden UDP increase**: Check for DNS amplification attack (port 53 + high volume), NTP amplification (port 123), or new VoIP deployment.

### Step 5 — Troubleshooting

- **Protocol field shows only TCP and UDP** — Your NetFlow exporter may not include the IP protocol field in the flow template, or may aggregate all non-TCP/UDP traffic as "other". Check the flow record template on the exporter.

- **Protocol numbers don't match known protocols** — Verify the `protocol_names.csv` lookup covers IANA-assigned protocol numbers (https://www.iana.org/assignments/protocol-numbers). Numbers >143 are unassigned and highly suspicious.

- **GRE traffic expected (SD-WAN overlay)** — SD-WAN solutions (Cisco Viptela, Silver Peak, VMware VeloCloud) use GRE or IPsec tunnels. Add SD-WAN hub/edge device IPs to an exclusion list to avoid false positives.

**IPv6 Note:** ICMPv6 is architecturally critical for IPv6 — it carries NDP (Neighbor Discovery), Path MTU Discovery, and Multicast Listener Discovery. Unlike ICMP for IPv4, blocking ICMPv6 breaks IPv6 connectivity entirely. Ensure firewall policies permit at minimum ICMPv6 types 1-4 (Destination Unreachable, Packet Too Big, Time Exceeded, Parameter Problem) and types 133-137 (RS, RA, NS, NA, Redirect). See RFC 4890 for filtering recommendations.

## SPL

```spl
index=network sourcetype="netflow"
| lookup service_lookup dest_port OUTPUT service_name
| stats sum(bytes) as total_bytes dc(src) as unique_sources by protocol, service_name
| eval GB=round(total_bytes/1073741824,2) | sort -total_bytes
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out dc(All_Traffic.src) as unique_sources
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.transport All_Traffic.app span=1h
| eval total_bytes=bytes_in+bytes_out
| sort -total_bytes
| head 20
```

## Visualization

Pie chart (by protocol), Treemap (by service + volume), Timechart.

## Known False Positives

Traffic spikes during backup jobs, large file transfers, or video streaming events shift the protocol mix without an attack; updates to apps and NBAR signatures also change the pie chart in harmless ways.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
