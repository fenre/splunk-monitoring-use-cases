<!-- AUTO-GENERATED from UC-5.6.3.json — DO NOT EDIT -->

---
id: "5.6.3"
title: "SERVFAIL Rate Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.3 · SERVFAIL Rate Monitoring

> **Criticality:** High &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Availability

*We watch servfail rate monitoring so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

SERVFAIL increases indicate upstream DNS failures, DNSSEC validation issues, or resolver problems.

## Value

DNS operations teams detect resolver failures (SERVFAIL) in real time, identify the specific domains and zones affected, and quantify client impact for rapid troubleshooting of DNS infrastructure issues.

## Implementation

Track SERVFAIL response codes. Alert on increases. Investigate which domains are failing and which resolvers are affected.

## Detailed Implementation

### Prerequisites
- DNS query logs in `index=dns` with `reply_code` field extracted. SERVFAIL (Server Failure, RCODE 2) indicates the DNS server encountered an error while processing the query. Unlike NXDOMAIN (domain doesn't exist), SERVFAIL means the server tried but failed — typically due to upstream resolver unreachable, DNSSEC validation failure, zone transfer problems, or authoritative server timeout.
- Normal SERVFAIL rate should be < 1% of total queries. Rates above 2% indicate a significant DNS infrastructure problem that impacts application availability.
- Common SERVFAIL causes: (a) upstream forwarder/recursive resolver unreachable, (b) authoritative nameserver timeout, (c) DNSSEC chain validation failure, (d) zone file corruption, (e) resource exhaustion (file descriptors, memory) on the resolver.

### Step 1 — Configure data collection
Verify SERVFAIL events:
```spl
index=dns reply_code="SERVFAIL" earliest=-1h
| stats count by host, sourcetype
```

### Step 2 — Create the search and alert

**Primary search — SERVFAIL rate by resolver:**
```spl
index=dns earliest=-15m
| stats count as total count(eval(reply_code="SERVFAIL")) as sf_count by host
| eval sf_pct=round(100*sf_count/total, 2)
| eval status=case(sf_pct > 5, "CRITICAL", sf_pct > 2, "HIGH", sf_pct > 0.5, "WARNING", 1==1, "OK")
| where sf_pct > 0.5
| sort -sf_pct
```

**SERVFAIL by domain — identify failing zones:**
```spl
index=dns reply_code="SERVFAIL" earliest=-1h
| stats count dc(src) as affected_clients by query
| sort -count
| head 20
| eval impact=case(affected_clients > 100, "WIDESPREAD", affected_clients > 10, "MODERATE", 1==1, "LOW")
```

#### Understanding this SPL: Identifying which domains are returning SERVFAIL pinpoints the root cause. If one domain/zone dominates, it's likely an authoritative server issue for that zone. If many diverse domains fail, it's a recursive resolver problem.

**SERVFAIL trending with client impact:**
```spl
index=dns earliest=-24h
| bin _time span=5m
| stats count(eval(reply_code="SERVFAIL")) as sf_count count as total dc(eval(if(reply_code="SERVFAIL", src, null()))) as affected_clients by _time, host
| eval sf_pct=round(100*sf_count/total, 2)
| where sf_count > 0
```

### Step 3 — Validate
(a) On the DNS server, check for error conditions: Infoblox NIOS dashboard for failed queries, Windows DNS Server event logs for errors, BIND `rndc status` for error counters.
(b) Test: configure a DNS forwarder to point to a non-existent upstream IP and verify SERVFAIL rate increases.
(c) For DNSSEC-related SERVFAIL: use `dig +dnssec <domain>` to verify DNSSEC chain validation.

### Step 4 — Operationalize
Dashboard ("DNS — SERVFAIL Monitoring"):
- Row 1 — Single-value tiles: "SERVFAIL rate (%)", "Affected clients", "Top failing domain", "Resolvers with issues".
- Row 2 — Timechart: SERVFAIL rate per resolver over 24h.
- Row 3 — Failing domains table: domain, count, affected_clients, impact.
- Row 4 — Client impact: top clients experiencing SERVFAIL.

Alerting:
- Critical (SERVFAIL > 5% on any resolver for 10+ minutes): DNS resolution is significantly impacted — page DNS operations.
- High (SERVFAIL > 2% sustained): alert for investigation.
- Warning (SERVFAIL > 0.5% on specific domain with > 100 affected clients): zone-specific issue.

Runbook:
1. **Widespread SERVFAIL across domains**: Check upstream forwarder connectivity. If using Infoblox, verify Grid Member can reach external recursive resolvers. If using Windows DNS, check conditional forwarders and root hints.
2. **SERVFAIL on specific domain**: Check if the authoritative nameserver for that domain is reachable (`dig @<auth_ns> <domain>`). Check DNSSEC chain if the domain is DNSSEC-signed.

### Step 5 — Troubleshooting

- **SERVFAIL from DNSSEC validation** — If your resolver validates DNSSEC and the authoritative zone has a broken DNSSEC chain (expired signatures, missing DS records), all queries for that zone return SERVFAIL. Verify: `dig +dnssec +cd <domain>` (CD flag disables validation — if it resolves with CD but fails without, it's a DNSSEC issue).

- **Intermittent SERVFAIL** — May indicate timeout issues with upstream resolvers. Check network latency to the upstream DNS servers. Increase resolver timeout if possible.

- **SERVFAIL field name mismatch** — Some sourcetypes report as `SERVFAIL`, others as `2` (numeric RCODE). Normalize: `| eval reply_code=case(reply_code=="2", "SERVFAIL", 1==1, reply_code)`.

## SPL

```spl
index=dns reply_code="SERVFAIL" OR rcode="2"
| timechart span=5m count as servfail | where servfail > 10
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

Line chart, Table (failing domains), Single value.

## Known False Positives

Legitimate NXDOMAIN or odd query bursts can come from cache flushes, new app rollouts, mis-typed domains, or chatty IoT devices; baseline your network before alerting on spikes.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
