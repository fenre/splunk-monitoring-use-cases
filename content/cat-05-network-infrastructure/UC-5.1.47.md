<!-- AUTO-GENERATED from UC-5.1.47.json — DO NOT EDIT -->

---
id: "5.1.47"
title: "Trunk Link Utilization and Performance (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.47 · Trunk Link Utilization and Performance (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with trunk link utilization and performance so the team can act before it grows into a bigger outage.*

---

## Description

Monitors inter-switch and uplink trunk utilization to identify bandwidth constraints.

## Value

Network engineers monitor Meraki MS trunk link utilization, detecting inter-switch uplink saturation that impacts all downstream VLANs and devices.

## Implementation

1. Enable the Switch Ports by Switch input. The TA polls GET /organizations/{orgId}/switch/ports/bySwitch daily and emits one event per switch with a ports[] array of {portId, name, type, enabled, status, vlan, allowedVlans, ...}. 2. Filter where type=trunk to identify uplink ports between switches. 3. For live link-down or utilization, configure a Meraki webhook alert profile and ingest via the Webhook Logs (HEC) input.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Switch Ports by Switch input (sourcetype=meraki:switchportsbyswitch, daily, TA v3.2+, OAuth scope switch:config:read). Per-port utilization counters are NOT exposed by the polling API; use the Webhook Logs (HEC) input + Meraki alert profile 'switch port status changed' or 'switch port flapping' for live trunk-flap detection..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. Enable the Switch Ports by Switch input. The TA polls GET /organizations/{orgId}/switch/ports/bySwitch daily and emits one event per switch with a ports[] array of {portId, name, type, enabled, status, vlan, allowedVlans, ...}. 2. Filter where type=trunk to identify uplink ports between switches. 3. For live link-down or utilization, configure a Meraki webhook alert profile and ingest via the Webhook Logs (HEC) input.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:switchportsbyswitch" earliest=-24h
| spath path=ports{} output=port_arr
| mvexpand port_arr
| spath input=port_arr
| where type="trunk" AND enabled="true"
| stats count as trunk_port_count,
        values(name) as trunk_port_names,
        sum(eval(if(status="Connected",0,1))) as down_trunks
         by serial, name, network.name
| where down_trunks > 0
| sort - down_trunks
```

#### Understanding this SPL

**Trunk Link Utilization and Performance (Meraki MS)** — Network engineers monitor Meraki MS trunk link utilization, detecting inter-switch uplink saturation that impacts all downstream VLANs and devices.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Switch Ports by Switch input (sourcetype=meraki:switchportsbyswitch, daily, TA v3.2+, OAuth scope switch:config:read). Per-port utilization counters are NOT exposed by the polling API; use the Webhook Logs (HEC) input + Meraki alert profile 'switch port status changed' or 'switch port flapping' for live trunk-flap detection. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:switchportsbyswitch. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:switchportsbyswitch", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- Extracts structured paths (JSON/XML) with `spath`.
- Expands multivalue fields with `mvexpand` — use `limit=` to cap row explosion.
- Extracts structured paths (JSON/XML) with `spath`.
- Filters the current rows with `where type="trunk" AND enabled="true"` — typically the threshold or rule expression for this monitoring goal.
- `stats` rolls up events into metrics; results are split **by serial, name, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where down_trunks > 0` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Trunk link utilization heatmap; timeline showing peak demand; capacity planning chart.

## SPL

```spl
index=meraki sourcetype="meraki:switchportsbyswitch" earliest=-24h
| spath path=ports{} output=port_arr
| mvexpand port_arr
| spath input=port_arr
| where type="trunk" AND enabled="true"
| stats count as trunk_port_count,
        values(name) as trunk_port_names,
        sum(eval(if(status="Connected",0,1))) as down_trunks
         by serial, name, network.name
| where down_trunks > 0
| sort - down_trunks
```

## Visualization

Trunk link utilization heatmap; timeline showing peak demand; capacity planning chart.

## Known False Positives

Short bursts during backups, patch pushes, or video calls can approach thresholds without an outage. Match alerts to business hours and known batch jobs.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
