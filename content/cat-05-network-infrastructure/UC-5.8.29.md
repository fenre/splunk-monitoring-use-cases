<!-- AUTO-GENERATED from UC-5.8.29.json — DO NOT EDIT -->

---
id: "5.8.29"
title: "Infoblox DNS NXDOMAIN Flood per Client (Potential Tunneling or Malware DGA)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.8.29 · Infoblox DNS NXDOMAIN Flood per Client (Potential Tunneling or Malware DGA)

## Description

Malware domain generation algorithms and some DNS tunneling implementations produce bursts of unique names that fail resolution. A single client generating hundreds of NXDOMAIN responses in minutes is rarely normal user behavior.

## Value

Provides an early DNS-layer signal for bot infections and tunneling without requiring full payload decryption.

## Implementation

Ingest full resolver query and response fields. Confirm which extracted field carries the query name and response code for your NIOS version. Baseline internal resolvers and exclude known security scanners. Pair with threat intelligence on SLD patterns for tuning.

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

## References

- [Splunk Documentation — Configure inputs for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Configureinputs)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
