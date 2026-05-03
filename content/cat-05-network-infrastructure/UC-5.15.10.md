<!-- AUTO-GENERATED from UC-5.15.10.json — DO NOT EDIT -->

---
id: "5.15.10"
title: "Infoblox DNS NXDOMAIN Rate Trending for Recursive Clients (Infoblox)"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.15.10 · Infoblox DNS NXDOMAIN Rate Trending for Recursive Clients (Infoblox)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Security, Analytics &middot; **Wave:** Walk &middot; **Status:** Verified

*We track how often computers ask for names that do not exist; when that jumps for one machine it can mean malware guessing names or a broken app mis-typing addresses.*

---

## Description

Hourly aggregation compares NXDOMAIN responses to total DNS queries per internal client IP so sudden hikes—often tied to malware DGAs or misconfigured applications—stand out against historical medians.

## Value

Risk teams gain a lightweight complementary indicator to full PCAP inspection, guiding containment decisions while application owners receive evidence for fixing fat-fingered suffix searches or broken automation.

## Implementation

Normalize rcode fields via eval, exclude authoritative-only members if splits exist using `host` tags, baseline per building, alert when nx_rate exceeds adaptive percentile with minimum query floor.

## Detailed Implementation

### Prerequisites
- Recursive members identified in `infoblox_members_role.csv` lookup for filtering.
- Understanding of split-horizon DNS—internal NXDOMAIN expected for some namespaces.
- Storage sizing for query logging volumes.

### Step 1 — Configure data collection
Enable DNS query logging categories balanced with Infoblox sizing guidelines; prefer sampled logging plus RPZ feeds for layered coverage.

### Step 2 — Create the search and alert
Primary SPL measures nx_rate hourly; complement with `predict` on aggregate NXDOMAIN/min for fleet-wide malware surge alerts.

### Step 3 — Validate
Cross-check randomly sampled hour against Splunk raw events counting NXDOMAIN substrings vs TA numeric rcode.

### Step 4 — Operationalize
Heatmap of src_ip by site, integration with proxy logs for HTTP correlation when nx_rate spikes.

### Step 5 — Troubleshooting
**Missing rcode:** rely on substring match path cautiously—performance heavy.**Legitimate scanners:** exclude vulnerability scanner subnets.**Wildcard internal zones:** misconfigured search lists inflate NXDOMAIN.

## SPL

```spl
index=dns sourcetype="infoblox:dns" earliest=-7d@h latest=now
| eval rcode_norm=upper(trim(coalesce(rcode,rcode_str,"")))
| eval is_nx=if(rcode_norm="NXDOMAIN" OR match(_raw,"(?i)\\bNXDOMAIN\\b") OR rcode="3" OR rcode=3, 1, 0)
| bin _time span=1h
| stats count as queries sum(is_nx) as nx_count by _time src_ip host
| eval nx_rate=round(100*nx_count/queries,2)
| eventstats median(nx_rate) as med by src_ip
| where nx_rate >= 35 AND queries>=200
| sort - nx_rate
| head 200
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Network_Resolution where nodename=Network_Resolution.DNS by DNS.src DNS.reply_code span=1h
```

## Visualization

Timechart nx_rate for top talkers, geographic site facet, reference line at organizational threshold.

## Known False Positives

**Broken SaaS clients:** Misconfigured connectors hammer invalid hostnames.**Guest Wi‑Fi:** Captive portals generate noisy NXDOMAIN.**New AV deployments:** Large NX spikes during initial lookups sometimes normalize within days.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
