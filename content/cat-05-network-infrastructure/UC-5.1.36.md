<!-- AUTO-GENERATED from UC-5.1.36.json — DO NOT EDIT -->

---
id: "5.1.36"
title: "Port Utilization and Congestion Alerts (Meraki MS)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.1.36 · Port Utilization and Congestion Alerts (Meraki MS)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We help you know early when something looks wrong with port utilization and congestion alerts so the team can act before it grows into a bigger outage.*

---

## Description

Identifies port saturation and congestion events that require capacity upgrades or load balancing adjustments.

## Value

Operations teams monitor Meraki MS switch port utilization and congestion, identifying saturated ports that require link aggregation or capacity upgrades.

## Implementation

1. In Splunk_TA_cisco_meraki, enable the Switch Ports Overview input. The TA polls GET /organizations/{orgId}/switch/ports/overview daily and writes one event per network with counts.byStatus.{active,inactive,disconnected}, counts.byMedia.{wired,wireless} and counts.byLinkSpeed.{10mbps,100mbps,1Gbps,10Gbps}. 2. Per-port utilization counters are NOT exposed by the Dashboard API; for live per-port flap detection enable the Webhook Logs (HEC) input and configure a Meraki alert profile that triggers on 'switch port status changed'. 3. Tune the 80% in-use threshold to your capacity policy.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
- Ensure the following data sources are available: Splunk_TA_cisco_meraki (Splunkbase #5580): Switch Ports Overview input (sourcetype=meraki:switchportsoverview, daily, OAuth scope switch:telemetry:read). Optional: configure the Webhook Logs (HEC) input + Meraki Dashboard alerts on port_status_changed for near-real-time per-port flap detection (sourcetype=meraki:webhook)..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
1. In Splunk_TA_cisco_meraki, enable the Switch Ports Overview input. The TA polls GET /organizations/{orgId}/switch/ports/overview daily and writes one event per network with counts.byStatus.{active,inactive,disconnected}, counts.byMedia.{wired,wireless} and counts.byLinkSpeed.{10mbps,100mbps,1Gbps,10Gbps}. 2. Per-port utilization counters are NOT exposed by the Dashboard API; for live per-port flap detection enable the Webhook Logs (HEC) input and configure a Meraki alert profile that triggers…

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki:switchportsoverview" earliest=-24h
| stats latest(counts.byStatus.active) as active_ports,
        latest(counts.byStatus.inactive) as inactive_ports,
        latest(counts.byStatus.disconnected) as disconnected_ports,
        latest(counts.byMedia.wired) as wired_ports
         by network.id, network.name
| eval total_ports = active_ports + inactive_ports + disconnected_ports
| eval pct_in_use = round(active_ports*100/total_ports, 1)
| where pct_in_use > 80
| sort - pct_in_use
```

#### Understanding this SPL

**Port Utilization and Congestion Alerts (Meraki MS)** — Operations teams monitor Meraki MS switch port utilization and congestion, identifying saturated ports that require link aggregation or capacity upgrades.

Documented **Data sources**: Splunk_TA_cisco_meraki (Splunkbase #5580): Switch Ports Overview input (sourcetype=meraki:switchportsoverview, daily, OAuth scope switch:telemetry:read). Optional: configure the Webhook Logs (HEC) input + Meraki Dashboard alerts on port_status_changed for near-real-time per-port flap detection (sourcetype=meraki:webhook). **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki:switchportsoverview. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki:switchportsoverview", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by network.id, network.name** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- `eval` defines or adjusts **total_ports** — often to normalize units, derive a ratio, or prepare for thresholds.
- `eval` defines or adjusts **pct_in_use** — often to normalize units, derive a ratio, or prepare for thresholds.
- Filters the current rows with `where pct_in_use > 80` — typically the threshold or rule expression for this monitoring goal.
- Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table of congested ports; timeline showing peak congestion; port utilization heatmap.

## SPL

```spl
index=meraki sourcetype="meraki:switchportsoverview" earliest=-24h
| stats latest(counts.byStatus.active) as active_ports,
        latest(counts.byStatus.inactive) as inactive_ports,
        latest(counts.byStatus.disconnected) as disconnected_ports,
        latest(counts.byMedia.wired) as wired_ports
         by network.id, network.name
| eval total_ports = active_ports + inactive_ports + disconnected_ports
| eval pct_in_use = round(active_ports*100/total_ports, 1)
| where pct_in_use > 80
| sort - pct_in_use
```

## Visualization

Table of congested ports; timeline showing peak congestion; port utilization heatmap.

## Known False Positives

Short bursts during backups, patch pushes, or video calls can approach thresholds without an outage. Match alerts to business hours and known batch jobs.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
