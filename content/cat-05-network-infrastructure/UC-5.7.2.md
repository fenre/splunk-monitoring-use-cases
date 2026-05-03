<!-- AUTO-GENERATED from UC-5.7.2.json — DO NOT EDIT -->

---
id: "5.7.2"
title: "Anomalous Traffic Patterns"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.2 · Anomalous Traffic Patterns

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Anomaly

*We help you notice when a computer suddenly talks to many new places or ports, which can be a break-in, a misconfiguration, or just an unusual but harmless app run.*

---

## Description

Unusual flows (new protocols, unexpected destinations) indicate compromise, misconfiguration, or shadow IT.

## Value

Network and security teams detect anomalous traffic patterns — volume spikes/drops, new external destinations, protocol shifts — that may indicate attacks, data exfiltration, or infrastructure failures.

## Implementation

Baseline normal flow patterns over 30 days. Alert on new protocol/port combinations, new external destinations, or unusual volume patterns.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with normalized fields: `src`, `dest`, `bytes`, `packets`, `protocol`, `src_port`, `dest_port`. The Splunk Add-on for NetFlow or CIM Network_Traffic data model provides field normalization.
- Baseline traffic patterns must be established before anomaly detection is meaningful. Run baseline collection for at least 7-14 days to capture weekly patterns (weekday vs. weekend, business hours vs. off-hours).
- Understand what "anomalous" means in your environment: (a) Volume anomaly — sudden increase or decrease in total bytes; (b) Pattern anomaly — new source-destination pairs not seen before; (c) Protocol anomaly — unusual protocols or ports appearing; (d) Timing anomaly — traffic patterns shifting to unexpected hours. This UC focuses on statistical volume and pattern anomalies.
- The Splunk Machine Learning Toolkit (MLTK) is recommended for advanced anomaly detection but not required — the SPL-native `eventstats` and `outlier` approaches work for most use cases.

### Step 1 — Configure data collection
Establish and store baselines:
```spl
index=netflow earliest=-7d latest=now
| bin _time span=1h
| stats sum(bytes) as hourly_bytes dc(src) as unique_sources dc(dest) as unique_dests by _time, host
| stats avg(hourly_bytes) as avg_bytes stdev(hourly_bytes) as std_bytes avg(unique_sources) as avg_sources avg(unique_dests) as avg_dests by host
```
Save this as a lookup `netflow_baselines.csv` and refresh weekly.

### Step 2 — Create the search and alert

**Primary search — Volume anomaly detection (hourly):**
```spl
index=netflow earliest=-24h
| bin _time span=1h
| stats sum(bytes) as hourly_bytes dc(src) as unique_sources dc(dest) as unique_dests dc(dest_port) as unique_ports by _time, host
| eventstats avg(hourly_bytes) as avg_bytes stdev(hourly_bytes) as std_bytes by host
| eval upper_threshold=avg_bytes + (3 * std_bytes)
| eval lower_threshold=avg_bytes - (3 * std_bytes)
| where hourly_bytes > upper_threshold OR hourly_bytes < lower_threshold
| eval anomaly_type=if(hourly_bytes > upper_threshold, "Volume Spike", "Volume Drop")
| eval deviation=round((hourly_bytes - avg_bytes) / std_bytes, 1)
| sort -abs(deviation)
```

#### Understanding this SPL: Statistical anomaly detection using 3-sigma thresholds. Volume spikes can indicate DDoS, data exfiltration, or backup jobs. Volume drops can indicate link failures, routing changes, or exporter issues. The `deviation` score shows how many standard deviations from normal — a score of 5+ is highly anomalous.

**New destination detection — first-seen external IPs:**
```spl
index=netflow earliest=-1h
| stats sum(bytes) as bytes dc(src) as internal_hosts by dest
| where NOT cidrmatch("10.0.0.0/8", dest) AND NOT cidrmatch("172.16.0.0/12", dest) AND NOT cidrmatch("192.168.0.0/16", dest)
| lookup known_destinations.csv dest OUTPUT first_seen
| where isnull(first_seen)
| eval bytes_MB=round(bytes/1048576, 1)
| where bytes_MB > 10
| sort -bytes_MB
| head 20
```

#### Understanding this SPL: Identifies external destinations that internal hosts are communicating with for the first time. New destinations with significant data volume (>10 MB in 1 hour) could indicate C2 beaconing, data exfiltration to a new drop site, or a newly compromised cloud service. The `known_destinations.csv` lookup should be populated from previous traffic history.

**Protocol distribution anomaly:**
```spl
index=netflow earliest=-24h
| bin _time span=1h
| stats sum(bytes) as bytes by _time, protocol
| eventstats sum(bytes) as total_bytes by _time
| eval pct=round(100*bytes/total_bytes, 2)
| eventstats avg(pct) as avg_pct by protocol
| where abs(pct - avg_pct) > 10
| eval shift=round(pct - avg_pct, 1)
| sort -abs(shift)
```

Schedule as Alert: volume anomaly runs hourly. New destination detection runs hourly. Trigger on volume deviation > 4 sigma or new destination with > 100 MB.

### Step 3 — Validate
(a) During a known event (backup window, patch Tuesday), verify the anomaly detection correctly identifies the volume spike and that the type is labeled correctly.
(b) Verify that the baseline is representative: compare the 7-day average to a normal week, not a holiday or maintenance week.
(c) Test the new destination detection: access a previously unvisited external IP from a test host and verify it appears in the results.

### Step 4 — Operationalize
Dashboard ("Network — Traffic Anomaly Detection"):
- Row 1 — Single-value tiles: "Anomalies detected (24h)", "Highest deviation score", "New external destinations (1h)", "Protocol shifts detected".
- Row 2 — Timechart: hourly traffic volume by exporter with anomaly threshold bands.
- Row 3 — Anomaly table: time, exporter, anomaly_type, deviation, volume.
- Row 4 — New destination table: dest IP, bytes, internal hosts communicating, GeoIP lookup.

Alerting:
- Critical (deviation > 5 sigma, sustained for 2+ hours): page network/security team — likely infrastructure event or attack.
- Warning (deviation > 3 sigma, single hour): notify for review.
- Security (new destination with > 100 MB from sensitive subnet): alert security team.

Runbook (owner: Network Operations / Security):
1. **Volume spike**: Identify the top talkers during the spike period (cross-reference with UC-5.7.1). Determine if legitimate (backup, VM migration) or suspicious (DDoS, exfiltration).
2. **Volume drop**: Check interface status on the exporter. A silent drop often means a link failure or routing change that diverted traffic.
3. **New destination with high volume**: GeoIP lookup the destination. If it's in a high-risk country, escalate to security. Correlate with DNS logs to identify the domain.

### Step 5 — Troubleshooting

- **Too many false positives** — Increase the sigma threshold from 3 to 4, or add time-of-day awareness (separate weekday/weekend baselines). Exclude known noisy hours (backup windows) from the baseline.

- **Anomalies detected but unactionable** — Enrich with context: add GeoIP, DNS reverse lookup, and asset inventory to every anomaly result. Without context, operators waste time investigating normal traffic.

- **Baseline is unstable (high standard deviation)** — Your traffic may have high natural variance. Use median/MAD (Median Absolute Deviation) instead of mean/stdev for more robust anomaly detection.

- **New destination detection returns too many results** — The `known_destinations.csv` lookup needs regular updates. Schedule a daily job to add all destinations seen in the last 24 hours to the lookup.

## SPL

```spl
index=netflow
| stats dc(dest_port) as unique_ports, dc(dest) as unique_dests by src
| where unique_ports > 100 OR unique_dests > 500
| sort -unique_ports
```

## CIM SPL

```spl
| tstats `summariesonly` dc(All_Traffic.dest_port) as unique_ports dc(All_Traffic.dest) as unique_dests
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src span=1h
| where unique_ports > 100 OR unique_dests > 500
| sort -unique_ports
```

## Visualization

Table, Scatter plot (ports vs. destinations), Timechart.

## Known False Positives

Vulnerability scans, content delivery, and legitimate many-destination services can look like reconnaissance. Traffic spikes during backup jobs, large file transfers, or video streaming also inflate diversity; baseline per role and site.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
