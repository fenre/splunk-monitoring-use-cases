---
id: "5.6.16"
title: "DHCP Lease Exhaustion and Scope Utilization"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.6.16 · DHCP Lease Exhaustion and Scope Utilization

## Description

Exhausted DHCP scopes prevent new devices from joining the network. Monitoring utilization and lease count supports proactive scope expansion or cleanup.

## Value

Exhausted DHCP scopes prevent new devices from joining the network. Monitoring utilization and lease count supports proactive scope expansion or cleanup.

## Implementation

Poll DHCP server (Infoblox API, Windows WMI, or lease file) for scope size and in-use count. Ingest daily or hourly. Alert when utilization exceeds 85%. Track lease duration and stale lease cleanup.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Infoblox, Microsoft DHCP, ISC DHCP — scripted input or API.
• Ensure the following data sources are available: DHCP server logs, lease table export, SNMP (DHCP pool MIB).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll DHCP server (Infoblox API, Windows WMI, or lease file) for scope size and in-use count. Ingest daily or hourly. Alert when utilization exceeds 85%. Track lease duration and stale lease cleanup.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=dhcp_scope
| eval used_pct=round(leases_in_use/scope_size*100, 1)
| stats latest(used_pct) as pct, latest(leases_in_use) as used by scope_name, server
| where pct > 85
| table scope_name server used scope_size pct
```

Understanding this SPL

**DHCP Lease Exhaustion and Scope Utilization** — Exhausted DHCP scopes prevent new devices from joining the network. Monitoring utilization and lease count supports proactive scope expansion or cleanup.

Documented **Data sources**: DHCP server logs, lease table export, SNMP (DHCP pool MIB). **App/TA** (typical add-on context): Infoblox, Microsoft DHCP, ISC DHCP — scripted input or API. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: dhcp_scope. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=dhcp_scope. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **used_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by scope_name, server** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where pct > 85` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **DHCP Lease Exhaustion and Scope Utilization**): table scope_name server used scope_size pct


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge per scope, Table (scope, used, size, %), Line chart (utilization trend).

## SPL

```spl
index=network sourcetype=dhcp_scope
| eval used_pct=round(leases_in_use/scope_size*100, 1)
| stats latest(used_pct) as pct, latest(leases_in_use) as used by scope_name, server
| where pct > 85
| table scope_name server used scope_size pct
```

## Visualization

Gauge per scope, Table (scope, used, size, %), Line chart (utilization trend).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
