<!-- AUTO-GENERATED from UC-5.7.10.json — DO NOT EDIT -->

---
id: "5.7.10"
title: "Long-Duration Flow Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.7.10 · Long-Duration Flow Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Anomaly, Security

*We help you see connections that stay open a very long time, which is normal for some apps but can also be a long leak of data or a backdoor to watch for.*

---

## Description

Extremely long-lived flows may indicate data exfiltration, persistent backdoors, or stuck sessions consuming resources.

## Value

Security teams identify persistent connections, detect C2 beaconing patterns, and investigate abnormally long-lived network sessions that may indicate compromise, tunneling, or application issues.

## Implementation

Analyze flow records for duration >60 minutes. Cross-reference with known long-lived services (VPN, database replication). Flag unknown long flows for investigation.

## Detailed Implementation

### Prerequisites
- NetFlow/IPFIX data in `index=netflow` with flow duration information. Flow duration can come from: (a) explicit `duration` or `flow_duration` field in the flow record, (b) calculated from `flow_start` and `flow_end` timestamps, (c) derived from NetFlow active/inactive timeouts. Standard NetFlow active timeout is 60 seconds, meaning long-lived flows are exported as multiple records every 60 seconds.
- Understanding long-duration flows: most network flows are short-lived (web requests: <10s, API calls: <5s, DNS: <1s). Flows lasting minutes to hours indicate: persistent connections (database connections, SSH sessions, VPN tunnels), file transfers, streaming, or potentially C2 (command and control) beaconing. Context determines whether a long flow is benign or malicious.
- For C2 detection: many C2 frameworks (Cobalt Strike, Metasploit, Empire) maintain persistent TCP connections that can last hours. These often have regular, periodic data patterns (beaconing).
- Build a `long_flow_exclusions.csv` for known long-lived connections: VPN concentrators, database connection pools, monitoring systems, backup agents.

### Step 1 — Configure data collection
Understand how your exporter handles long flows:
```spl
index=netflow earliest=-1h
| stats count avg(duration) as avg_duration max(duration) as max_duration perc95(duration) as p95_duration by host
```
If `duration` is null, calculate it: `| eval duration=flow_end-flow_start`. If both are null, look for `first_switched` and `last_switched` fields. Note: if max_duration equals your active timeout (e.g., 60s), the exporter is splitting long flows — you'll need to reassemble them by session.

For session reassembly of split flows:
```spl
index=netflow earliest=-4h
| stats min(_time) as first_seen max(_time) as last_seen sum(bytes) as total_bytes sum(packets) as total_pkts count as flow_records by src, dest, src_port, dest_port, protocol
| eval session_duration_min=round((last_seen - first_seen)/60, 1)
| where session_duration_min > 30
```

### Step 2 — Create the search and alert

**Primary search — Long-duration sessions (reassembled):**
```spl
index=netflow earliest=-4h
| stats min(_time) as first_seen max(_time) as last_seen sum(bytes) as total_bytes sum(packets) as total_pkts count as flow_records by src, dest, src_port, dest_port, protocol
| eval session_min=round((last_seen - first_seen)/60, 1)
| where session_min > 60
| eval total_MB=round(total_bytes/1048576, 1)
| eval bytes_per_min=round(total_bytes/(session_min*60), 0)
| lookup long_flow_exclusions.csv src dest OUTPUT known_service
| where isnull(known_service)
| lookup asset_inventory.csv ip as src OUTPUT hostname as src_host role as src_role
| eval proto_name=case(protocol==6, "TCP", protocol==17, "UDP", 1==1, "Proto-".protocol)
| sort -session_min
| head 50
```

#### Understanding this SPL: Reassembles split flow records into sessions using the 5-tuple (src, dest, ports, protocol). Sessions lasting over 60 minutes are unusual for most applications. The `bytes_per_min` calculation reveals the traffic pattern: constant low rate (beaconing/C2), constant high rate (file transfer/streaming), or bursty (interactive session). The exclusion lookup filters known long-lived services.

**C2 beaconing detection — periodic data patterns:**
```spl
index=netflow earliest=-24h
| where cidrmatch("10.0.0.0/8", src) AND NOT cidrmatch("10.0.0.0/8", dest)
| bin _time span=5m
| stats sum(bytes) as bytes sum(packets) as pkts by _time, src, dest, dest_port
| eventstats count as intervals stdev(bytes) as byte_stdev avg(bytes) as byte_avg by src, dest
| where intervals > 12 AND byte_stdev < byte_avg * 0.3
| eval consistency=round(1 - (byte_stdev/byte_avg), 2)
| stats avg(consistency) as beacon_score max(intervals) as duration_intervals dc(dest_port) as ports by src, dest
| where beacon_score > 0.7 AND duration_intervals > 24
| sort -beacon_score
```

#### Understanding this SPL: C2 beacons have a distinctive signature: regular, consistent data transfers at periodic intervals. A session with low coefficient of variation (stdev/mean < 0.3) across many intervals (12+ five-minute bins = 1+ hours) is likely beaconing. The `beacon_score` (0 to 1, higher = more periodic) ranks potential C2 connections. Human-generated traffic (browsing, email) has high variation; automated beacons are unnaturally consistent.

**Long flow analysis by category:**
```spl
index=netflow earliest=-4h
| stats min(_time) as first_seen max(_time) as last_seen sum(bytes) as total_bytes by src, dest, dest_port, protocol
| eval session_min=round((last_seen - first_seen)/60, 1)
| where session_min > 30
| eval total_MB=round(total_bytes/1048576, 1)
| eval rate_kbps=round(total_bytes*8/(session_min*60*1024), 1)
| eval category=case(dest_port==22 OR dest_port==3389, "Remote Access", dest_port==443 OR dest_port==80, "Web/API", dest_port==3306 OR dest_port==5432 OR dest_port==1433, "Database", dest_port==53, "DNS (suspicious if long)", rate_kbps < 1 AND session_min > 120, "Low-rate Persistent (C2?)", 1==1, "Other")
| stats count avg(session_min) as avg_duration max(session_min) as max_duration sum(total_MB) as total_MB by category
| sort -count
```

### Step 3 — Validate
(a) Identify a known long-lived connection (SSH session to a bastion host, VPN tunnel) and verify it appears in the results.
(b) Verify session reassembly: for a known 2-hour SSH session, check that the flow records are properly grouped (the `flow_records` count should be approximately `session_duration / active_timeout`).
(c) Test beacon detection: set up a cron job that curls an external URL every 5 minutes and verify it appears with a high beacon_score after a few hours.

### Step 4 — Operationalize
Dashboard ("Security — Long-Duration Flow Analysis"):
- Row 1 — Single-value tiles: "Active long sessions (>1h)", "Potential C2 beacons", "Longest active session (hours)", "Total long-session bandwidth (GB)".
- Row 2 — Table: long sessions with src_host, dest, session_min, total_MB, category.
- Row 3 — Beacon analysis: src, dest, beacon_score, duration, ports.
- Row 4 — Timechart: long flow category distribution over 24h.

Alerting:
- Critical (beacon_score > 0.8 to external IP from sensitive subnet): possible active C2 — alert SOC for immediate triage.
- High (long-duration DNS flow > 30 minutes): DNS should be short-lived; persistent DNS connections may indicate DNS tunneling.
- Medium (new long-duration flow to previously unseen external IP > 2 hours): alert for review.

Runbook:
1. **High beacon score**: Investigate the destination IP (GeoIP, threat intel feeds, VirusTotal). Check the source host for malware (EDR logs, AV). If confirmed C2, isolate the host immediately.
2. **Long DNS flow**: Check if it's DNS over HTTPS (DoH) or DNS tunneling. Inspect the destination — if it's a known DoH provider (Cloudflare 1.1.1.1, Google 8.8.8.8), it may be legitimate but still a policy violation.
3. **Database connection > 24 hours**: Investigate whether connection pooling is configured correctly. Stale connections waste resources and may indicate a hung application.

### Step 5 — Troubleshooting

- **Session reassembly creates too many sessions** — If source ports change mid-session (NAT or load balancer), the 5-tuple match breaks. Remove `src_port` from the stats grouping and use only `src, dest, dest_port, protocol` for a looser match.

- **All flows show 60-second duration (active timeout)** — The exporter is using the default active timeout. To see true session duration, you must reassemble flows using the session approach shown in Step 1.

- **Beacon detection false positives from monitoring systems** — NTP, SNMP polling, and heartbeat checks all produce periodic traffic. Add monitoring system IPs to `long_flow_exclusions.csv`.

- **Very high flow record counts for reassembled sessions** — A 24-hour session with 60-second active timeout produces 1,440 flow records. This is normal and should not be confused with scanning activity (which has many different destination IPs, not many records for the same 5-tuple).

## SPL

```spl
index=network sourcetype="netflow"
| eval duration_min=duration/60
| where duration_min > 60
| stats sum(bytes) as total_bytes, max(duration_min) as max_duration by src, dest, dest_port
| eval GB=round(total_bytes/1073741824,2) | sort -max_duration
| head 20
```

## CIM SPL

```spl
| tstats `summariesonly` max(All_Traffic.duration) as max_dur sum(All_Traffic.bytes_in) as bi sum(All_Traffic.bytes_out) as bo
  from datamodel=Network_Traffic.All_Traffic
  by All_Traffic.src All_Traffic.dest All_Traffic.dest_port span=1h
| eval total_bytes=bi+bo, duration_min=max_dur/60
| where duration_min > 60
| sort -max_dur
```

## Visualization

Table (source, destination, port, duration, bytes), Scatter plot (duration vs. bytes).

## Known False Positives

VPN, DB replication, and terminal sessions can run for hours. Traffic spikes during backup jobs, large file transfers, or video streaming are often long; allowlist those peers. Flow aggregation can also stretch or truncate duration depending on the exporter.

## References

- [CIM: Network_Traffic](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Traffic)
