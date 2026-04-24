---
id: "5.15.1"
title: "Infoblox DNS RPZ Block Audit and Top Blocked Domains (Infoblox)"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.15.1 · Infoblox DNS RPZ Block Audit and Top Blocked Domains (Infoblox)

## Description

RPZ enforcement turns DNS into a first-line control for malware, phishing, and data-exfiltration domains. Splunking RPZ block events gives you an auditable trail of what was stopped and which clients queried malicious names.

## Value

Security teams prove RPZ effectiveness to auditors, tune false positives faster, and spot patient-zero clients that repeatedly hit blocked indicators.

## Implementation

Enable RPZ logging on Grid members and forward syslog to Splunk with TA field extractions. Normalize blocked FQDN and client IP. Schedule a daily top-blocked report and an alert on sudden spikes versus a 14-day baseline.

## SPL

```spl
index=dns sourcetype="infoblox:rpz" earliest=-24h
| where match(lower(action),"(?i)block|nxdomain|drop|rpz") OR match(_raw,"(?i)rpz")
| stats count by qname, src_ip, policy_name, host
| sort -count
| head 100
```

## Visualization

Bar chart (top blocked domains), timechart (block rate), table (client, domain, policy name, Grid member).

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)

