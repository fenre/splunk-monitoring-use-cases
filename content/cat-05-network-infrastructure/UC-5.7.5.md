<!-- AUTO-GENERATED from UC-5.7.5.json — DO NOT EDIT -->

---
id: "5.7.5"
title: "Data Exfiltration Detection"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.7.5 · Data Exfiltration Detection

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We help you catch when someone is sending a huge amount of data to an odd place, which can mean a theft attempt or a lost laptop backing up the wrong way.*

---

## Description

Unusually large outbound transfers to uncommon destinations may be data theft.

## Value

Security teams detect potential data exfiltration by monitoring outbound transfer volumes, identifying unknown external destinations, and flagging statistical anomalies in per-host outbound behavior.

## Implementation

Baseline normal outbound transfer volumes per host. Alert when transfers exceed threshold to unknown destinations. Correlate with DNS and firewall logs.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with `src`, `dest`, `bytes`, `packets`, `dest_port`, and directional information. For exfiltration detection, you need to distinguish outbound (internal-to-external) flows from inbound.
- Build a `known_destinations.csv` lookup containing approved external destinations: cloud providers (AWS, Azure, GCP IP ranges), SaaS services (O365, Salesforce, Slack), CDNs, partner networks. Include columns: `dest`, `service_name`, `category`, `approved`. This allow-list approach reduces false positives.
- Build an `internal_subnets.csv` with your organization's IP ranges to identify internal sources.
- Understand normal outbound data volumes per host class: workstations typically send 1-5 GB/day outbound, web servers send more, database servers should send almost nothing outbound to the internet. Deviations from these baselines are the core signal.
- GeoIP lookup data should be available for external IP enrichment — the Splunk GeoIP database provides country, city, latitude, longitude.

### Step 1 — Configure data collection
Verify outbound flow visibility:
```spl
index=netflow earliest=-1h
| where cidrmatch("10.0.0.0/8", src) AND NOT cidrmatch("10.0.0.0/8", dest)
| stats sum(bytes) as outbound_bytes dc(src) as internal_hosts dc(dest) as external_dests
```
This shows total outbound volume, internal sources, and external destinations. Adjust CIDR ranges to match your internal address space.

### Step 2 — Create the search and alert

**Primary search — Large outbound transfers to unknown destinations:**
```spl
index=netflow earliest=-1h
| where cidrmatch("10.0.0.0/8", src) AND NOT cidrmatch("10.0.0.0/8", dest)
| stats sum(bytes) as total_bytes dc(dest_port) as unique_ports values(dest_port) as ports by src, dest
| eval total_MB=round(total_bytes/1048576, 1)
| where total_MB > 100
| lookup known_destinations.csv dest OUTPUT service_name approved
| where isnull(approved) OR approved!="true"
| iplocation dest
| eval dest_label=if(isnotnull(service_name), service_name, dest." (".Country.")")
| lookup asset_inventory.csv ip as src OUTPUT hostname department role
| sort -total_bytes
| head 50
```

#### Understanding this SPL: Focuses on large outbound transfers (>100 MB in 1 hour) to destinations not on the approved list. The `iplocation` enrichment adds geographic context — transfers to unexpected countries raise the severity. The asset lookup identifies the internal source (is it a workstation, server, or network device?). A database server sending 500 MB to an IP in an unexpected country is high-priority.

**Statistical anomaly — per-host outbound volume deviation:**
```spl
index=netflow earliest=-7d
| where cidrmatch("10.0.0.0/8", src) AND NOT cidrmatch("10.0.0.0/8", dest)
| bin _time span=1h
| stats sum(bytes) as hourly_bytes by _time, src
| eventstats avg(hourly_bytes) as avg_bytes stdev(hourly_bytes) as std_bytes by src
| where hourly_bytes > avg_bytes + (4 * std_bytes) AND hourly_bytes > 104857600
| eval deviation=round((hourly_bytes - avg_bytes) / std_bytes, 1)
| eval spike_MB=round(hourly_bytes/1048576, 0)
| eval normal_MB=round(avg_bytes/1048576, 0)
| sort -deviation
```

#### Understanding this SPL: Per-host statistical anomaly detection. Instead of a fixed threshold (which can't distinguish a file server from a workstation), this compares each host against its own historical behavior. A workstation that normally sends 10 MB/hour suddenly sending 1 GB is flagged (100x deviation), while a CDN origin server sending 1 GB is normal.

**Slow drip exfiltration detection (daily aggregate):**
```spl
index=netflow earliest=-24h
| where cidrmatch("10.0.0.0/8", src) AND NOT cidrmatch("10.0.0.0/8", dest)
| stats sum(bytes) as total_bytes dc(dest) as unique_dests by src
| eval total_GB=round(total_bytes/1073741824, 2)
| lookup asset_inventory.csv ip as src OUTPUT hostname role
| where (role="workstation" AND total_GB > 5) OR (role="server" AND unique_dests > 100)
| sort -total_bytes
```

#### Understanding this SPL: Catches slow, sustained exfiltration that stays under hourly thresholds but accumulates. A workstation sending 5 GB outbound in 24 hours or a server communicating with 100+ external destinations are both suspicious patterns.

### Step 3 — Validate
(a) Identify a known large outbound transfer (cloud backup, software deployment) and verify it appears in results, then confirm it's in the `known_destinations.csv` approved list and would be filtered out.
(b) GeoIP accuracy: spot-check 5 external IPs in the results against MaxMind or another GeoIP service.
(c) Test: upload a 200 MB file to an external test server from a workstation and verify it triggers the alert.
(d) Validate that internal-to-internal transfers (east-west) are NOT included (false positives from misconfigured CIDR).

### Step 4 — Operationalize
Dashboard ("Security — Data Exfiltration Detection"):
- Row 1 — Single-value tiles: "Large outbound transfers (1h)", "Unknown destinations contacted", "Highest single transfer (MB)", "Anomalous hosts detected".
- Row 2 — Map visualization: destination countries with bubble size proportional to bytes transferred.
- Row 3 — Alert table: src hostname/IP, dest IP/label, country, total_MB, ports used.
- Row 4 — Per-host trending: selected host's outbound volume over 7 days with anomaly bands.

Alerting:
- Critical (> 1 GB to unknown destination from sensitive subnet, or database server to any external IP): page security SOC immediately.
- High (> 100 MB to unknown destination from workstation): alert security team for next-business-hour investigation.
- Medium (statistical anomaly > 4 sigma on any host): queue for review.

Runbook (owner: Security Operations):
1. **Large transfer to unknown destination**: GeoIP the destination. Check DNS logs for the domain. If the domain is a known cloud storage (Dropbox, Google Drive), check DLP policy. If unknown, investigate the source host for compromise.
2. **Database server outbound traffic**: Database servers should almost never communicate directly with external IPs. Investigate immediately — possible SQL injection with data exfil, or compromised application.
3. **Statistical anomaly on workstation**: Check if the user is backing up to a personal cloud service, or if the host is compromised. Correlate with endpoint logs (EDR) and proxy logs.

### Step 5 — Troubleshooting

- **Too many false positives from cloud backup services** — Add your corporate-approved cloud service IP ranges (AWS, Azure, GCP) to `known_destinations.csv`. For dynamic cloud IPs, use DNS-based filtering (correlate with DNS logs to identify the domain).

- **`iplocation` returns null for some IPs** — The GeoIP database may not cover all IP ranges (especially new allocations). Use `| where isnotnull(Country)` to filter, or add a fallback with ASN lookup for ownership information.

- **Encrypted traffic makes content analysis impossible** — NetFlow only provides metadata (IPs, ports, bytes). For content-level DLP, integrate with proxy/CASB logs. NetFlow's value is in detecting volume and pattern anomalies without needing to decrypt traffic.

- **Sampled NetFlow underestimates transfer sizes** — If your exporters use sampling (1:100, 1:1000), multiply byte counts by the sampling ratio. A 100 MB transfer at 1:1000 sampling only shows as 100 KB in flow records. Adjust thresholds accordingly.

## SPL

```spl
index=netflow direction="outbound"
| stats sum(bytes) as total_bytes by src, dest
| where total_bytes > 1073741824
| lookup known_destinations dest OUTPUT known
| where isnull(known)
| sort -total_bytes
```

## CIM SPL

```spl
| tstats `summariesonly` sum(All_Traffic.bytes_out) as total_bytes
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest span=1h
| where total_bytes > 1073741824
| sort -total_bytes
```

## Visualization

Table, Bar chart, Map (destination GeoIP).

## Known False Positives

Off-site backup, video uploads, and cloud sync can be huge and legitimate; maintain a `known_destinations` lookup and tune thresholds by site. Traffic spikes during backup jobs, large file transfers, or video streaming are common false leads.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
