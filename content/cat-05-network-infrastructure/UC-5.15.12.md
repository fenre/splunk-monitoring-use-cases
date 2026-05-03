<!-- AUTO-GENERATED from UC-5.15.12.json — DO NOT EDIT -->

---
id: "5.15.12"
title: "Infoblox Authoritative Zone Transfer (AXFR/IXFR) Failure Monitoring (Infoblox)"
status: "verified"
criticality: "critical"
splunkPillar: "IT Operations"
---

# UC-5.15.12 · Infoblox Authoritative Zone Transfer (AXFR/IXFR) Failure Monitoring (Infoblox)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Fault &middot; **Wave:** Walk &middot; **Status:** Verified

*We watch whether copies of your official internet directory successfully sync from the master list to backup servers, because a failed copy means people sometimes get old or missing addresses.*

---

## Description

Monitoring highlights unsuccessful authoritative zone transfers or NOTIFY-driven replication errors between Grid members and downstream secondaries so stale DNS answers do not silently propagate to external resolvers.

## Value

Customer-facing authoritative DNS stays consistent across stealth secondary servers and cloud anycast edges, preventing TTL‑bounded outages when primaries update but secondaries stall due to TSIG or firewall drift.

## Implementation

Increase authoritative logging verbosity temporarily during investigations; normalize TSIG-related phrases; alert on any TRANSFER failure keywords grouped by zone_name and peer; integrate with firewall change tickets.

## Detailed Implementation

### Prerequisites
- Inventory of secondary nameservers (BIND, cloud DNS) with expected peers encoded in `infoblox_dns_secondaries.csv`.
- Understanding whether transfers traverse NAT devices rewriting source IPs.
- Coordination with PKI owners if TSIG keys rotate on calendar.

### Step 1 — Configure data collection
Enable DNS daemon categories logging zone transfers on authoritative members—not only recursion logs. Validate samples contain both success and failure lines.

### Step 2 — Create the search and alert
Primary SPL focuses on failure-bearing clauses; add success baseline search for SLA dashboards comparing success/failure ratio.

### Step 3 — Validate
Manually block TCP/53 in lab between primary and secondary to generate deterministic failure; confirm Splunk captures matching keywords within one minute.

### Step 4 — Operationalize
Per-zone health tiles, integration with ITSI KPI for external DNS availability, automated Slack ping tagging DNS on-call.

### Step 5 — Troubleshooting
**Low verbosity:** failures absent until logging raised—consult Infoblox KB for daemon categories.**Benign REFUSED:** ACL mismatches during provisioning mimic attacks—pair with change records.**Log truncation:** long TSIG errors may truncate—use TCP syslog.

## SPL

```spl
index=dns sourcetype="infoblox:dns" earliest=-24h
| search (("AXFR" OR "IXFR" OR "zone transfer" OR "transfer failed" OR "NOTIFY" OR "TSIG" OR "NOTAUTH" OR "REFUSED") AND (fail OR failed OR deny OR error OR timeout OR refused))
| rex field=_raw "(?i)(?:zone|domain)[\\s:=]+(?<zone_name>[^\\s,;]+)"
| rex field=_raw "(?i)(?:client|peer|master)[\\s:=]+(?<peer>[^\\s,;]+)"
| stats count latest(_time) as last_event values(_raw) as samples by zone_name peer host
| sort - count
| head 150
```

## CIM SPL

```spl
| tstats count where index=dns sourcetype=infoblox:dns ("AXFR" OR "IXFR") by host span=15m
```

## Visualization

Table (zone_name, peer, count, last_event), timeline of failures, side-by-side map of Grid member roles.

## Known False Positives

**Planned cutovers:** Temporary REFUSED while secondaries are rebuilt.**Pen-test probes:** External scanners trigger refused transfers—correlate with perimeter IDS.**Verbose NOTIFY chatter:** informational NOTIFY logs without failures may keyword-match until filters tightened.

## References

- [Splunk Documentation — Sourcetypes for the Splunk Add-on for Infoblox](https://docs.splunk.com/Documentation/AddOns/released/Infoblox/Sourcetypes)
- [Splunkbase — Splunk Add-on for Infoblox](https://splunkbase.splunk.com/app/2934)
- [Infoblox — DNS zone transfers overview](https://docs.infoblox.com/)
