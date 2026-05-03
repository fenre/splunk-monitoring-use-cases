<!-- AUTO-GENERATED from UC-5.7.6.json — DO NOT EDIT -->

---
id: "5.7.6"
title: "Port Scan Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.6 · Port Scan Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We help you spot when one machine tries a huge list of door numbers on another, which is often someone probing the network for a way in—before they find one that works.*

---

## Description

Hosts scanning many ports on targets indicate reconnaissance, worm propagation, or vulnerability scanning.

## Value

Security operations teams detect network reconnaissance in real time by identifying horizontal sweeps, vertical port enumeration, and comprehensive scans while suppressing known legitimate scanning activity.

## Implementation

Detect hosts connecting to >50 unique ports on a single target in 5 minutes. Alert with source and target details.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with `src`, `dest`, `dest_port`, `protocol`, `bytes`, `packets`, and `tcp_flags` (if available). Port scans generate many flows with unique `dest_port` values from a single source, which is the primary detection signal.
- Understanding scan types: (a) Horizontal scan — one source targets one port across many destinations (e.g., scanning for open SSH port 22 on the entire /24 subnet); (b) Vertical scan — one source targets many ports on a single destination (enumeration of services on one host); (c) Stealth scan — slow scanning (fewer than 10 ports/min) designed to evade detection.
- TCP flag analysis (if available in flow records): SYN-only flags indicate TCP SYN scan (nmap -sS). SYN+ACK responses indicate open ports. RST responses indicate closed ports. A high ratio of RST to SYN+ACK suggests scanning. Some NetFlow implementations aggregate flags per flow, which limits this analysis.
- Build a `scan_exclusions.csv` lookup for legitimate scanning sources: vulnerability scanners (Qualys, Nessus, Rapid7), network discovery tools (Cisco DNA Center, SolarWinds), monitoring systems (Nagios, PRTG). These should not trigger alerts.

### Step 1 — Configure data collection
Verify port and destination diversity in flow data:
```spl
index=netflow earliest=-15m
| stats dc(dest_port) as unique_ports dc(dest) as unique_dests by src
| where unique_ports > 100 OR unique_dests > 50
| sort -unique_ports
| head 20
```
This quick scan shows sources with high port or destination diversity — potential scanners. If your results are empty but you know scanning occurs, check if flow records include port information.

### Step 2 — Create the search and alert

**Primary search — Horizontal scan detection (one port, many destinations):**
```spl
index=netflow earliest=-15m
| stats dc(dest) as unique_dests sum(bytes) as total_bytes sum(packets) as total_pkts by src, dest_port
| where unique_dests > 20
| eval avg_bytes_per_flow=round(total_bytes/total_pkts, 0)
| lookup scan_exclusions.csv src OUTPUT is_scanner
| where isnull(is_scanner)
| eval scan_type="Horizontal"
| eval severity=case(unique_dests > 200, "CRITICAL", unique_dests > 50, "HIGH", 1==1, "MEDIUM")
| sort -unique_dests
| head 20
```

#### Understanding this SPL: Horizontal scans (network sweeps) target a single port across many IPs. A source touching 20+ unique destinations on the same port in 15 minutes is almost certainly scanning. Legitimate services rarely contact more than a handful of peers on the same port. The `avg_bytes_per_flow` helps classify: scan probes are tiny (40-64 bytes per packet for SYN scan), while legitimate traffic has larger packets. Excluding known scanners prevents alert fatigue.

**Vertical scan detection (many ports, one destination):**
```spl
index=netflow earliest=-15m
| stats dc(dest_port) as unique_ports sum(bytes) as total_bytes sum(packets) as total_pkts by src, dest
| where unique_ports > 50
| eval avg_bytes_per_flow=round(total_bytes/total_pkts, 0)
| lookup scan_exclusions.csv src OUTPUT is_scanner
| where isnull(is_scanner)
| eval scan_type="Vertical"
| eval severity=case(unique_ports > 1000, "CRITICAL", unique_ports > 200, "HIGH", 1==1, "MEDIUM")
| sort -unique_ports
| head 20
```

#### Understanding this SPL: Vertical scans enumerate services on a single target. An attacker or pentester probing 50+ ports on one host is doing service enumeration (nmap -sV). This is often a precursor to exploitation — once they find open ports, they attack the vulnerable service.

**Combined scan dashboard search with rate analysis:**
```spl
index=netflow earliest=-1h
| stats dc(dest) as unique_dests dc(dest_port) as unique_ports sum(packets) as total_pkts by src
| where unique_dests > 20 OR unique_ports > 50
| lookup scan_exclusions.csv src OUTPUT is_scanner
| where isnull(is_scanner)
| eval scan_type=case(unique_dests > 20 AND unique_ports < 5, "Horizontal Scan", unique_ports > 50 AND unique_dests < 5, "Vertical Scan", unique_dests > 20 AND unique_ports > 50, "Comprehensive Scan", 1==1, "Suspicious")
| eval scan_rate=round(total_pkts/3600, 1)
| lookup asset_inventory.csv ip as src OUTPUT hostname department role
| eval src_label=if(isnotnull(hostname), hostname, src)
| sort -unique_dests, -unique_ports
```

### Step 3 — Validate
(a) Run a controlled nmap scan from a test machine: `nmap -sS -p 22,80,443 10.0.0.0/24`. Verify the scan source appears in horizontal scan results with ~254 unique destinations.
(b) Run a vertical scan: `nmap -sV -p 1-1000 <target>`. Verify the source appears in vertical scan results with ~1000 unique ports.
(c) Verify that scanners in `scan_exclusions.csv` do NOT appear in results.
(d) Check for false positives from legitimate services (DNS servers querying many destinations, LDAP lookups to many DCs, monitoring systems).

### Step 4 — Operationalize
Dashboard ("Security — Port Scan Detection"):
- Row 1 — Single-value tiles: "Active scans detected (1h)", "Horizontal scans", "Vertical scans", "CRITICAL severity scans".
- Row 2 — Table: src_label, scan_type, severity, unique_dests, unique_ports, scan_rate (probes/sec).
- Row 3 — Timechart: scan activity over 24h by severity.
- Row 4 — Drilldown: selected scanner's target list (destinations and ports).

Alerting:
- Critical (> 200 unique destinations in 15 min, or > 1000 ports on single host): real-time alert to SOC — active reconnaissance in progress.
- High (> 50 unique destinations or > 200 ports): alert for investigation within 30 minutes.
- Correlation: if same source is detected scanning AND later appears in firewall deny logs or IDS alerts, escalate automatically.

Runbook (owner: Security Operations):
1. **Internal host scanning**: Determine if it's an authorized security scan (check with the vulnerability management team). If not, isolate the host — it may be compromised and performing reconnaissance for lateral movement.
2. **External IP scanning internal hosts**: This should be blocked by the firewall. If flows reach internal hosts, investigate firewall rules. The scan source is likely a threat actor probing for exposed services.
3. **Slow scan detected**: Sophisticated attackers scan slowly to evade detection. Lower time window thresholds if you suspect evasion.

### Step 5 — Troubleshooting

- **Too many false positives from DNS servers** — DNS servers legitimately connect to many external IPs (upstream DNS). Exclude known DNS server IPs in the search or add them to `scan_exclusions.csv`.

- **Load balancer health checks appear as scans** — Load balancers probe multiple backend servers on specific ports (health checks). Add load balancer IPs to exclusions.

- **Cannot detect slow scans** — The 15-minute window misses scans at 1 probe/minute or slower. Create a second search with a 24-hour window and lower thresholds (e.g., > 100 unique destinations over 24 hours).

- **TCP flag information unavailable** — Not all NetFlow implementations export TCP flags. Without flags, you cannot distinguish SYN scans from full connections. Use the destination diversity (dc) approach instead, which works regardless of flag availability.

## SPL

```spl
index=netflow
| stats dc(dest_port) as unique_ports by src, dest
| where unique_ports > 50
| sort -unique_ports
```

## CIM SPL

```spl
| tstats `summariesonly` dc(All_Traffic.dest_port) as unique_ports
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| where unique_ports > 50
| sort -unique_ports
```

## Visualization

Table, Scatter plot, Timeline.

## Known False Positives

Load balancers, health checks, and some SaaS clients hit many ports on one target legitimately. Traffic spikes during backup jobs, large file transfers, or video streaming can also add port variety on noisy hosts; baseline scanners and NMS ranges.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
