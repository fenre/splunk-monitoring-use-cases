<!-- AUTO-GENERATED from UC-5.7.1.json — DO NOT EDIT -->

---
id: "5.7.1"
title: "Top Talkers Analysis"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.1 · Top Talkers Analysis

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity

*We help you see who is using the most internet so you can find congestion and plan more capacity before video calls and apps start failing.*

---

## Description

Identifies top bandwidth consumers. Essential for troubleshooting congestion and capacity planning. IPv6 flows require NetFlow v9 or IPFIX templates (or sFlow) — NetFlow v5 is IPv4-only.

## Value

Network operations and capacity planning teams identify the hosts and conversations consuming the most bandwidth, enabling targeted troubleshooting of congestion, capacity upgrades, and detection of unauthorized high-volume transfers.

## Implementation

Export NetFlow from routers/switches to a NetFlow collector that forwards to Splunk. Install NetFlow TA for field parsing.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX/sFlow data flowing into `index=netflow` via one of: (a) Splunk Add-on for NetFlow (Splunkbase 1759) receiving NetFlow v5/v9, IPFIX, or sFlow on a designated Heavy Forwarder or standalone collector; (b) Splunk Stream capturing NetFlow inline; (c) SC4SNMP with NetFlow receiver enabled. Key fields: `src` (source IP), `dest` (destination IP), `bytes` (or `bytes_in`/`bytes_out`), `packets`, `protocol`, `src_port`, `dest_port`.
- NetFlow export must be enabled on routers and switches. For Cisco IOS/IOS-XE: `ip flow-export destination <splunk_collector> 2055` on each interface or use Flexible NetFlow with a flow monitor applied globally. For Juniper: configure `forwarding-options sampling`. For Arista: `flow tracking`. Export intervals typically 60 seconds (active timeout) and 15 seconds (inactive timeout).
- Index sizing: NetFlow generates approximately 50-200 bytes per flow record. A campus with 10,000 hosts and average 50 flows/sec ≈ 4.3M records/day ≈ 0.2-0.9 GB/day. A data center with 100K flows/sec ≈ 8.6B records/day ≈ hundreds of GB/day — consider summary indexing or Splunk metrics for high-volume environments.
- CIM compliance: the Network_Traffic data model provides normalized fields (`All_Traffic.bytes_in`, `All_Traffic.bytes_out`, `All_Traffic.src`, `All_Traffic.dest`). Enable data model acceleration for `tstats`-based searches.
- Build an `asset_inventory.csv` lookup mapping IPs to hostnames, departments, and roles (server/workstation/network device) for enriching top talker results with business context.

### Step 1 — Configure data collection
Verify NetFlow data is arriving:
```spl
index=netflow earliest=-15m
| stats count by sourcetype
```
You should see `stream:netflow`, `stream:ipfix`, or your configured sourcetype. If zero events, check: (a) the collector is listening on the configured UDP port (typically 2055, 9995, or 9996), (b) firewall rules allow NetFlow traffic from exporters to the collector, (c) the exporter is actively sending flows (verify with `show ip flow export` on Cisco or equivalent).

Verify key field extraction:
```spl
index=netflow earliest=-15m
| stats count dc(src) as unique_sources dc(dest) as unique_dests sum(bytes) as total_bytes by host
```
Each `host` should correspond to a NetFlow exporter (router/switch). The `dc(src)` count gives the number of unique source IPs seen — this should be proportional to the number of hosts behind that exporter.

### Step 2 — Create the search and alert

**Primary search — Top 20 talkers by byte volume:**
```spl
index=netflow earliest=-1h
| stats sum(bytes) as total_bytes sum(packets) as total_pkts dc(dest) as unique_dests by src
| eval total_GB=round(total_bytes/1073741824, 2)
| eval avg_pkt_size=round(total_bytes/total_pkts, 0)
| lookup asset_inventory.csv ip as src OUTPUT hostname department role
| eval src_label=if(isnotnull(hostname), hostname." (".department.")", src)
| sort -total_bytes
| head 20
```

#### Understanding this SPL: We aggregate all flow records by source IP to find the heaviest bandwidth consumers. The `total_GB` conversion makes volumes immediately understandable. `dc(dest)` shows how many destinations each talker communicates with — a server talking to 1 destination at 10 GB is a backup job, while a host talking to 10,000 destinations at 10 GB is suspicious (scanning, C2). The `avg_pkt_size` differentiates traffic types: ~1400 bytes = bulk transfer, ~64 bytes = control/scan traffic. The asset lookup adds business context.

**Bidirectional top talker pairs — conversation analysis:**
```spl
index=netflow earliest=-1h
| stats sum(bytes) as total_bytes by src, dest
| eval pair=if(src < dest, src."-".dest, dest."-".src)
| stats sum(total_bytes) as conversation_bytes by pair
| eval conversation_GB=round(conversation_bytes/1073741824, 2)
| where conversation_GB > 1
| sort -conversation_bytes
| head 20
```

#### Understanding this SPL: Instead of individual talkers, this finds the heaviest conversations (IP pairs). By normalizing the pair ordering (smaller IP first), we combine both directions of the same conversation. This reveals the specific traffic flows consuming the most bandwidth — more actionable than knowing "server X is busy" without knowing who it's talking to.

**CIM-accelerated variant (recommended for large environments):**
```spl
| tstats summariesonly=true sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out from datamodel=Network_Traffic.All_Traffic by All_Traffic.src All_Traffic.dest span=1h
| eval total_bytes=bytes_in+bytes_out
| sort -total_bytes
| head 20
| eval total_GB=round(total_bytes/1073741824, 2)
```

Schedule as Alert: run hourly. Trigger when any single source exceeds 50 GB in 1 hour (adjust to your network's normal peak). Route to network operations for investigation.

### Step 3 — Validate
(a) Compare top talker byte counts to interface counters on the exporting router. The sum of all flows through an interface should approximate the SNMP ifHCInOctets/ifHCOutOctets for that interface (within NetFlow sampling ratio if sampled).
(b) Identify a known large transfer (backup job, VM migration) and verify it appears in the top talkers list.
(c) If using sampled NetFlow (common at high speeds), verify the sampling rate in the exporter configuration and apply a multiplier to the byte counts for accurate volume estimation.
(d) Validate the `asset_inventory.csv` lookup: spot-check that top talker IPs resolve to the correct hostnames and departments.

### Step 4 — Operationalize
Dashboard ("Network — Top Talkers"):
- Row 1 — Single-value tiles: "Total bandwidth (1h) in TB", "Top talker volume (1h) in GB", "Unique active hosts", "Active flow exporters".
- Row 2 — Bar chart: top 20 sources by bytes with asset labels.
- Row 3 — Table: src_label, total_GB, total_pkts, unique_dests, avg_pkt_size. Drilldown to per-destination breakdown.
- Row 4 — Top conversation pairs with volume and direction indicators.

Alerting:
- Capacity (single host > 50 GB/h or > 80% of link capacity): alert network operations for capacity review.
- Anomaly (host that was never a top talker appears in top 5): alert security for investigation — possible compromise or unauthorized use.

Runbook (owner: Network Operations):
1. **Unexpected top talker**: Check what application is generating the traffic — correlate with firewall/proxy logs by the same src IP. Common legitimate causes: backup jobs, VM live migration, database replication, Windows Update distribution.
2. **Sustained high bandwidth from a workstation**: Investigate for potential data exfiltration, unauthorized P2P, or compromised host. Check the `unique_dests` count — many destinations suggests scanning or distributed transfer.

### Step 5 — Troubleshooting

- **Byte counts seem too low compared to SNMP counters** — If the NetFlow exporter uses sampling (common at 10G/40G/100G speeds), flow records represent only 1-in-N packets. Multiply bytes by the sampling rate to get estimated actual volume. Check `show flow monitor` or `show ip flow export` for the sampling rate.

- **`src` and `dest` show exporter IPs instead of endpoint IPs** — If NetFlow is exported from a Layer 3 switch in transit, src/dest may be the switch's own interfaces. Verify that the flow record template includes the original source/destination IPs (not NAT-translated or router-interface IPs).

- **Too many flow records overwhelming Splunk** — High-volume environments (>100K flows/sec) can generate TBs of flow data. Solutions: enable sampling on the exporter, use summary indexing in Splunk, or aggregate flows at the collector before forwarding to Splunk.

- **Missing `bytes` field** — Some NetFlow v5 implementations report bytes as `in_bytes` or `dOctets`. Check `fieldsummary` and add aliases in `props.conf` if needed.

**IPv6 Coverage:** NetFlow v5 is IPv4-only — NetFlow v9 or IPFIX is required for IPv6 flows. Add `ip_version` field check. Configure IPv6 flow records on Cisco: `match ipv6 source address`, `match ipv6 destination address` in the flow record.

## SPL

```spl
index=netflow
| stats sum(bytes) as total_bytes by src, dest
| sort -total_bytes | head 20
| eval total_GB=round(total_bytes/1073741824,2)
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| eval bytes=bytes_in+bytes_out
| sort -bytes
| head 20
```

## Visualization

Table (source, dest, bytes), Sankey diagram, Bar chart.

## Known False Positives

Traffic spikes during backup jobs, large file transfers, or video streaming events can vault hosts to the top of the list with no security issue; tune with baselines and business-hour context.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
