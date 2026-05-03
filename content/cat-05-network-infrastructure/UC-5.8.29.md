<!-- AUTO-GENERATED from UC-5.8.29.json — DO NOT EDIT -->

---
id: "5.8.29"
title: "Infoblox DNS NXDOMAIN Flood per Client (Potential Tunneling or Malware DGA)"
status: "draft"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.8.29 · Infoblox DNS NXDOMAIN Flood per Client (Potential Tunneling or Malware DGA)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Anomaly &middot; **Status:** Draft

*We help you see when one client asks for a storm of non-existent names, which can be harmless noise or a sign of something nasty.*

---

## Description

Malware domain generation algorithms and some DNS tunneling implementations produce bursts of unique names that fail resolution. A single client generating hundreds of NXDOMAIN responses in minutes is rarely normal user behavior.

## Value

Security operations teams detect potential malware DGA activity and DNS tunneling by identifying clients generating excessive NXDOMAIN responses with domain entropy analysis, enabling rapid endpoint isolation before C2 communication succeeds.

## Implementation

Ingest full resolver query and response fields. Confirm which extracted field carries the query name and response code for your NIOS version. Baseline internal resolvers and exclude known security scanners. Pair with threat intelligence on SLD patterns for tuning.

## Detailed Implementation

### Prerequisites
- Splunk Add-on for Infoblox (Splunk_TA_infoblox, Splunkbase 2934) installed. Infoblox DNS query logs forwarded to Splunk via syslog. Data in `index=dns` with `sourcetype=infoblox:dns`. Key fields: `src_ip` (client), `query` (queried domain), `query_type`, `reply_code` (NOERROR, NXDOMAIN, SERVFAIL), `response_time`.
- This UC specifically targets excessive NXDOMAIN responses per client, which indicates: (1) malware using Domain Generation Algorithms (DGA) to find C2 servers — generates hundreds of random-looking domains, most of which don't exist, (2) DNS tunneling reconnaissance — probing for valid exfiltration subdomains, (3) misconfigured applications — software repeatedly querying non-existent internal domains.
- DGA domains typically have high entropy (random characters), unusual TLDs, and consistent length patterns. Examples: `aXk9mP2qR.com`, `bY3nL8wVe.net`, `zQ7cF1gHj.xyz`.

### Step 1 — Configure data collection
Verify NXDOMAIN events:
```spl
index=dns sourcetype="infoblox:dns" reply_code="NXDOMAIN" earliest=-1h
| stats count by src_ip
| sort -count
| head 10
```

### Step 2 — Create the search and alert

**Primary search — NXDOMAIN flood per client with DGA scoring:**
```spl
index=dns sourcetype="infoblox:dns" reply_code="NXDOMAIN" earliest=-1h
| stats count as nxdomain_count dc(query) as unique_domains values(query) as sample_domains by src_ip
| where nxdomain_count > 50
| eval domain_sample=mvindex(sample_domains, 0, 9)
| eval avg_domain_len=0
| foreach domain_sample [eval avg_domain_len=avg_domain_len + len(<<ITEM>>)]
| eval avg_domain_len=round(avg_domain_len/min(mvcount(domain_sample), 10), 1)
| eval consonant_ratio_hint=case(avg_domain_len > 20, "HIGH_ENTROPY", avg_domain_len > 12, "MODERATE", 1==1, "NORMAL")
| lookup dhcp_leases.csv ip as src_ip OUTPUT mac hostname username
| eval client_label=case(isnotnull(username), username." (".hostname.")", isnotnull(hostname), hostname, 1==1, src_ip)
| eval threat_level=case(nxdomain_count > 500 AND consonant_ratio_hint="HIGH_ENTROPY", "CRITICAL_DGA", nxdomain_count > 200, "HIGH", nxdomain_count > 100, "MEDIUM", 1==1, "LOW")
| table client_label, src_ip, nxdomain_count, unique_domains, avg_domain_len, consonant_ratio_hint, threat_level, domain_sample
| sort -nxdomain_count
```

#### Understanding this SPL: DGA malware typically generates 500-10,000 unique domain queries per hour, almost all returning NXDOMAIN. The domain length and entropy hints help distinguish DGA (long, random-looking domains) from misconfigured applications (short, structured domains like `server01.old-domain.local`). A client with 500+ NXDOMAINs and high-entropy domains is very likely compromised.

**NXDOMAIN trending per client:**
```spl
index=dns sourcetype="infoblox:dns" reply_code="NXDOMAIN" earliest=-24h
| bin _time span=1h
| stats count as nxdomains dc(query) as unique_queries by _time, src_ip
| where nxdomains > 50
| lookup dhcp_leases.csv ip as src_ip OUTPUT hostname
| eval label=coalesce(hostname, src_ip)
| timechart span=1h sum(nxdomains) by label limit=10
```

**DGA domain pattern analysis:**
```spl
index=dns sourcetype="infoblox:dns" reply_code="NXDOMAIN" earliest=-4h
| stats count by query
| where count > 1
| rex field=query "^(?P<subdomain>[^.]+)\.(?P<tld_parts>.+)$"
| eval sub_len=len(subdomain)
| eval has_numbers=if(match(subdomain, "\d"), 1, 0)
| eval has_hyphens=if(match(subdomain, "-"), 1, 0)
| where sub_len > 15 AND has_numbers=1
| sort -count
| head 50
```

### Step 3 — Validate
(a) Generate test NXDOMAIN queries: `for i in $(seq 1 100); do dig random${i}domain${RANDOM}.com @infoblox-server; done`. Verify the client appears in the alert.
(b) Compare results with known malware incidents: if a client was identified as compromised by endpoint security, verify it also appeared in the NXDOMAIN flood detection.
(c) Cross-reference with Infoblox Threat Protection blocks (UC-5.8.27): DGA domains that match RPZ feeds will appear in both this UC and the threat block UC.

### Step 4 — Operationalize
Dashboard ("DNS NXDOMAIN & DGA Detection"):
- Row 1 — Single-value tiles: "Clients with NXDOMAIN floods", "Suspected DGA activity", "Total NXDOMAIN (1h)", "Unique failed domains".
- Row 2 — Client threat table: client, NXDOMAIN count, unique domains, entropy hint, threat level, sample domains.
- Row 3 — NXDOMAIN trending per client (24h).
- Row 4 — DGA domain pattern analysis: domains with high length and numeric content.

Alerting:
- Critical (client with > 500 NXDOMAINs and HIGH_ENTROPY domains): suspected DGA — isolate endpoint and investigate.
- High (client with > 200 NXDOMAINs): investigate — malware or misconfiguration.
- Warning (client with > 50 NXDOMAINs sustained): monitor for escalation.

### Step 5 — Troubleshooting

- **High NXDOMAIN count from DNS forwarder IP** — If clients use a local DNS forwarder that then queries Infoblox, all NXDOMAINs appear from the forwarder IP. Enable EDNS Client Subnet or log at the local forwarder level to identify the actual client.

- **NXDOMAIN spikes from legitimate applications** — Some applications (service discovery, mDNS proxying, Active Directory site detection) generate legitimate NXDOMAINs. Add known application patterns to a suppression lookup.

- **DGA scoring false positives for CDN domains** — CDN domains (e.g., `a1b2c3.cloudfront.net`) can look like DGA. Maintain a whitelist of known CDN and cloud service domain patterns.

## SPL

```spl
index=dns sourcetype="infoblox:dns" earliest=-24h
| eval rcode=upper(coalesce(response_code, dns_response, "NOERROR"))
| eval qname=coalesce(dns_request, dns_query, query, dns_qname)
| where rcode="NXDOMAIN" OR match(_raw,"(?i)NXDOMAIN")
| bin _time span=10m
| stats dc(qname) as unique_qnames, count as nx_total by _time, src_ip
| where unique_qnames > 200 AND nx_total > 500
| sort -nx_total
```

## Visualization

Scatter (unique QNAMEs vs total NXDOMAIN), Table (top offending src_ip), Line chart (baseline vs spike).

## Known False Positives

Caching resolvers, captive portals, and fat-finger searches create NXDOMAINs; focus on new internal names and sustained floods per client.

## References

- [Splunk Documentation — Configure inputs for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Configureinputs)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
