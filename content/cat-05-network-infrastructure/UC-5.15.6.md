<!-- AUTO-GENERATED from UC-5.15.6.json — DO NOT EDIT -->

---
id: "5.15.6"
title: "Infoblox DNS RPZ Enforcement Blocks versus Redirects (Infoblox)"
status: "verified"
criticality: "high"
splunkPillar: "Security"
---

# UC-5.15.6 · Infoblox DNS RPZ Enforcement Blocks versus Redirects (Infoblox)

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Security &middot; **Type:** Security, Audit &middot; **Wave:** Walk &middot; **Status:** Verified

*We sort DNS policy stops into hard stops versus gentle detours so teams know whether bad websites were simply blocked or sent somewhere safer on purpose.*

---

## Description

Use case monitors Infoblox RPZ enforcement outcomes separating hard blocks from substitute redirects, preserving visibility into sinkhole or walled-garden responses used during investigations.

## Value

Investigators distinguish containment strategies—silent NXDOMAIN versus explicit redirection—and auditors receive proof that policy responses align with legal and operational guidance for customer-facing DNS tampering.

## Implementation

Keep RPZ logging enabled on all recursive members, route RPZ sourcetype distinctly, normalize actions with eval, build dashboards comparing BLOCK vs REDIRECT volumes per policy, alert on sudden REDIRECT spikes from unexpected feeds.

## Detailed Implementation

### Prerequisites
- Licensed RPZ coverage on Grid members serving recursion.
- RPZ syslog category enabled under Grid DNS Properties > Logging.
- Splunk TA parsing producing `action`, `policy_name`, `qname`, `src_ip` fields—verify with `fieldsummary`.

### Step 1 — Configure data collection
Send RPZ logs via TCP syslog to SC4S; confirm `infoblox:rpz` segregates from generic `infoblox:dns`. Capture PASSTHRU separately only if required for volume governance.

### Step 2 — Create the search and alert
Primary SPL summarizes enforcement paths. Add correlation subsearch against `infoblox:threatprotect` for matched IOC IDs when available. Alert when REDIRECT share rises above baseline fraction.

### Step 3 — Validate
Pick NIOS Reporting RPZ counters for an hour and reconcile counts by policy_name with Splunk `stats sum(count)` grouped identically.

### Step 4 — Operationalize
Heatmaps per Grid member, drilldown to VirusTotal links for top qname values, ticket automation tagging redirect-heavy zones as higher visibility changes.

### Step 5 — Troubleshooting
**Field drift:** If `action` missing, extract via `rex` on `_raw`.**Dual logging:** Ensure members behind load-balancers retain distinct `host`.**Privacy:** Mask `src_ip` for guest SSIDs before sharing dashboards externally.

## SPL

```spl
index=dns sourcetype="infoblox:rpz" earliest=-24h
| eval action_norm=lower(coalesce(action,"unknown"))
| eval rpz_outcome=case(
    match(action_norm,"passthru|pass-through"), "PASSTHRU",
    match(action_norm,"substitute|cname|redirect|policy") OR match(_raw,"(?i)substitute"), "REDIRECT",
    match(action_norm,"nxdomain|nodata|drop|block"), "BLOCK",
    1=1, "OTHER"
  )
| where rpz_outcome IN ("BLOCK","REDIRECT")
| stats count by rpz_outcome policy_name host qname src_ip
| sort - count
| head 200
```

## CIM SPL

```spl
| tstats `summariesonly` count from datamodel=Network_Resolution where nodename=Network_Resolution.DNS by DNS.query DNS.src span=1h
| where count>0
| sort -count
```

## Visualization

Stacked bar BLOCK vs REDIRECT by policy_name, timechart of redirects only, detailed table with qname/src_ip/host.

## Known False Positives

**Sinkhole testing:** Purple-team exercises spike REDIRECT counts benignly.**Mis-tuned policies:** Over-broad substitute rules mimic malware waves—review feed diffs before escalating.**Guest NAT:** Single NAT IP inflates apparent victims.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
