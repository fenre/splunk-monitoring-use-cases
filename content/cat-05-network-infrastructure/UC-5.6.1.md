<!-- AUTO-GENERATED from UC-5.6.1.json — DO NOT EDIT -->

---
id: "5.6.1"
title: "DNS Query Volume Trending"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.1 · DNS Query Volume Trending

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Capacity

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

DNS query volume trending supports capacity planning and reveals traffic pattern changes.

## Value

DNS and network operations teams track query-per-second trends per resolver, detect anomalous volume spikes from DGA malware or cache flushes, and plan resolver capacity based on true peak demand.

## Implementation

Forward DNS query logs. For Windows DNS: enable analytical logging. For Infoblox: configure syslog output. Track queries per second over time.

## Detailed Implementation

### Prerequisites
- DNS query logs flowing into `index=dns` from one or more sources: Infoblox NIOS (`sourcetype=infoblox:dns` via Splunk_TA_infoblox, Splunkbase 2934), Windows DNS Server (`sourcetype=MSAD:NT6:DNS` via Splunk_TA_windows — enable DNS Analytical logging in Event Viewer > Applications and Services Logs > Microsoft > Windows > DNS-Server > Analytical), BIND/named (`sourcetype=named`), or Pi-hole syslog.
- For Infoblox: configure syslog forwarding from each Grid Member to a Splunk syslog collector or Heavy Forwarder. In NIOS Grid Manager: Grid > Grid Manager > Members > [member] > Logging > Syslog > add log destination. Set facility to local6 or similar, severity to info.
- For Windows DNS: DNS Analytical logging generates high volume (~500 bytes/query). Estimate: 10,000 queries/sec = ~430 GB/day. Plan index sizing accordingly. Enable via: `wevtutil set-log Microsoft-Windows-DNSServer/Analytical /enabled:true /rt:true /ms:1073741824`.
- CIM: the Network_Resolution data model normalizes DNS fields: `DNS.query` (domain queried), `DNS.reply_code` (NOERROR, NXDOMAIN, SERVFAIL, etc.), `DNS.src` (client IP), `DNS.dest` (resolver IP), `DNS.query_type` (A, AAAA, MX, PTR, etc.).
- Baseline: understand your normal query volume patterns — weekday vs. weekend, business hours vs. off-hours. Typical enterprise: 1K-50K queries/sec depending on size.

### Step 1 — Configure data collection
Verify DNS data is arriving:
```spl
index=dns earliest=-15m
| stats count by sourcetype, host
```
Each DNS server/resolver should appear as a `host`. If empty: check syslog forwarding (Infoblox), Windows Event Forwarding, or inputs.conf targeting DNS log files.

Verify key field extraction:
```spl
index=dns earliest=-15m
| stats count dc(query) as unique_domains dc(src) as unique_clients by sourcetype
```

### Step 2 — Create the search and alert

**Primary search — QPS trending with anomaly bands:**
```spl
index=dns (sourcetype="infoblox:dns" OR sourcetype="MSAD:NT6:DNS" OR sourcetype="named") earliest=-24h
| bin _time span=5m
| stats count as queries by _time, host
| eval qps=round(queries/300, 1)
| eventstats avg(qps) as avg_qps stdev(qps) as std_qps by host
| eval upper_band=round(avg_qps + (3 * std_qps), 1)
| eval anomaly=if(qps > upper_band, "SPIKE", "normal")
| sort -_time
```

#### Understanding this SPL: Calculates queries-per-second (QPS) per resolver in 5-minute windows. The 3-sigma upper band provides a dynamic threshold that adapts to each server's normal pattern. A QPS spike can indicate: DNS cache flush (all clients re-resolve), new application deployment, DGA malware generating random lookups, or DNS amplification attack.

**Per-resolver capacity trending (7-day growth):**
```spl
index=dns (sourcetype="infoblox:dns" OR sourcetype="MSAD:NT6:DNS") earliest=-7d
| bin _time span=1h
| stats count as hourly_queries by _time, host
| timechart span=1h max(hourly_queries) as peak_queries by host
```

**Top clients driving query volume:**
```spl
index=dns earliest=-1h
| stats count as queries dc(query) as unique_domains by src
| sort -queries
| head 20
| eval queries_per_sec=round(queries/3600, 1)
```

#### Understanding this SPL: Identifies the chattiest DNS clients. A single client generating an outsized proportion of queries could be: a misconfigured application (DNS retry storm), malware (DGA beaconing), or a legitimate high-traffic service (reverse proxy, load balancer).

### Step 3 — Validate
(a) Compare QPS with the DNS server's built-in statistics: Infoblox NIOS reporting, Windows DNS Server `dnscmd /statistics`, or BIND `rndc stats`.
(b) During a known event (DNS cache flush, application deployment), verify the QPS spike appears in the trending data.
(c) Verify per-resolver data: each DNS server should show independent volume — if one shows zero, its logs are not being forwarded.

### Step 4 — Operationalize
Dashboard ("DNS — Query Volume"):
- Row 1 — Single-value tiles: "Total QPS (all resolvers)", "Peak QPS (1h)", "Active resolvers", "QPS anomalies (24h)".
- Row 2 — Timechart: QPS per resolver over 24h with anomaly band overlay.
- Row 3 — Top clients table: src, queries, unique_domains, queries_per_sec.
- Row 4 — Week-over-week comparison: peak QPS by resolver.

Alerting:
- Critical (QPS > 3x normal sustained for 10+ minutes): possible DNS amplification or DGA outbreak — alert security and DNS operations.
- Warning (QPS > 2x normal for any single resolver): capacity concern — check resolver health.
- Capacity (7-day peak QPS > 80% of resolver rated capacity): plan infrastructure expansion.

Runbook (owner: DNS/Network Operations):
1. **QPS spike**: Identify top clients during the spike. If one client dominates, investigate that host. If many clients spike simultaneously, check for DNS cache expiry, application change, or network issue forcing re-resolution.
2. **Gradual QPS increase**: Normal growth from new users/services. Track against resolver capacity limits and plan scaling.

### Step 5 — Troubleshooting

- **Windows DNS Analytical log not generating events** — The Analytical log must be explicitly enabled and is disabled by default. Enable via PowerShell: `Set-DnsServerDiagnostics -All $true` or selectively enable query logging. After enabling, the Splunk TA needs to read from the Windows Event Log channel.

- **Infoblox query logs missing for some members** — Each Grid Member must have syslog forwarding configured individually. Check NIOS: Grid > Member > Logging. If the member sends to a VIP, ensure the VIP routes to the Splunk collector.

- **QPS calculation seems low** — If using `timechart count`, divide by the span in seconds (300 for 5-minute bins) to get true QPS. The search above handles this with `eval qps=round(queries/300, 1)`.

## SPL

```spl
index=dns sourcetype="infoblox:dns" OR sourcetype="MSAD:NT6:DNS"
| timechart span=5m count as qps
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.query DNS.reply_code span=5m
| where count>0
| sort -count
```

## Visualization

Line chart (QPS over time), Single value (current QPS), Table.

## Known False Positives

Spikes can come from DNS cache flushes, authorized security or performance monitoring, or very talky clients; compare against change windows and known scanning tools.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
