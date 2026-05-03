<!-- AUTO-GENERATED from UC-5.6.4.json — DO NOT EDIT -->

---
id: "5.6.4"
title: "DNS Tunneling Detection"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.6.4 · DNS Tunneling Detection

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We watch for unusual DNS patterns so we notice possible attacks, mistakes, or overloaded resolvers before people feel it as slow apps or failed lookups.*

---

## Description

DNS tunneling uses DNS queries to exfiltrate data or establish C2 channels, bypassing traditional security controls.

## Value

Security teams detect DNS tunneling used for data exfiltration and C2 communication by identifying encoded subdomain patterns, anomalous TXT/NULL query volumes, and estimating exfiltrated data volume.

## Implementation

Monitor for anomalously long DNS queries (>50 chars), high query volumes to single domains, and TXT record queries. Baseline normal DNS patterns.

## Detailed Implementation

### Prerequisites
- DNS query logs in `index=dns` with `query` (domain name) and `query_type` (TXT, NULL, CNAME, MX) fields extracted. DNS tunneling encodes data in DNS queries/responses, typically using long subdomain labels and TXT or NULL record types.
- Understanding DNS tunneling: tools like iodine, dnscat2, DNSExfiltrator, and Cobalt Strike's DNS beacon encode arbitrary data in DNS queries. The queried subdomain becomes the data channel (e.g., `aGVsbG8gd29ybGQ.tunnel.evil.com`). Detection signals: unusually long domain names, high entropy in subdomain labels, excessive TXT/NULL queries, high query rate to a single parent domain.
- Normal DNS query length: average 20-40 characters. DNS tunneling queries are typically 60-200+ characters (approaching the 253-character DNS name limit). The subdomain portion (before the registered domain) carries the encoded data.
- A `dns_tunneling_whitelist.csv` lookup should contain domains known to use long DNS names legitimately: CDN domains (e.g., akamaiedge.net), email authentication (DKIM keys in TXT records), cloud services.

### Step 1 — Configure data collection
Verify domain name and query type extraction:
```spl
index=dns earliest=-15m
| stats avg(eval(len(query))) as avg_len max(eval(len(query))) as max_len dc(query_type) as query_types by sourcetype
```
Average domain length should be 20-40 characters. If `max_len` > 100, there may be DNS tunneling or legitimate long DKIM records.

### Step 2 — Create the search and alert

**Primary search — DNS tunneling detection (multi-signal):**
```spl
index=dns earliest=-1h
| eval domain_len=len(query)
| eval subdomain=mvindex(split(query, "."), 0)
| eval sub_len=len(subdomain)
| eval has_base64=if(match(subdomain, "^[A-Za-z0-9+/=]{20,}$"), 1, 0)
| eval has_hex=if(match(subdomain, "^[0-9a-fA-F]{16,}$"), 1, 0)
| eval encoding_score=has_base64 + has_hex + if(sub_len > 40, 1, 0) + if(domain_len > 80, 1, 0)
| where encoding_score >= 2
| rex field=query "\.(?<parent_domain>[^.]+\.[^.]+)$"
| lookup dns_tunneling_whitelist.csv parent_domain OUTPUT whitelisted
| where isnull(whitelisted)
| stats count dc(query) as unique_queries dc(src) as sources avg(domain_len) as avg_len by parent_domain, src
| where unique_queries > 20 OR count > 50
| eval suspicion=case(unique_queries > 500, "CRITICAL - Active tunnel", unique_queries > 100, "HIGH - Likely tunnel", 1==1, "MEDIUM - Investigate")
| sort -unique_queries
```

#### Understanding this SPL: Multi-signal detection: (1) long subdomain labels (> 40 chars), (2) Base64-like patterns, (3) hex-encoded patterns, (4) overall long domain names. A single signal could be legitimate, but 2+ signals combined with high query volume to the same parent domain strongly indicates tunneling. The parent domain extraction identifies the tunnel endpoint.

**TXT/NULL query volume anomaly:**
```spl
index=dns earliest=-1h
| where query_type IN ("TXT", "NULL", "16", "10")
| rex field=query "\.(?<parent_domain>[^.]+\.[^.]+)$"
| stats count dc(query) as unique_queries dc(src) as sources by parent_domain, query_type
| where count > 50 OR unique_queries > 20
| sort -count
| head 20
```

#### Understanding this SPL: TXT and NULL record types are the preferred carriers for DNS tunneling because they support larger response payloads (TXT can carry ~450 bytes per response). High volumes of TXT/NULL queries to a single domain are a strong tunneling indicator.

**Data volume estimation (exfiltration rate):**
```spl
index=dns earliest=-1h
| eval subdomain=mvindex(split(query, "."), 0)
| eval sub_len=len(subdomain)
| where sub_len > 30
| rex field=query "\.(?<parent_domain>[^.]+\.[^.]+)$"
| stats count sum(sub_len) as total_encoded_chars dc(src) as sources by parent_domain
| eval estimated_bytes=round(total_encoded_chars*0.75, 0)
| eval estimated_KB=round(estimated_bytes/1024, 1)
| where estimated_KB > 10
| sort -estimated_KB
```

### Step 3 — Validate
(a) Test: set up dnscat2 or iodine in a lab and verify the detection search catches the tunnel traffic.
(b) Review false positives: DKIM TXT records for email authentication have long encoded strings. CDN domains may have long hostnames. Add legitimate long-domain services to the whitelist.
(c) Cross-reference with network flow data: DNS tunneling generates many DNS queries but little non-DNS traffic from the same host.

### Step 4 — Operationalize
Dashboard ("Security — DNS Tunneling Detection"):
- Row 1 — Single-value tiles: "Suspected tunnels", "Estimated data exfiltrated (KB)", "Affected clients", "Parent domains flagged".
- Row 2 — Tunnel suspects table: parent_domain, suspicion, unique_queries, sources, estimated_KB.
- Row 3 — TXT/NULL query analysis: top domains by TXT/NULL volume.
- Row 4 — Per-client analysis: source hosts with highest encoding scores.

Alerting:
- Critical (> 500 unique encoded queries to single parent domain in 1 hour): active DNS tunnel — alert SOC.
- High (> 100 unique encoded queries): likely tunnel — investigate within 30 minutes.
- Warning (TXT/NULL queries > 50 to unknown domain): queue for review.

Runbook:
1. **Active DNS tunnel detected**: Block the parent domain at the DNS resolver (RPZ/sinkhole) and at the firewall. Investigate the source host for malware. Check if data was exfiltrated.
2. **False positive from legitimate service**: Add the domain to `dns_tunneling_whitelist.csv` and document why.

### Step 5 — Troubleshooting

- **Too many false positives from DKIM/SPF records** — DKIM public keys in TXT records are long Base64 strings. Filter: `| where NOT match(query, "^(\w+\._domainkey|_dmarc)")` to exclude email authentication records.

- **`query_type` field not available** — Some DNS logging formats don't include the query type. For Infoblox, it's typically extracted as `qtype`. Add aliases.

- **DNS tunneling over HTTPS (DoH) not detected** — This UC detects traditional DNS tunneling over UDP/53. DNS-over-HTTPS tunneling bypasses DNS logs entirely. For DoH detection, monitor HTTPS connections to known DoH resolvers (1.1.1.1, 8.8.8.8) via network flow data.

## SPL

```spl
index=dns
| eval query_len=len(query)
| stats avg(query_len) as avg_len, count as queries, dc(query) as unique_queries by src, domain
| where avg_len > 50 OR queries > 1000
| sort -avg_len
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution.DNS
  by DNS.src DNS.query span=5m
| where count>0
| sort -count
```

## Visualization

Table (client, domain, query length, volume), Scatter plot, Bar chart.

## Known False Positives

Legitimate NXDOMAIN or odd query bursts can come from cache flushes, new app rollouts, mis-typed domains, or chatty IoT devices; baseline your network before alerting on spikes.

## References

- [CIM: Network_Resolution](https://docs.splunk.com/Documentation/CIM/latest/User/Network_Resolution)
