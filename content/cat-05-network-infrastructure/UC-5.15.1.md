<!-- AUTO-GENERATED from UC-5.15.1.json — DO NOT EDIT -->

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

## Detailed Implementation

Prerequisites
• Install `Splunk_TA_infoblox` and forward `infoblox:rpz` (and optional threat-intel) into `index=dns` as you have modeled.
• Ensure response policy and logging are enabled for the view you need on the Grid, and that blocked actions produce clear `action` or `_raw` markers.
• `docs/implementation-guide.md` for receiver placement and PII on client IPs.

Step 1 — Configure data collection
Enable RPZ hit logging to syslog or file as Infoblox documents; use the add-on to parse `qname`, `src_ip`, and `policy_name`. Keep a lookup of internal scanners if you have noisy security tools.

Step 2 — Create the search and alert
```spl
index=dns sourcetype="infoblox:rpz" earliest=-24h
| where match(lower(action),"(?i)block|nxdomain|drop|rpz") OR match(_raw,"(?i)rpz")
| stats count by qname, src_ip, policy_name, host
| sort -count
| head 100
```

Understanding this SPL
We only keep events that look like a block, then rank by how often each domain and client mix appears so you can tune RPZ and spot patient-zero clients.

Step 3 — Validate
In Grid Manager, open Reporting or a member with RPZ logging and pick the same time range as your Splunk search. Confirm one blocked FQDN and client IP in both places; for spikes, line up total block volume with a threat feed or policy change window.

Step 4 — Operationalize
Put the top domains and a timechart of block rate on a security dashboard. Send spikes to the SOC channel with the policy name.

Step 5 — Troubleshooting
If counts are zero, confirm members still send to Splunk, RPZ is bound to the right views, and you are in the right index. If noise is high, filter known-good client subnets.

## SPL

```spl
index=dns sourcetype="infoblox:rpz" earliest=-24h
| where match(lower(action),"(?i)block|nxdomain|drop|rpz") OR match(_raw,"(?i)rpz")
| stats count by qname, src_ip, policy_name, host
| sort -count
| head 100
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Resolution
  where nodename=Network_Resolution.DNS
  by DNS.query DNS.src span=1h
| where count>0
| sort -count
```

## Visualization

Bar chart (top blocked domains), timechart (block rate), table (client, domain, policy name, Grid member).

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
