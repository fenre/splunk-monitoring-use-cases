<!-- AUTO-GENERATED from UC-5.7.4.json — DO NOT EDIT -->

---
id: "5.7.4"
title: "East-West Traffic Monitoring"
criticality: "medium"
splunkPillar: "Security"
---

# UC-5.7.4 · East-West Traffic Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Performance, Security

*We help you see traffic moving inside the company network, not just to the internet, so you can spot odd sideways movement or overloaded links between data centers and offices.*

---

## Description

Lateral traffic between internal segments reveals application dependencies and detects lateral movement.

## Value

Data center and security teams gain visibility into server-to-server (east-west) traffic patterns, enabling capacity planning for the data center fabric, microsegmentation policy validation, and detection of lateral movement post-breach.

## Implementation

Export NetFlow from internal router/switch interfaces. Analyze internal traffic patterns. Establish baseline for anomaly detection.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with `src`, `dest`, `bytes`, `packets` fields. Critical requirement: you must be able to distinguish east-west (internal-to-internal) from north-south (internal-to-external) traffic. This requires: (a) a defined list of internal subnets (RFC 1918 ranges or your organization's specific IP allocations), and (b) NetFlow exports from core/distribution switches, not just border routers (border routers only see north-south traffic).
- Build an `internal_subnets.csv` lookup containing your organization's internal IP ranges: `subnet,zone,description` (e.g., `10.10.0.0/16,datacenter-east,Production servers`, `10.20.0.0/16,datacenter-west,DR servers`). This enables zone-based analysis.
- In data center environments, east-west traffic typically constitutes 70-80% of total traffic (server-to-server communication, database queries, replication, storage traffic). Monitoring east-west traffic is critical for: (a) detecting lateral movement by attackers post-breach, (b) capacity planning for data center fabric, (c) microsegmentation policy validation.
- For VXLAN/EVPN fabrics: ensure NetFlow is exported from the VTEP (Virtual Tunnel Endpoint) so you see the inner packet headers, not just the VXLAN-encapsulated outer headers.

### Step 1 — Configure data collection
Verify that internal-to-internal flows are captured:
```spl
index=netflow earliest=-15m
| where cidrmatch("10.0.0.0/8", src) AND cidrmatch("10.0.0.0/8", dest)
| stats count sum(bytes) as total_bytes dc(src) as sources dc(dest) as destinations
```
Adjust the CIDR ranges to match your internal subnets. If the count is zero but you know internal traffic exists, your NetFlow exporters may only be on border routers. Add export to core/distribution layer switches.

### Step 2 — Create the search and alert

**Primary search — East-west traffic volume by zone pair:**
```spl
index=netflow earliest=-1h
| where cidrmatch("10.0.0.0/8", src) AND cidrmatch("10.0.0.0/8", dest)
| lookup internal_subnets.csv subnet as src OUTPUT zone as src_zone
| lookup internal_subnets.csv subnet as dest OUTPUT zone as dest_zone
| eval flow_pair=if(src_zone < dest_zone, src_zone." -> ".dest_zone, dest_zone." -> ".src_zone)
| stats sum(bytes) as total_bytes sum(packets) as total_pkts dc(src) as sources dc(dest) as dests by flow_pair
| eval total_GB=round(total_bytes/1073741824, 2)
| sort -total_bytes
```

#### Understanding this SPL: This aggregates all internal traffic by zone pair (e.g., "Production -> Database", "Web -> Application"). Normalizing the pair direction (alphabetical ordering) combines both directions of the same conversation. This reveals the heaviest inter-zone traffic paths — essential for capacity planning of inter-switch/inter-pod links and for validating microsegmentation policies.

**Lateral movement detection — new server-to-server communication:**
```spl
index=netflow earliest=-1h
| where cidrmatch("10.0.0.0/8", src) AND cidrmatch("10.0.0.0/8", dest)
| lookup asset_inventory.csv ip as src OUTPUT role as src_role hostname as src_host
| lookup asset_inventory.csv ip as dest OUTPUT role as dest_role hostname as dest_host
| where src_role="server" AND dest_role="server"
| stats sum(bytes) as bytes dc(dest_port) as ports values(dest_port) as port_list by src, src_host, dest, dest_host
| lookup known_server_flows.csv src dest OUTPUT first_seen
| where isnull(first_seen)
| eval bytes_MB=round(bytes/1048576, 1)
| where bytes_MB > 1
| sort -bytes_MB
```

#### Understanding this SPL: Identifies server-to-server flows that have never been seen before. In a well-segmented data center, servers communicate with a predictable set of peers. A new server-to-server flow can indicate: lateral movement by an attacker, a misconfigured application, or a new deployment not yet in the baseline. The `known_server_flows.csv` lookup should be populated from historical traffic.

**East-west vs. north-south ratio trending:**
```spl
index=netflow earliest=-7d
| eval direction=case(cidrmatch("10.0.0.0/8", src) AND cidrmatch("10.0.0.0/8", dest), "east-west", cidrmatch("10.0.0.0/8", src) OR cidrmatch("10.0.0.0/8", dest), "north-south", 1==1, "external")
| bin _time span=1h
| stats sum(bytes) as bytes by _time, direction
| timechart span=1h sum(bytes) by direction
```

### Step 3 — Validate
(a) Compare east-west volume to spine/leaf interface counters. The sum of east-west flows should approximate the aggregate inter-leaf traffic.
(b) Verify zone assignment: spot-check 10 source IPs to ensure `internal_subnets.csv` correctly maps them to the right zone.
(c) Test lateral movement detection: initiate a test SSH connection between two servers that don't normally communicate and verify it appears in the "new server flow" results.

### Step 4 — Operationalize
Dashboard ("Network — East-West Traffic"):
- Row 1 — Single-value tiles: "E-W volume (1h) GB", "E-W as % of total", "Unique internal conversations", "New server flows detected (1h)".
- Row 2 — Chord diagram or Sankey: inter-zone traffic flows (zone-to-zone).
- Row 3 — Table: top zone pairs by volume.
- Row 4 — New server flow alerts with src/dest hostnames and ports.

Alerting:
- Capacity (E-W ratio exceeds 85% of fabric capacity): alert for capacity review.
- Security (new server-to-server flow on management ports 22/3389/445): alert security immediately.
- Anomaly (E-W/N-S ratio shifts by > 20% in 1 hour): alert for investigation — may indicate a routing change or internal DDoS.

Runbook:
1. **New server flow on sensitive port**: Verify with the server owner whether the connection is authorized. If not, isolate the source for investigation.
2. **Sudden E-W volume increase**: Identify the zone pair responsible. Common causes: database replication failover, storage migration, VM live migration burst.

### Step 5 — Troubleshooting

- **No east-west traffic visible** — NetFlow is only exported from border routers. Deploy flow export on core/distribution/leaf switches. Alternatively, use ERSPAN to mirror east-west traffic to a Splunk Stream sensor.

- **Zone assignment lookup returns null** — The `internal_subnets.csv` uses CIDR notation but Splunk's `lookup` command doesn't do CIDR matching natively. Use `cidrmatch()` in `eval` instead, or use the `cidr()` lookup type if available in your Splunk version.

- **Traffic appears as "external" even though both IPs are internal** — Your organization uses non-RFC1918 addresses internally (e.g., carrier-grade NAT space, or public IPs used internally). Update the CIDR rules in the search to include all your internal address space.

- **VXLAN-encapsulated traffic shows wrong IPs** — If the NetFlow exporter reports the outer VXLAN header (VTEP IPs) instead of the inner packet IPs, configure the exporter to export inner flow records. On Cisco NX-OS: `feature netflow` with `match ip` (not `match tunnel`).

## SPL

```spl
index=netflow
| where cidrmatch("10.0.0.0/8",src) AND cidrmatch("10.0.0.0/8",dest)
| stats sum(bytes) as bytes, count as flows by src, dest, dest_port
| sort -bytes | head 50
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out count as flows
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval bytes=bytes_in+bytes_out
| where cidrmatch("10.0.0.0/8", All_Traffic.src) AND cidrmatch("10.0.0.0/8", All_Traffic.dest)
| sort -bytes
| head 50
```

## Visualization

Chord diagram, Table, Sankey diagram.

## Known False Positives

Backup, replication, and large VM migrations can dominate east-west without being threats; adjust the RFC1918 CIDRs to your real internal ranges. Traffic spikes during backup jobs, large file transfers, or video streaming can look like lateral bulk moves.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
