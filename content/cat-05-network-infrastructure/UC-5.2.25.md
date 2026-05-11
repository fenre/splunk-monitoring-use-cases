<!-- AUTO-GENERATED from UC-5.2.25.json — DO NOT EDIT -->

---
id: "5.2.25"
title: "Site-to-Site VPN Latency and Performance (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.25 · Site-to-Site VPN Latency and Performance (Meraki MX)

> **Criticality:** Medium &middot; **Difficulty:** Beginner &middot; **Pillar:** Observability &middot; **Type:** Performance

*We follow tunnel delay on those paths so a slow provider or far peer is visible before people open tickets about "the VPN feels off."*

---

## Description

Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.

## Value

Operations teams trend Meraki MX site-to-site VPN latency, packet loss, and jitter per tunnel, detecting performance degradation that impacts inter-site application quality.

## Implementation

Extract VPN latency and jitter metrics. Monitor tunnel performance.

## Detailed Implementation

### Prerequisites
- Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA)..
- Ensure the following data sources are available: `sourcetype=meraki type=vpn sourcetype=meraki:devices` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA..
- For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

### Step 1 — Configure data collection
Extract VPN latency and jitter metrics. Monitor tunnel performance.

### Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=meraki sourcetype="meraki" type=events (vpn_connectivity_change OR "Auto VPN") latency=*
| stats avg(latency) as avg_vpn_latency, max(jitter) as max_jitter by tunnel_id, remote_site
| where avg_vpn_latency > 50
```

#### Understanding this SPL

**Site-to-Site VPN Latency and Performance (Meraki MX)** — Operations teams trend Meraki MX site-to-site VPN latency, packet loss, and jitter per tunnel, detecting performance degradation that impacts inter-site application quality.

Documented **Data sources**: `sourcetype=meraki type=vpn sourcetype=meraki:devices` | Alternate ingest: Splunk Connect for Syslog (SC4S) Meraki vendor pack — points the Meraki dashboard at an SC4S receiver and produces sourcetype="meraki" syslog events (free-form text extracted with rex). Use when you don't want to deploy the polling API TA. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580) | Optional alternate path: Splunk Connect for Syslog (SC4S) with the Meraki vendor pack ingests Meraki MX/MS/MR appliance syslog as sourcetype="meraki" (does not require the API TA). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: meraki; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

- Scopes the data: index=meraki, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
- `stats` rolls up events into metrics; results are split **by tunnel_id, remote_site** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
- Filters the current rows with `where avg_vpn_latency > 50` — typically the threshold or rule expression for this monitoring goal.


### Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

### Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge of VPN latency; latency trend line; jitter comparison chart.

## SPL

```spl
index=meraki sourcetype="meraki" type=events (vpn_connectivity_change OR "Auto VPN") latency=*
| stats avg(latency) as avg_vpn_latency, max(jitter) as max_jitter by tunnel_id, remote_site
| where avg_vpn_latency > 50
```

## Visualization

Gauge of VPN latency; latency trend line; jitter comparison chart.

## Known False Positives

ISPs, weather, and remote Wi-Fi often dominate latency; rule out the path before blaming the head-end device.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
