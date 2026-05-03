<!-- AUTO-GENERATED from UC-5.4.37.json — DO NOT EDIT -->

---
id: "5.4.37"
title: "Aruba Client Experience and Connectivity Score (HPE Aruba)"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.4.37 · Aruba Client Experience and Connectivity Score (HPE Aruba)

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We watch aruba client experience and connectivity score (hpe aruba) so we notice problems while they are still small, and we can fix them before Wi-Fi users get dropped calls or dead spots.*

---

## Description

Aruba Central provides per-client connectivity scores based on association time, authentication time, DHCP time, DNS resolution time, and throughput. Low scores identify problematic clients, congested APs, or misconfigured SSIDs before users report issues. Trending scores over time validates infrastructure changes.

## Value

Network operations teams track Aruba Central client connectivity scores with component breakdown (association, authentication, DHCP, DNS timing), identifying specific bottlenecks degrading wireless experience per site.

## Implementation

Use Aruba Central API credentials with least privilege; poll client health/experience endpoints on a schedule or stream via a forwarder, normalizing to JSON on HEC with indexed fields `client_mac`, `ap_name`, `ssid`, `connectivity_score`, and timing breakdowns when available. Baseline per site and SSID; alert on drops after code upgrades or RF changes.

## Detailed Implementation

### Prerequisites
- Custom HEC or scripted input polling Aruba Central REST API client health endpoints. Data in `index=network` with `sourcetype=aruba:central` or `sourcetype=aruba:central:client`. Key fields: `connectivity_score` (0-100 composite score), `client_mac`, `ap_name`, `ssid`, `site_name`, and timing breakdowns: `assoc_time_ms` (association time), `auth_time_ms` (authentication time), `dhcp_time_ms` (DHCP time), `dns_time_ms` (DNS resolution time).
- Aruba Central calculates the connectivity score from five components: (1) Association time — how long the 802.11 association takes, (2) Authentication time — 802.1X/RADIUS exchange duration, (3) DHCP time — time to obtain IP address, (4) DNS time — DNS resolution latency, (5) Throughput — actual data transfer rate. Each component contributes to the 0-100 composite score.
- Set up a scripted input or use a tool like Aruba Central Python SDK to poll `/monitoring/v2/clients` every 5 minutes and push to HEC. Include `client_mac`, `ap_name`, `ssid`, `site_name`, `connectivity_score`, and all timing fields.

### Step 1 — Configure data collection
Create a scripted input polling Aruba Central API:
1. Generate API credentials: Aruba Central > Account Home > API Gateway > Create Token.
2. Build a Python script using `pycentral` SDK or direct REST calls to `/monitoring/v2/clients`.
3. Configure HEC token in Splunk for `sourcetype=aruba:central`.

Verify data:
```spl
index=network (sourcetype="aruba:central" OR sourcetype="aruba:central:client") earliest=-4h
| where isnotnull(connectivity_score) OR isnotnull(client_health_score)
| stats count avg(connectivity_score) as avg_score by site_name
```

### Step 2 — Create the search and alert

**Primary search — Client experience scoring with component breakdown:**
```spl
index=network (sourcetype="aruba:central" OR sourcetype="aruba:central:client") earliest=-4h
| eval score=coalesce(connectivity_score, client_health_score, experience_score, health_score)
| eval ap=coalesce(ap_name, ap_serial, device_name)
| stats avg(score) as avg_score min(score) as worst_score perc95(score) as p95_score dc(client_mac) as clients avg(assoc_time_ms) as avg_assoc avg(auth_time_ms) as avg_auth avg(dhcp_time_ms) as avg_dhcp avg(dns_time_ms) as avg_dns by ap, ssid, site_name
| eval grade=case(avg_score > 85, "A — Excellent", avg_score > 70, "B — Good", avg_score > 55, "C — Fair", avg_score > 40, "D — Poor", 1==1, "F — Critical")
| eval bottleneck=case(avg_auth > 500, "Authentication slow (".round(avg_auth, 0)."ms) — check RADIUS", avg_dhcp > 2000, "DHCP slow (".round(avg_dhcp, 0)."ms) — check DHCP server", avg_dns > 200, "DNS slow (".round(avg_dns, 0)."ms) — check DNS resolver", avg_assoc > 100, "Association slow (".round(avg_assoc, 0)."ms) — RF issue", 1==1, "No single bottleneck")
| where avg_score < 75 OR worst_score < 50
| sort avg_score
```

**Experience score trending (validates infrastructure changes):**
```spl
index=network (sourcetype="aruba:central" OR sourcetype="aruba:central:client") earliest=-7d
| eval score=coalesce(connectivity_score, client_health_score, experience_score)
| bin _time span=1h
| stats avg(score) as avg_score dc(client_mac) as clients by _time, site_name
| timechart span=1h avg(avg_score) by site_name
```

This search is essential for change validation: overlay the score trend with a maintenance window annotation. If you upgraded AOS firmware on Tuesday at 2 AM, the score trend should improve (or at least not degrade) after the change.

### Step 3 — Validate
(a) Compare Splunk connectivity scores with Aruba Central dashboard: Monitor > Clients > Experience.
(b) Identify a site with known WiFi complaints and verify it shows lower scores.
(c) Test individual components: slow down DNS (e.g., test with a remote DNS server) and verify the score drops and "DNS slow" appears in the bottleneck field.

### Step 4 — Operationalize
Dashboard ("Aruba — Client Experience"):
- Row 1 — Single-value tiles: "Average score (all sites)", "Worst site", "Sites rated D/F", "Total clients".
- Row 2 — Per-site/AP experience table with grade, bottleneck identification, and client count.
- Row 3 — 7-day experience score trending by site (with change window annotations).

Alerting:
- Warning (site avg score drops > 15 points from 7-day baseline): degradation detected.
- Warning (site avg score < 55 for > 30 min): poor wireless experience.
- Info (weekly): client experience report card for all sites.

### Step 5 — Troubleshooting

- **Low score, bottleneck is "Authentication slow"** — RADIUS/ClearPass latency is degrading the connect experience. Check ClearPass server load, network path to ClearPass, and authentication policy complexity.

- **Low score, bottleneck is "DHCP slow"** — DHCP response time high. Check: (1) DHCP server load and scope availability, (2) DHCP relay agent (IP helper) configuration on the VLAN, (3) Network path between client VLAN and DHCP server.

- **Score dropped after firmware upgrade** — Some AOS firmware versions have known issues with specific AP models. Check Aruba support advisories for the AOS version. Roll back if necessary and report to Aruba TAC.

- **API data not updating** — Check the scripted input: (1) API token expiry (Aruba Central tokens expire — refresh them), (2) Rate limiting (Central API has rate limits), (3) Script execution errors in splunkd.log.

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

## Known False Positives

Wireless metrics move with user behavior, maintenance, and nearby RF; we tune alerts around change windows and known busy hours so normal days do not page the team.

## References

- [Cato Networks Events App](https://splunkbase.splunk.com/app/8037)
