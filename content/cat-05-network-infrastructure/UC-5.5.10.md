---
id: "5.5.10"
title: "WAN Link Utilization per Transport"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.10 · WAN Link Utilization per Transport

## Description

Unbalanced link utilization wastes expensive MPLS bandwidth while underusing broadband circuits. Enables cost-effective traffic engineering.

## Value

Unbalanced link utilization wastes expensive MPLS bandwidth while underusing broadband circuits. Enables cost-effective traffic engineering.

## Implementation

Collect interface stats per WAN transport type (MPLS, Internet, LTE). Compare utilization across links. Alert on >70% sustained utilization. Use for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), SNMP.
• Ensure the following data sources are available: `sourcetype=cisco:sdwan:interface`, SNMP IF-MIB.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Collect interface stats per WAN transport type (MPLS, Internet, LTE). Compare utilization across links. Alert on >70% sustained utilization. Use for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="cisco:sdwan:interface"
| eval util_pct=round(tx_octets*8/speed*100,1)
| stats avg(util_pct) as avg_util, max(util_pct) as peak_util by system_ip, color, interface_name
| where avg_util > 70 | sort -avg_util
```

Understanding this SPL

**WAN Link Utilization per Transport** — Unbalanced link utilization wastes expensive MPLS bandwidth while underusing broadband circuits. Enables cost-effective traffic engineering.

Documented **Data sources**: `sourcetype=cisco:sdwan:interface`, SNMP IF-MIB. **App/TA** (typical add-on context): `Cisco Catalyst Add-on for Splunk` (Splunkbase 7538), SNMP. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: cisco:sdwan:interface. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="cisco:sdwan:interface". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by system_ip, color, interface_name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Filters the current rows with `where avg_util > 70` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart (utilization per transport), Stacked bar (site comparison), Table.

## SPL

```spl
index=network sourcetype="cisco:sdwan:interface"
| eval util_pct=round(tx_octets*8/speed*100,1)
| stats avg(util_pct) as avg_util, max(util_pct) as peak_util by system_ip, color, interface_name
| where avg_util > 70 | sort -avg_util
```

## Visualization

Line chart (utilization per transport), Stacked bar (site comparison), Table.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
