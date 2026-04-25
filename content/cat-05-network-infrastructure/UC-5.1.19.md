<!-- AUTO-GENERATED from UC-5.1.19.json — DO NOT EDIT -->

---
id: "5.1.19"
title: "PoE Power Budget Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.1.19 · PoE Power Budget Monitoring

## Description

PoE budget exhaustion causes powered devices (IP phones, APs, cameras) to lose power. Proactive monitoring prevents unplanned device outages.

## Value

PoE budget exhaustion causes powered devices (IP phones, APs, cameras) to lose power. Proactive monitoring prevents unplanned device outages.

## Implementation

Poll POWER-ETHERNET-MIB every 300s. Track per-switch PoE budget utilization. Alert at 80% utilization. Trend over time to plan for additional PoE capacity.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: SNMP Modular Input, POWER-ETHERNET-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog.
• Ensure the following data sources are available: `sourcetype=snmp:poe`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Poll POWER-ETHERNET-MIB every 300s. Track per-switch PoE budget utilization. Alert at 80% utilization. Trend over time to plan for additional PoE capacity.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="snmp:poe"
| stats latest(pethMainPseOperStatus) as status, latest(pethMainPsePower) as total_watts, latest(pethMainPseConsumptionPower) as used_watts by host
| eval utilization_pct=round(used_watts/total_watts*100,1)
| where utilization_pct > 80 | sort -utilization_pct
```

Understanding this SPL

**PoE Power Budget Monitoring** — PoE budget exhaustion causes powered devices (IP phones, APs, cameras) to lose power. Proactive monitoring prevents unplanned device outages.

Documented **Data sources**: `sourcetype=snmp:poe`. **App/TA** (typical add-on context): SNMP Modular Input, POWER-ETHERNET-MIB, `TA-cisco_ios`, `Splunk_TA_juniper`, `arista:eos` via SC4S, HPE Aruba CX syslog. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: snmp:poe. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="snmp:poe". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **utilization_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where utilization_pct > 80` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
SSH to a sample device that appears in the result and run the `show` command that matches the signal in this use case. Confirm the timestamp, interface, or user string matches a row in Splunk, and that your index and sourcetype are the ones the team expects after the last change window.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge (per switch), Line chart (utilization trending), Table (switch, budget, used, remaining).

## SPL

```spl
index=network sourcetype="snmp:poe"
| stats latest(pethMainPseOperStatus) as status, latest(pethMainPsePower) as total_watts, latest(pethMainPseConsumptionPower) as used_watts by host
| eval utilization_pct=round(used_watts/total_watts*100,1)
| where utilization_pct > 80 | sort -utilization_pct
```

## Visualization

Gauge (per switch), Line chart (utilization trending), Table (switch, budget, used, remaining).

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
