<!-- AUTO-GENERATED from UC-5.6.14.json — DO NOT EDIT -->

---
id: "5.6.14"
title: "DNS Resolution Performance and Failures (Meraki)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.6.14 · DNS Resolution Performance and Failures (Meraki)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

Monitors DNS query resolution times and failures to identify misconfiguration or server issues affecting user experience.

## Value

Network operations teams monitoring Meraki-managed sites detect DNS resolution failures and upstream resolver health issues per site, enabling rapid failover to backup resolvers before users experience connectivity problems.

## Implementation

Extract DNS query timing from syslog events. Set SLA thresholds (e.g., <100ms average).

## Detailed Implementation

### Prerequisites
- Cisco Meraki event logs in `index=meraki` via Splunk_TA_cisco_meraki. DNS performance events come from the Meraki MX appliance, which acts as a DNS forwarder/caching resolver for LAN clients. The MX logs DNS resolution failures, timeouts, and can export DNS query data.
- Meraki DNS events include: DNS resolution failures, upstream DNS timeout, DNS cache events. The Meraki Dashboard API also provides DNS statistics per network.
- Meraki MX DNS behavior: the MX receives DNS queries from LAN clients and forwards to configured upstream resolvers (ISP DNS, Google 8.8.8.8, Cloudflare 1.1.1.1, or custom). If the upstream resolver is unreachable or slow, all LAN clients experience DNS failures.
- Build an `upstream_resolvers.csv` lookup: `resolver_ip,resolver_name,provider` listing the upstream DNS servers configured on each MX.

### Step 1 — Configure data collection
Verify DNS-related Meraki events:
```spl
index=meraki "dns" earliest=-24h
| stats count by event_type, host
```

### Step 2 — Create the search and alert

**Primary search — DNS resolution failures by MX:**
```spl
index=meraki ("dns" AND ("fail" OR "timeout" OR "error" OR "unreachable")) earliest=-1h
| rex field=_raw "(?i)(?:server|resolver|upstream)[\s:]+(?<resolver_ip>[\d.]+)"
| stats count dc(src) as affected_clients by host, resolver_ip
| eval severity=case(count > 50, "CRITICAL", count > 10, "HIGH", 1==1, "WARNING")
| lookup upstream_resolvers.csv resolver_ip OUTPUT resolver_name provider
| eval resolver_label=if(isnotnull(resolver_name), resolver_name." (".provider.")", resolver_ip)
| sort -count
```

#### Understanding this SPL: Identifies which Meraki MX appliances are experiencing DNS resolution failures and which upstream resolver is failing. If a specific resolver fails (e.g., 8.8.8.8), it affects all MX devices using that resolver. If all resolvers fail on one MX, it's likely a local connectivity issue.

**DNS performance by site:**
```spl
index=meraki "dns" earliest=-24h
| rex field=_raw "(?i)latency[\s:=]+(?<dns_latency_ms>\d+)"
| stats avg(dns_latency_ms) as avg_latency perc95(dns_latency_ms) as p95_latency count as queries by host
| where p95_latency > 100 OR avg_latency > 50
| eval status=case(p95_latency > 500, "CRITICAL", p95_latency > 200, "HIGH", p95_latency > 100, "WARNING", 1==1, "OK")
| sort -p95_latency
```

**DNS failure trending:**
```spl
index=meraki "dns" ("fail" OR "timeout") earliest=-7d
| bin _time span=1h
| stats count as failures by _time, host
| where failures > 0
```

### Step 3 — Validate
(a) In Meraki Dashboard: Security & SD-WAN > SD-WAN > check DNS resolution health. Compare with Splunk results.
(b) From a client behind the MX: `nslookup google.com` should succeed. If it fails, the MX DNS forwarding is down.
(c) Test: temporarily configure the MX to use a non-existent upstream resolver and verify failures appear in Splunk.

### Step 4 — Operationalize
Dashboard ("Meraki — DNS Health"):
- Row 1 — Single-value tiles: "DNS failures (1h)", "Affected sites", "P95 latency (ms)", "Failing resolvers".
- Row 2 — Site DNS health table: site, avg_latency, p95_latency, failures, status.
- Row 3 — Failing resolver analysis: resolver_ip, resolver_name, failure count.
- Row 4 — DNS failure trending by site over 7 days.

Alerting:
- Critical (DNS failures > 50 at any site in 1 hour): page site operations — users cannot resolve domains.
- Warning (DNS P95 latency > 200ms): investigate upstream resolver health.

Runbook:
1. **Single upstream resolver failing**: Switch to alternative resolvers in Meraki Dashboard (Security & SD-WAN > Addressing & VLANs > DNS servers). Add redundant resolvers if only one was configured.
2. **All DNS failing at one site**: Check the MX's WAN uplink status. If the uplink is down, DNS (and everything else) fails. Check Dashboard for WAN status.

### Step 5 — Troubleshooting

- **DNS events not in Meraki logs** — Not all Meraki firmware versions log detailed DNS events. Ensure firmware is current. Alternatively, use Splunk Stream or a local DNS server for more detailed DNS analytics.

- **Cannot extract latency from Meraki events** — Meraki may not include latency in every DNS event. Use the Meraki Dashboard API's `/networks/{id}/health/dns` endpoint for latency data, or deploy external DNS monitoring (ThousandEyes).

- **Meraki Dashboard shows DNS OK but Splunk shows failures** — Time range mismatch. Ensure Splunk and Meraki Dashboard are looking at the same time window.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=security_event signature="*DNS*" resolution_time=*
| stats avg(resolution_time) as avg_dns_time, max(resolution_time) as max_dns_time, count by ap_name
| where avg_dns_time > 100
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

Gauge showing average DNS time; histogram of query times; slow query detail table.

## Known False Positives

Spikes can come from DNS cache flushes, authorized security or performance monitoring, or very talky clients; compare against change windows and known scanning tools.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
