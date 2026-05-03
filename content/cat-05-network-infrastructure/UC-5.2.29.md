<!-- AUTO-GENERATED from UC-5.2.29.json — DO NOT EDIT -->

---
id: "5.2.29"
title: "Threat Intelligence Correlation and IoC Matching (Meraki MX)"
criticality: "critical"
splunkPillar: "Security"
---

# UC-5.2.29 · Threat Intelligence Correlation and IoC Matching (Meraki MX)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security

*We line up your threat indicators with what the small office already saw so you can see known bad addresses without waiting on a manual list.*

---

## Description

Correlates network traffic with threat intelligence databases to detect known malicious IPs and domains.

## Value

Security teams correlate Meraki MX firewall traffic against threat intelligence IoC feeds, prioritizing unblocked connections to high-confidence indicators of compromise.

## Implementation

Create threat intelligence lookup table. Correlate with network events.

## Detailed Implementation

### Prerequisites
* Meraki MX threat/IDS events enriched with threat intelligence. Data in `index=meraki` with `sourcetype=meraki:events`. Additional enrichment: threat intelligence lookups (`threat_intel_ioc.csv`), TAXII/STIX feeds, or Splunk Enterprise Security threat intelligence framework.
* IoC matching: correlate firewall observed IPs/domains against known Indicators of Compromise from threat feeds (OSINT, commercial, ISAC).

### Step 1 — - Configure data collection
Create or obtain threat intelligence lookup:
```
# threat_intel_ioc.csv columns:
# ioc_value, ioc_type (ip/domain/url/hash), threat_name, confidence, source, last_updated
```
Verify:
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| eval dst=coalesce(dest, dest_ip, dst)
| lookup threat_intel_ioc.csv ioc_value AS dst OUTPUT threat_name, confidence
| where isnotnull(threat_name)
| stats count by threat_name
```

### Step 2 — - Create the search and alert

**Primary search -- Threat intelligence IoC correlation:**
```spl
index=meraki sourcetype="meraki:events" earliest=-4h
| eval src=coalesce(src, src_ip)
| eval dst=coalesce(dest, dest_ip, dst)
| eval domain=coalesce(dest_hostname, dest_domain, dns_query)
| lookup threat_intel_ioc.csv ioc_value AS dst OUTPUT threat_name AS dst_threat, confidence AS dst_confidence, source AS intel_source
| lookup threat_intel_ioc.csv ioc_value AS domain OUTPUT threat_name AS domain_threat, confidence AS domain_confidence
| eval threat=coalesce(dst_threat, domain_threat)
| eval conf=coalesce(dst_confidence, domain_confidence)
| where isnotnull(threat)
| eval act=lower(coalesce(action, pattern))
| eval blocked=if(match(act, "(?i)deny|block|drop"), "YES", "NO")
| stats count as hits dc(src) as affected_hosts values(src) as internal_hosts by threat, conf, blocked, intel_source
| eval severity=case(blocked="NO" AND conf="high", "CRITICAL -- high-confidence IoC NOT blocked", blocked="NO", "HIGH -- IoC match, traffic not blocked", blocked="YES" AND conf="high", "WARNING -- high-confidence IoC blocked", 1==1, "INFO")
| where severity != "INFO"
| sort severity, -hits
```

### Step 3 — - Validate
(a) Add a known test IoC to the lookup and verify it matches traffic.
(b) Cross-reference matches with external threat intelligence platforms.
(c) Verify lookup freshness: `| inputlookup threat_intel_ioc.csv | stats max(last_updated) as freshness`.

### Step 4 — - Operationalize
Dashboard ("Meraki MX -- Threat Intel Correlation"):
* Row 1 -- Single-value: "IoC matches", "Unblocked IoC matches", "Affected hosts".
* Row 2 -- IoC match table with blocking status.

Alerting:
* Critical (high-confidence IoC not blocked): immediate investigation.
* Warning (IoC match blocked): confirmed threat successfully blocked.

### Step 5 — - Troubleshooting

* **False positive IoC match** -- Validate with multiple threat intelligence sources. Remove from lookup if false positive confirmed. Document the exclusion.

* **Stale threat intelligence** -- Update feeds regularly (daily minimum). Remove IoCs older than 90 days unless confirmed active. Check `last_updated` field.

* **IoC matched but traffic is legitimate** -- CDN/shared hosting IPs may appear in threat feeds. Check: ASN, reverse DNS, and threat context before blocking.

## SPL

```spl
index=cisco_network sourcetype="meraki" (type=security_event OR type=urls OR type=flow)
| lookup threat_intelligence_list src as src OUTPUTNEW threat_name, threat_severity
| where threat_severity="high" OR threat_severity="critical"
| stats count as hit_count by src, dest, threat_name
| sort - hit_count
```

## Visualization

IoC match timeline; threat severity breakdown; affected hosts table.

## Known False Positives

New cloud ranges, fast-flux, and short-lived goodware can overlap threat feeds; tune age and scope of feeds you trust.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
