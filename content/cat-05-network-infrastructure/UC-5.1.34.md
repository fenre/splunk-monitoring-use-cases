---
id: "5.1.34"
title: "PoE Power Budget Utilization"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.34 · PoE Power Budget Utilization

## Description

Power over Ethernet budget approaching capacity per switch.

## Value

Power over Ethernet budget approaching capacity per switch.

## Implementation

Poll POWER-ETHERNET-MIB (pethMainPsePower, pethMainPseConsumptionPower) every 300s. Alert when utilization exceeds 80%. Track per PSE unit on modular switches.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: POWER-ETHERNET-MIB (pethMainPseOperStatus, pethMainPseConsumptionPower, pethMainPsePower).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll POWER-ETHERNET-MIB (pethMainPsePower, pethMainPseConsumptionPower) every 300s. Alert when utilization exceeds 80%. Track per PSE unit on modular switches.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype=snmp:poe
| eval util_pct=round(pethMainPseConsumptionPower/pethMainPsePower*100,1)
| where pethMainPseOperStatus="on" AND util_pct > 80
| stats latest(util_pct) as poe_util, latest(pethMainPseConsumptionPower) as used_w, latest(pethMainPsePower) as total_w by host
| table host poe_util used_w total_w
```

Understanding this SPL

**PoE Power Budget Utilization** — Power over Ethernet budget approaching capacity per switch.

Documented **Data sources**: POWER-ETHERNET-MIB (pethMainPseOperStatus, pethMainPseConsumptionPower, pethMainPsePower). **App/TA** (typical add-on context): SNMP modular input, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:poe. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype=snmp:poe. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **util_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where pethMainPseOperStatus="on" AND util_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Pipeline stage (see **PoE Power Budget Utilization**): table host poe_util used_w total_w


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (utilization), Table (host, used, total), Line chart.

## SPL

```spl
index=network sourcetype=snmp:poe
| eval util_pct=round(pethMainPseConsumptionPower/pethMainPsePower*100,1)
| where pethMainPseOperStatus="on" AND util_pct > 80
| stats latest(util_pct) as poe_util, latest(pethMainPseConsumptionPower) as used_w, latest(pethMainPsePower) as total_w by host
| table host poe_util used_w total_w
```

## Visualization

Gauge (utilization), Table (host, used, total), Line chart.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
