<!-- AUTO-GENERATED from UC-5.7.8.json — DO NOT EDIT -->

---
id: "5.7.8"
title: "Multicast Traffic Monitoring"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.7.8 · Multicast Traffic Monitoring

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you see when one-to-many network traffic (like video or some apps) is flooding links so you can fix it before normal calls and web traffic slow down.*

---

## Description

Uncontrolled multicast traffic floods switches and consumes bandwidth. Monitoring ensures multicast storms are detected before impacting unicast traffic.

## Value

Network operations teams monitor multicast group activity, detect multicast storms before they cause outages, identify unauthorized sources, and validate that multicast services stay within expected bandwidth budgets.

## Implementation

Enable NetFlow on core/distribution switches. Filter for multicast destination range (224.0.0.0/4). Baseline expected multicast groups. Alert on new or high-volume groups.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with `dest` IP and protocol fields. Multicast traffic uses destination IPs in the 224.0.0.0/4 range (224.0.0.0 – 239.255.255.255). For IGMP (Internet Group Management Protocol) visibility, protocol number 2 must be included in flow exports.
- Understand multicast IP ranges: 224.0.0.0/24 is link-local (OSPF 224.0.0.5/6, VRRP 224.0.0.18, EIGRP 224.0.0.10); 224.0.1.0/24 is internetwork control; 232.0.0.0/8 is SSM (Source-Specific Multicast); 239.0.0.0/8 is administratively scoped (organization-local). Most enterprise multicast is in the 239.x.x.x range.
- Build a `multicast_groups.csv` lookup mapping group addresses to services: `group_ip,service_name,owner,expected_sources,expected_bandwidth` (e.g., `239.1.1.1,Video Conferencing,IT,5,500 Mbps`, `224.0.0.5,OSPF Hello,Network,all_routers,low`).
- Multicast monitoring matters because: (a) a single misconfigured multicast source can flood an entire VLAN; (b) PIM/IGMP issues can cause multicast black holes; (c) multicast storms are a leading cause of network outages in campus networks.

### Step 1 — Configure data collection
Verify multicast flow visibility:
```spl
index=netflow earliest=-1h
| where cidrmatch("224.0.0.0/4", dest)
| stats count sum(bytes) as total_bytes dc(dest) as unique_groups dc(src) as unique_sources by host
```
Each exporter (`host`) should show multicast flow records. If zero, the exporter may be filtering multicast flows — enable multicast flow export (on Cisco: ensure `ip flow ingress` is on multicast-enabled interfaces, and the flow monitor includes multicast traffic).

### Step 2 — Create the search and alert

**Primary search — Multicast group activity overview:**
```spl
index=netflow earliest=-1h
| where cidrmatch("224.0.0.0/4", dest)
| lookup multicast_groups.csv group_ip as dest OUTPUT service_name owner expected_bandwidth
| eval group_label=if(isnotnull(service_name), service_name." (".dest.")", dest)
| stats sum(bytes) as total_bytes sum(packets) as total_pkts dc(src) as active_sources first(owner) as owner by dest, group_label
| eval total_MB=round(total_bytes/1048576, 1)
| eval rate_Mbps=round(total_bytes*8/3600/1048576, 1)
| sort -total_bytes
```

#### Understanding this SPL: Provides a real-time view of all active multicast groups, their bandwidth consumption, and source count. The `rate_Mbps` calculation converts hourly bytes to average Mbps, which can be compared against the expected bandwidth in the lookup. A group consuming 10x its expected bandwidth likely has a looping or misconfigured source.

**Multicast storm detection — sudden volume spike:**
```spl
index=netflow earliest=-24h
| where cidrmatch("224.0.0.0/4", dest)
| bin _time span=5m
| stats sum(bytes) as bytes by _time, dest
| eventstats avg(bytes) as avg_bytes stdev(bytes) as std_bytes by dest
| eval threshold=avg_bytes + (4 * std_bytes)
| where bytes > threshold AND bytes > 10485760
| eval spike_factor=round(bytes/avg_bytes, 1)
| lookup multicast_groups.csv group_ip as dest OUTPUT service_name
| sort -spike_factor
```

#### Understanding this SPL: Detects multicast storms — situations where a multicast group suddenly receives far more traffic than normal. Multicast storms can be caused by: routing loops in the PIM topology, a single source sending at an excessive rate, IGMP snooping failures that flood multicast to all ports, or duplicate source streams. A 4-sigma spike with an absolute minimum of 10 MB in 5 minutes triggers the alert.

**Unauthorized or unexpected multicast sources:**
```spl
index=netflow earliest=-1h
| where cidrmatch("224.0.0.0/4", dest) AND NOT cidrmatch("224.0.0.0/24", dest)
| lookup multicast_groups.csv group_ip as dest OUTPUT expected_sources
| stats sum(bytes) as bytes dc(dest) as groups values(dest) as group_list by src
| lookup asset_inventory.csv ip as src OUTPUT hostname role
| eval src_label=if(isnotnull(hostname), hostname, src)
| where role!="network_device" AND role!="multicast_server"
| eval bytes_MB=round(bytes/1048576, 1)
| sort -bytes
```

#### Understanding this SPL: Identifies non-authorized multicast sources. In a controlled environment, only designated servers and network devices should be multicast sources. A workstation sending multicast traffic could indicate a misconfigured application, an unauthorized streaming tool, or a network attack.

### Step 3 — Validate
(a) Compare the active multicast groups to PIM routing table on the RP (Rendezvous Point): `show ip mroute` should list the same groups and sources.
(b) Verify bandwidth estimates: compare the `rate_Mbps` for a known video stream against the encoder's configured bitrate.
(c) Test storm detection: if you have a test environment, start a high-bitrate multicast stream and verify it triggers the spike alert.

### Step 4 — Operationalize
Dashboard ("Network — Multicast Monitoring"):
- Row 1 — Single-value tiles: "Active multicast groups", "Total multicast bandwidth (Mbps)", "Active sources", "Storm alerts (24h)".
- Row 2 — Table: group_label, owner, rate_Mbps, expected_bandwidth, active_sources (color-coded by over/under expected).
- Row 3 — Timechart: multicast bandwidth over 24h by group (top 10 groups).
- Row 4 — Storm alerts and unauthorized source alerts.

Alerting:
- Critical (multicast volume spike > 4 sigma + any group > 1 Gbps): potential storm — alert network operations for immediate investigation.
- High (unauthorized multicast source detected): alert security.
- Warning (group exceeds expected bandwidth by > 2x): alert multicast service owner.

Runbook:
1. **Multicast storm**: Check the RP for the affected group (`show ip mroute <group>`). Identify all sources (S,G entries). If multiple sources exist unexpectedly, prune the unauthorized source. Check IGMP snooping status on access switches.
2. **Unknown multicast group**: If the group is in the 239.x.x.x range, it's organization-local — identify the application. If in 224.0.0.x, it's a routing protocol — verify configuration.

### Step 5 — Troubleshooting

- **No multicast flows visible** — NetFlow on many routers does not export multicast flows by default. On Cisco, ensure the flow monitor is applied to interfaces where multicast traffic flows, and that the flow record template includes multicast.

- **IGMP traffic not visible** — IGMP (protocol 2) may not be included in standard NetFlow flow records. For IGMP visibility, consider enabling IGMP snooping logging on switches, or use Splunk Stream with protocol decode.

- **Link-local multicast (224.0.0.x) overwhelming the results** — OSPF hellos, VRRP/HSRP heartbeats, and EIGRP hellos generate constant low-volume multicast. Exclude the 224.0.0.0/24 range from volume-based analysis (as done in the unauthorized source search above) to focus on application multicast.

## SPL

```spl
index=network sourcetype="netflow"
| where cidrmatch("224.0.0.0/4", dest)
| stats sum(bytes) as total_bytes, dc(src) as sources by dest
| eval MB=round(total_bytes/1048576,1) | sort -total_bytes
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_in) as bytes_in sum(All_Traffic.bytes_out) as bytes_out dc(All_Traffic.src) as sources
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.dest span=1h
| eval total_bytes=bytes_in+bytes_out
| where cidrmatch("224.0.0.0/4", All_Traffic.dest)
| sort -total_bytes
| head 20
```

## Visualization

Table (multicast group, volume, sources), Timechart (multicast volume), Bar chart.

## Known False Positives

IPTV, trading floors, and imaging can legitimately use heavy multicast. Traffic spikes during backup jobs, large file transfers, or video streaming (including multicast video) are often normal; baseline known groups and PIM changes.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
