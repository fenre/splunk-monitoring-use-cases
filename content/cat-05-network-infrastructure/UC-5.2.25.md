<!-- AUTO-GENERATED from UC-5.2.25.json — DO NOT EDIT -->

---
id: "5.2.25"
title: "Site-to-Site VPN Latency and Performance (Meraki MX)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.2.25 · Site-to-Site VPN Latency and Performance (Meraki MX)

## Description

Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.

## Value

Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.

## Implementation

Extract VPN latency and jitter metrics. Monitor tunnel performance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Cisco Meraki Add-on for Splunk` (Splunkbase 5580).
• Ensure the following data sources are available: `sourcetype=meraki type=vpn sourcetype=meraki:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Extract VPN latency and jitter metrics. Monitor tunnel performance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=cisco_network sourcetype="meraki" type=vpn latency=*
| stats avg(latency) as avg_vpn_latency, max(jitter) as max_jitter by tunnel_id, remote_site
| where avg_vpn_latency > 50
```

Understanding this SPL

**Site-to-Site VPN Latency and Performance (Meraki MX)** — Monitors latency and jitter on VPN tunnels to ensure quality of critical business traffic.

Documented **Data sources**: `sourcetype=meraki type=vpn sourcetype=meraki:api`. **App/TA** (typical add-on context): `Cisco Meraki Add-on for Splunk` (Splunkbase 5580). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: cisco_network; **sourcetype**: meraki. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=cisco_network, sourcetype="meraki". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by tunnel_id, remote_site** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_vpn_latency > 50` — typically the threshold or rule expression for this monitoring goal.


Step 3 — Validate
In the Meraki cloud dashboard, use the same organization, network, and time range as the search. Confirm VPN paths, tunnel states, uplinks, and device names you expect there match the Splunk view.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Gauge of VPN latency; latency trend line; jitter comparison chart.

## SPL

```spl
index=cisco_network sourcetype="meraki" type=vpn latency=*
| stats avg(latency) as avg_vpn_latency, max(jitter) as max_jitter by tunnel_id, remote_site
| where avg_vpn_latency > 50
```

## Visualization

Gauge of VPN latency; latency trend line; jitter comparison chart.

## References

- [Splunkbase app 5580](https://splunkbase.splunk.com/app/5580)
