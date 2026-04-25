<!-- AUTO-GENERATED from UC-5.4.37.json — DO NOT EDIT -->

---
id: "5.4.37"
title: "Aruba Client Experience and Connectivity Score (HPE Aruba)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.37 · Aruba Client Experience and Connectivity Score (HPE Aruba)

## Description

Aruba Central provides per-client connectivity scores based on association time, authentication time, DHCP time, DNS resolution time, and throughput. Low scores identify problematic clients, congested APs, or misconfigured SSIDs before users report issues. Trending scores over time validates infrastructure changes.

## Value

Aruba Central provides per-client connectivity scores based on association time, authentication time, DHCP time, DNS resolution time, and throughput. Low scores identify problematic clients, congested APs, or misconfigured SSIDs before users report issues. Trending scores over time validates infrastructure changes.

## Implementation

Use Aruba Central API credentials with least privilege; poll client health/experience endpoints on a schedule or stream via a forwarder, normalizing to JSON on HEC with indexed fields `client_mac`, `ap_name`, `ssid`, `connectivity_score`, and timing breakdowns when available. Baseline per site and SSID; alert on drops after code upgrades or RF changes.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Custom HEC or scripted input (Aruba Central REST API — client health / experience metrics).
• Ensure the following data sources are available: Aruba Central API (client health / experience), recommended `sourcetype=aruba:central` (JSON from HEC).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Use Aruba Central API credentials with least privilege; poll client health/experience endpoints on a schedule or stream via a forwarder, normalizing to JSON on HEC with indexed fields `client_mac`, `ap_name`, `ssid`, `connectivity_score`, and timing breakdowns when available. Baseline per site and SSID; alert on drops after code upgrades or RF changes.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="aruba:central" OR sourcetype="aruba:central:client"
| eval score=coalesce(connectivity_score, client_health_score, experience_score, health_score)
| eval ap=coalesce(ap_name, ap_serial, device_name)
| stats avg(score) as avg_score, min(score) as worst_score, perc95(score) as p95_score, dc(client_mac) as clients by ap, ssid, site_name
| where avg_score < 75 OR worst_score < 50 OR p95_score < 70
| sort avg_score
```

Understanding this SPL

**Aruba Client Experience and Connectivity Score (HPE Aruba)** — Aruba Central provides per-client connectivity scores based on association time, authentication time, DHCP time, DNS resolution time, and throughput. Low scores identify problematic clients, congested APs, or misconfigured SSIDs before users report issues. Trending scores over time validates infrastructure changes.

Documented **Data sources**: Aruba Central API (client health / experience), recommended `sourcetype=aruba:central` (JSON from HEC). **App/TA** (typical add-on context): Custom HEC or scripted input (Aruba Central REST API — client health / experience metrics). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: aruba:central, aruba:central:client. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="aruba:central". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **score** — often to normalize units, derive a ratio, or prepare for thresholds.
• `eval` defines or adjusts **ap** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by ap, ssid, site_name** so each row reflects one combination of those dimensions.
• Filters the current rows with `where avg_score < 75 OR worst_score < 50 OR p95_score < 70` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.


Step 3 — Validate
In Aruba Central, the mobility controller UI, or ClearPass Policy Manager (Access Tracker / policy views), compare authentication and health events with the search for the same timeframe.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (mean connectivity score by SSID), Table (worst APs and SSIDs), Histogram (score distribution), Scatter (clients vs score) for drill-down.

## SPL

```spl
index=network sourcetype="aruba:central" OR sourcetype="aruba:central:client"
| eval score=coalesce(connectivity_score, client_health_score, experience_score, health_score)
| eval ap=coalesce(ap_name, ap_serial, device_name)
| stats avg(score) as avg_score, min(score) as worst_score, perc95(score) as p95_score, dc(client_mac) as clients by ap, ssid, site_name
| where avg_score < 75 OR worst_score < 50 OR p95_score < 70
| sort avg_score
```

## Visualization

Timechart (mean connectivity score by SSID), Table (worst APs and SSIDs), Histogram (score distribution), Scatter (clients vs score) for drill-down.

## References

- [Cato Networks Events App](https://splunkbase.splunk.com/app/8037)
