<!-- AUTO-GENERATED from UC-5.6.5.json — DO NOT EDIT -->

---
id: "5.6.5"
title: "DHCP Scope Exhaustion"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.5 · DHCP Scope Exhaustion

## Description

Empty DHCP scopes prevent new devices from getting network access.

## Value

Empty DHCP scopes prevent new devices from getting network access.

## Implementation

For Windows: forward DHCP audit logs + scripted input for scope stats. For Infoblox: use API or syslog. Alert when >90% utilized.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk_TA_windows (DHCP logs), Splunk_TA_infoblox.
• Ensure the following data sources are available: DHCP server logs, API metrics.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
For Windows: forward DHCP audit logs + scripted input for scope stats. For Infoblox: use API or syslog. Alert when >90% utilized.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=dhcp sourcetype="DhcpSrvLog" OR sourcetype="infoblox:dhcp"
| stats dc(assigned_ip) as used by scope_name, scope_range
| eval total = scope_end - scope_start
| eval used_pct=round(used/total*100,1) | where used_pct > 90
```

Understanding this SPL

**DHCP Scope Exhaustion** — Empty DHCP scopes prevent new devices from getting network access.

Documented **Data sources**: DHCP server logs, API metrics. **App/TA** (typical add-on context): Splunk_TA_windows (DHCP logs), Splunk_TA_infoblox. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: dhcp; **sourcetype**: DhcpSrvLog, infoblox:dhcp. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=dhcp, sourcetype="DhcpSrvLog". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by scope_name, scope_range** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **total** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where used_pct > 90` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
Compare lease and scope utilization in Infoblox Grid Manager, Windows Server DHCP, or your ISC/BIND tooling to the Splunk rows for the same scopes and servers.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per scope, Table, Bar chart.

## SPL

```spl
index=dhcp sourcetype="DhcpSrvLog" OR sourcetype="infoblox:dhcp"
| stats dc(assigned_ip) as used by scope_name, scope_range
| eval total = scope_end - scope_start
| eval used_pct=round(used/total*100,1) | where used_pct > 90
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Network_Sessions.DHCP
  by DHCP.mac DHCP.ip DHCP.action span=1h
| where count>0
| sort -count
```

## Visualization

Gauge per scope, Table, Bar chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
