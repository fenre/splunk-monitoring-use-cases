<!-- AUTO-GENERATED from UC-5.1.44.json — DO NOT EDIT -->

---
id: "5.1.44"
title: "Broadcast Storm Detection and Mitigation (Meraki MS)"
criticality: "critical"
splunkPillar: "Observability"
---

# UC-5.1.44 · Broadcast Storm Detection and Mitigation (Meraki MS)

> **Criticality:** Critical &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Anomaly

*We help you know early when something looks wrong with broadcast storm detection and mitigation so the team can act before it grows into a bigger outage.*

---

## Description

Identifies and alerts on broadcast storms that can freeze network performance across all switches.

## Value

NOC teams detect broadcast storms on Meraki MS switches and track storm control actions including port disablement, enabling rapid identification and resolution of network loops.

## Implementation

1. Enable the Assurance Alerts input. 2. Filter to deviceType=switch and storm/broadcast/loop keywords. 3. For continuous broadcast-rate visibility, deploy Splunk's SNMP modular input against each switch's management IP using IF-MIB ifInBroadcastPkts / ifOutBroadcastPkts counters.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: per-port broadcast packet counters are NOT exposed via syslog or the Dashboard API. Storm-control activations surface as switch alerts in the Assurance feed; for live broadcast counters use SNMP polling against the switch..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Assurance Alerts input. 2. Filter to deviceType=switch and storm/broadcast/loop keywords. 3. For continuous broadcast-rate visibility, deploy Splunk's SNMP modular input against each switch's management IP using IF-MIB ifInBroadcastPkts / ifOutBroadcastPkts counters.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (title="*storm*" OR title="*broadcast*" OR title="*loop*"
     OR categoryType="performance")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity
         by scope.devices{}.serial, scope.devices{}.name, network.name
| sort - alert_count
```

#### Understanding this SPL

**Broadcast Storm Detection and Mitigation (Meraki MS)** — NOC teams detect broadcast storms on Meraki MS switches and track storm control actions including port disablement, enabling rapid identification and resolution of network loops.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Assurance Alerts input (sourcetype=meraki:assurancealerts). NOTE: per-port broadcast packet counters are NOT exposed via syslog or the Dashboard API. Storm-control activations surface as switch alerts in the Assurance feed; for live broadcast counters use SNMP polling against the switch. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:assurancealerts. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:assurancealerts", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by scope.devices{}.serial, scope.devices{}.name, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Real-time alert dashboard; time-series of broadcast packets; affected port list.

## SPL

```spl
index=meraki sourcetype="meraki:assurancealerts"
    deviceType="MS"
    (title="*storm*" OR title="*broadcast*" OR title="*loop*"
     OR categoryType="performance")
    earliest=-24h
| stats count as alert_count,
        values(title) as alert_titles,
        latest(severity) as severity
         by scope.devices{}.serial, scope.devices{}.name, network.name
| sort - alert_count
```

## Visualization

Real-time alert dashboard; time-series of broadcast packets; affected port list.

## Known False Positives

Imaging, Wake-on-LAN, and some IoT devices can create broadcast spikes. Confirm port security and STP before blaming a DDoS.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
