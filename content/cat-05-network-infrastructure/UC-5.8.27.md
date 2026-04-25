<!-- AUTO-GENERATED from UC-5.8.27.json — DO NOT EDIT -->

---
id: "5.8.27"
title: "Infoblox DNS Firewall and RPZ Threat Block Events"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.8.27 · Infoblox DNS Firewall and RPZ Threat Block Events

## Description

Infoblox Threat Protection and response policy zones block queries to known malicious or policy-violating names. Aggregating blocks by client, threat category, and domain validates policy coverage and reveals infected or compromised endpoints.

## Value

Turns DNS resolver enforcement into actionable SOC visibility without waiting for proxy or endpoint telemetry to catch the same activity.

## Implementation

Forward Infoblox DNS Firewall and Threat Protection logs to Splunk via syslog. Install `Splunk_TA_infoblox` for CIM-compatible extractions under `infoblox:threatprotect`. Enrich `src_ip` with DHCP or AD identity where available. Tune out noisy NAT gateways using internal subnet lookups.

## SPL

```spl
index=dns sourcetype="infoblox:threatprotect" earliest=-24h
| stats count by src_ip, threat_type, threat_rule, domain
| sort -count
| head 40
```

## Visualization

Table (top blocked clients), Bar chart (threat_type), Timeline (block volume).

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
