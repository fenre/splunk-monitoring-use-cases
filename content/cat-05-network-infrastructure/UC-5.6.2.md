<!-- AUTO-GENERATED from UC-5.6.2.json — DO NOT EDIT -->

---
id: "5.6.2"
title: "NXDOMAIN Spike Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.6.2 · NXDOMAIN Spike Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Anomaly

*We watch nxdomain spike detection so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

NXDOMAIN spikes indicate DGA malware (generating random domain lookups), misconfiguration, or DNS infrastructure issues.

## Value

DNS and security teams detect DGA malware activity, DNS zone misconfigurations, and abnormal NXDOMAIN rates that indicate compromised hosts or infrastructure issues.

## Implementation

Monitor DNS response codes. Baseline NXDOMAIN rates. Alert when exceeding 3 standard deviations. Investigate the querying clients and domain patterns.

## Detailed Implementation

### Prerequisites
- DNS query logs in `index=dns` with the `reply_code` field extracted. CIM field: `DNS.reply_code`. NXDOMAIN (Non-Existent Domain, RCODE 3) is returned when the queried domain does not exist.
- Normal NXDOMAIN rate is typically 5-15% of total queries (typos, stale bookmarks, cached entries for deleted records). Rates above 30% suggest a problem — either DGA (Domain Generation Algorithm) malware generating random domain lookups, or a misconfigured application.
- DGA detection: modern malware (Zeus, Conficker, CryptoLocker families) use DGA to generate thousands of pseudo-random domain names, attempting to contact C2 servers. Most generated domains return NXDOMAIN, creating a distinctive pattern: one client, thousands of unique NXDOMAIN domains.
- Splunk_TA_infoblox extracts `reply_code` for Infoblox; Windows DNS Analytical logs include the RCODE. Verify field availability before deploying.

### Step 1 — Configure data collection
Verify NXDOMAIN events exist:
```spl
index=dns reply_code="NXDOMAIN" earliest=-15m
| stats count by host, sourcetype
```
If `reply_code` is null, check field extraction in `props.conf`. For Infoblox, the field may be extracted as `rcode` or from the raw log text. Add field aliases if needed.

### Step 2 — Create the search and alert

**Primary search — NXDOMAIN rate by resolver:**
```spl
index=dns earliest=-1h
| stats count as total count(eval(reply_code="NXDOMAIN")) as nx_count by host
| eval nx_pct=round(100*nx_count/total, 1)
| eval status=case(nx_pct > 30, "CRITICAL", nx_pct > 20, "WARNING", 1==1, "OK")
| where nx_pct > 15
| sort -nx_pct
```

#### Understanding this SPL: Calculates the NXDOMAIN percentage per resolver. A resolver with 30%+ NXDOMAIN rate is either serving a network with active DGA malware or has a DNS zone issue. Per-resolver analysis is important because a zone configuration error affects only the authoritative resolver, while malware affects client-facing resolvers.

**DGA detection — per-client NXDOMAIN spike:**
```spl
index=dns reply_code="NXDOMAIN" earliest=-1h
| stats dc(query) as unique_nx_domains count as nx_queries by src
| where unique_nx_domains > 100
| eval avg_domain_len=0
| eval suspicion=case(unique_nx_domains > 1000, "HIGH - likely DGA malware", unique_nx_domains > 500, "MEDIUM - investigate", 1==1, "LOW - may be misconfigured app")
| sort -unique_nx_domains
| head 20
```

#### Understanding this SPL: A single client generating 100+ unique NXDOMAIN domains in one hour is highly suspicious. Normal users generate fewer than 10 unique NXDOMAIN lookups per hour (typos). DGA malware generates hundreds to thousands of random domain names. The `dc(query)` (distinct count of queried domains) is the key signal — high volume on the same domain is a retry, high count of unique domains is DGA.

**NXDOMAIN domain analysis — entropy scoring:**
```spl
index=dns reply_code="NXDOMAIN" earliest=-1h
| stats count by query, src
| eval domain_len=len(query)
| eval has_numbers=if(match(query, "\d{4,}"), 1, 0)
| eval consonant_heavy=if(match(query, "[^aeiou]{5,}"), 1, 0)
| eval dga_score=has_numbers + consonant_heavy + if(domain_len > 30, 1, 0)
| where dga_score >= 2
| sort -dga_score, -count
| head 50
```

#### Understanding this SPL: DGA-generated domains have distinctive characteristics: long strings, many consecutive consonants, embedded number sequences, unusual TLDs. A simple scoring system flags likely DGA domains for investigation.

### Step 3 — Validate
(a) Check NXDOMAIN rate against DNS server statistics (Infoblox reporting, Windows DNS statistics counters). The percentage should be similar.
(b) Test: query several non-existent domains (`nslookup thisdoesnotexist12345.com`) and verify they appear in the NXDOMAIN search.
(c) For DGA detection: if you have a test environment, run a DGA simulator and verify the per-client alert fires.

### Step 4 — Operationalize
Dashboard ("DNS — NXDOMAIN Analysis"):
- Row 1 — Single-value tiles: "NXDOMAIN rate (%)", "Clients with > 100 unique NX", "DGA suspects", "Total NXDOMAIN (1h)".
- Row 2 — Timechart: NXDOMAIN rate by resolver over 24h.
- Row 3 — DGA suspect table: src, unique_nx_domains, suspicion level.
- Row 4 — Top NXDOMAIN domains table: query, count, sources — for identifying common misconfigurations.

Alerting:
- Critical (any client with > 1000 unique NXDOMAIN domains in 1 hour): likely DGA malware — alert SOC immediately.
- High (resolver NXDOMAIN rate > 30% sustained for 30 minutes): investigate DNS zone issues or widespread malware.
- Warning (client with > 100 unique NXDOMAIN): investigate — may be misconfigured application or early-stage malware.

Runbook:
1. **DGA suspect client**: Isolate the host from the network. Run endpoint malware scan (EDR). Check the NXDOMAIN domain list against threat intel feeds.
2. **High NXDOMAIN rate on authoritative resolver**: Check for deleted DNS zones, expired delegations, or DNSSEC issues causing NXDOMAIN for valid domains.

### Step 5 — Troubleshooting

- **NXDOMAIN field not extracted** — Different sourcetypes use different field names. Infoblox may use `rcode`, Windows may use `DNS_RCODE` or embed it in the event data. Add field aliases in `props.conf`: `FIELDALIAS-reply = rcode AS reply_code`.

- **High NXDOMAIN rate from internal Microsoft domains** — Active Directory generates many internal DNS queries that may return NXDOMAIN (e.g., `_ldap._tcp.dc._msdcs.domain.local`). Filter these from the analysis: `| where NOT match(query, "\.local$")`.

- **DGA detection false positives from CDN pre-fetching** — Some browsers and CDNs pre-resolve domains that may not exist yet. Check the client — if it's a known proxy/CDN, exclude it.

## SPL

```spl
index=dns reply_code="NXDOMAIN" OR rcode="3"
| timechart span=5m count as nxdomain_count
| eventstats avg(nxdomain_count) as avg_nx, stdev(nxdomain_count) as std_nx
| where nxdomain_count > (avg_nx + 3*std_nx)
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

Line chart with threshold, Table (top NXDOMAIN clients), Bar chart (top queried NX domains).

## Known False Positives

Legitimate NXDOMAIN or odd query bursts can come from cache flushes, new app rollouts, mis-typed domains, or chatty IoT devices; baseline your network before alerting on spikes.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
