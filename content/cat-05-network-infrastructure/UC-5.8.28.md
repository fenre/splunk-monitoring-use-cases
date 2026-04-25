<!-- AUTO-GENERATED from UC-5.8.28.json — DO NOT EDIT -->

---
id: "5.8.28"
title: "Infoblox DNS Zone Transfer (AXFR/IXFR) Attempts"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.8.28 · Infoblox DNS Zone Transfer (AXFR/IXFR) Attempts

## Description

Unauthorised zone transfers expose the entire zone contents to an attacker. Legitimate transfers should originate only from known secondary nameservers. Monitoring AXFR and IXFR queries surfaces reconnaissance and misconfiguration quickly.

## Value

Supports detection of TTPs such as DNS zone harvesting and validates that allow-listed secondaries match architectural documentation.

## Implementation

Ensure Infoblox query logging includes type AXFR/IXFR. Install the Infoblox TA and confirm field aliases for query type and client IP. Maintain a lookup of approved secondary IPs; alert on transfers from unknown sources. Review monthly with DNS operations.

## SPL

```spl
index=dns sourcetype="infoblox:dns" earliest=-7d
| eval qtype=upper(coalesce(query_type, record_type, dns_request_record_type))
| where qtype IN ("AXFR","IXFR")
| stats count by src_ip, dns_request, view, host
| sort -count
```

## Visualization

Table (client, zone, count), Map (geo for external sources).

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
