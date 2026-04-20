---
id: "6.1.32"
title: "MDS SAN Fabric Oversubscription Ratio"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-6.1.32 · MDS SAN Fabric Oversubscription Ratio

## Description

The ratio of total edge port bandwidth to ISL bandwidth determines oversubscription. High oversubscription ratios (>7:1 for production, >20:1 for backup) increase the risk of congestion. Tracking this metric supports capacity planning and fabric expansion decisions.

## Value

The ratio of total edge port bandwidth to ISL bandwidth determines oversubscription. High oversubscription ratios (>7:1 for production, >20:1 for backup) increase the risk of congestion. Tracking this metric supports capacity planning and fabric expansion decisions.

## Implementation

Poll interface inventory via SNMP or NX-API. Classify ports by type (F-port=edge, E/TE-port=ISL). Calculate oversubscription ratio per switch. Alert when ratio exceeds policy threshold. Report quarterly for capacity planning.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP TA, scripted input (NX-API).
• Ensure the following data sources are available: SNMP IF-MIB (port speeds, port types), NX-API (`show interface brief`).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll interface inventory via SNMP or NX-API. Classify ports by type (F-port=edge, E/TE-port=ISL). Calculate oversubscription ratio per switch. Alert when ratio exceeds policy threshold. Report quarterly for capacity planning.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:if" host="mds*"
| stats sum(eval(if(port_type="F",speed,0))) as edge_bw sum(eval(if(port_type="E" OR port_type="TE",speed,0))) as isl_bw by switch
| eval oversubscription=round(edge_bw/isl_bw,1)
| where oversubscription > 7
| table switch, edge_bw, isl_bw, oversubscription
| sort -oversubscription
```

Understanding this SPL

**MDS SAN Fabric Oversubscription Ratio** — The ratio of total edge port bandwidth to ISL bandwidth determines oversubscription. High oversubscription ratios (>7:1 for production, >20:1 for backup) increase the risk of congestion. Tracking this metric supports capacity planning and fabric expansion decisions.

Documented **Data sources**: SNMP IF-MIB (port speeds, port types), NX-API (`show interface brief`). **App/TA** (typical add-on context): SNMP TA, scripted input (NX-API). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:if; **host** filter: mds*. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:if". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by switch** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **oversubscription** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where oversubscription > 7` — typically the threshold or rule expression for this monitoring goal.
• Pipeline stage (see **MDS SAN Fabric Oversubscription Ratio**): table switch, edge_bw, isl_bw, oversubscription
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (switch oversubscription), Gauge (ratio per switch), Trend chart (ratio over quarters).

## SPL

```spl
index=network sourcetype="snmp:if" host="mds*"
| stats sum(eval(if(port_type="F",speed,0))) as edge_bw sum(eval(if(port_type="E" OR port_type="TE",speed,0))) as isl_bw by switch
| eval oversubscription=round(edge_bw/isl_bw,1)
| where oversubscription > 7
| table switch, edge_bw, isl_bw, oversubscription
| sort -oversubscription
```

## Visualization

Table (switch oversubscription), Gauge (ratio per switch), Trend chart (ratio over quarters).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
