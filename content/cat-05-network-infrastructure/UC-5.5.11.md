<!-- AUTO-GENERATED from UC-5.5.11.json — DO NOT EDIT -->

---
id: "5.5.11"
title: "OMP Route Table Monitoring"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.5.11 · OMP Route Table Monitoring

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance

*We keep an eye on how our wide-area links and SD-WAN paths are behaving so we spot a bad circuit or policy issue before branch users lose voice, video, or critical apps.*

---

## Description

OMP (Overlay Management Protocol) distributes routes across the SD-WAN fabric. Route churn, missing prefixes, or unexpected withdrawals indicate overlay instability that degrades site-to-site reachability.

## Value

Network operations teams monitor SD-WAN OMP route table health to detect routing anomalies, route churn, and missing network reachability that could isolate sites or disrupt application connectivity.

## Implementation

Poll vManage OMP peers and routes API endpoints. Baseline route count per device. Alert when a site loses more than 20% of its expected routes or when OMP peer adjacencies drop. Track route churn rate over time to identify flapping prefixes.

## Detailed Implementation

### Prerequisites
- Cisco Catalyst Add-on for Splunk polling vManage API for OMP (Overlay Management Protocol) route table. Data in `index=sdwan` with `sourcetype=cisco:sdwan:omp`. Key fields: `site_id`, `system_ip`, `prefix`, `protocol`, `from_peer` (vSmart IP), `originator` (advertising device), `color`, `status` (C=chosen, I=installed, R=received), `metric`, `preference`.
- OMP is the SD-WAN control plane routing protocol (similar to BGP for the SD-WAN overlay). vSmart controllers distribute OMP routes to edge devices. Route changes can indicate: network topology changes, policy updates, site failures, or control plane issues.
- Critical OMP metrics: total routes received, routes installed, route churn rate (frequent additions/removals), and missing expected routes.
- Build `sdwan_expected_routes.csv` lookup: `site_id,expected_prefixes,expected_count` for each site's expected OMP route count during normal operation.

### Step 1 — Configure data collection
Verify OMP route data:
```spl
index=sdwan sourcetype="cisco:sdwan:omp" earliest=-15m
| stats count dc(prefix) as unique_prefixes by site_id, status
```

### Step 2 — Create the search and alert

**Primary search — OMP route table anomalies:**
```spl
index=sdwan sourcetype="cisco:sdwan:omp" status="C" earliest=-15m
| stats dc(prefix) as installed_routes values(from_peer) as vsmart_sources by site_id, system_ip
| lookup sdwan_expected_routes.csv site_id OUTPUT expected_count
| eval route_delta=if(isnotnull(expected_count), installed_routes - expected_count, null())
| eval pct_of_expected=if(isnotnull(expected_count), round(100*installed_routes/expected_count, 1), null())
| lookup sdwan_sites.csv site_id OUTPUT site_name tier
| eval status=case(pct_of_expected < 50, "CRITICAL", pct_of_expected < 80, "WARNING", route_delta < -10, "DEGRADED", installed_routes < 5, "MINIMAL", 1==1, "OK")
| where status!="OK"
| sort status, tier
```

#### Understanding this SPL: A sudden drop in OMP route count means the edge device has lost visibility to parts of the network. If a site normally has 200 OMP routes and suddenly drops to 50, it means 150 network prefixes are unreachable from that site. This could be caused by: vSmart failure (routes not distributed), remote site failure (routes withdrawn), or policy change (routes filtered).

**OMP route churn detection:**
```spl
index=sdwan sourcetype="cisco:sdwan:omp" earliest=-2h
| bin _time span=10m
| stats dc(prefix) as routes by _time, site_id
| streamstats window=2 current=t range(routes) as route_churn by site_id
| where route_churn > 20
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval severity=case(route_churn > 100, "CRITICAL", route_churn > 50, "HIGH", 1==1, "WARNING")
```

**Route distribution by originator:**
```spl
index=sdwan sourcetype="cisco:sdwan:omp" status="C" earliest=-15m
| stats dc(prefix) as routes by originator
| lookup sdwan_devices.csv system_ip as originator OUTPUT hostname site_id
| lookup sdwan_sites.csv site_id OUTPUT site_name
| eval label=if(isnotnull(hostname), hostname." (".site_name.")", originator)
| sort -routes
```

### Step 3 — Validate
(a) On an edge device CLI: `show omp routes` — count the installed routes and compare with Splunk.
(b) On vSmart: `show omp routes` — verify the controller has the full route table.
(c) After a planned site addition, verify the new site's prefixes appear in OMP routes across the fabric.

### Step 4 — Operationalize
Dashboard ("SD-WAN — OMP Route Health"):
- Row 1 — Single-value tiles: "Sites with route deficit", "Total OMP routes", "Route churn (2h)", "Sites below 80% expected routes".
- Row 2 — Route anomaly table: site, installed routes, expected routes, delta, % of expected, status.
- Row 3 — Route churn chart: 2-hour timeline showing route count changes per site.
- Row 4 — Route distribution by originator: which devices are advertising how many routes.

Alerting:
- Critical (site has < 50% of expected routes): major routing loss — significant reachability impact.
- High (route churn > 100 in 10 minutes): routing instability — possible control plane flap.
- Warning (site below 80% expected routes): partial route loss — investigate.

### Step 5 — Troubleshooting

- **OMP route count drops to near zero** — Check control connections (UC-5.5.5). If the edge lost its vSmart connection, it won't receive new routes. Existing routes may age out depending on configuration.

- **Route churn coincides with policy push** — vManage policy changes can cause temporary route redistribution as vSmart recalculates and pushes updated routes. Allow 5-10 minutes for convergence after a policy push.

- **Missing routes from specific originator** — The originating device may have lost its vSmart connection, or its OMP advertisements are being filtered by a centralized data policy on vSmart.

## SPL

```spl
index=sdwan sourcetype="cisco:sdwan:omp"
| stats dc(prefix) as route_count, dc(peer) as peer_count by system_ip, site_id
| appendpipe [| stats avg(route_count) as baseline_routes]
| where route_count < baseline_routes * 0.8
| table system_ip site_id route_count peer_count
```

## Visualization

Line chart (route count over time per site), Table (devices below baseline), Single value (total OMP peers).

## Known False Positives

Route counts and peer mesh views shift during design changes, new site onboarding, or when a single transport is taken down for tests; confirm intent in vManage before escalation.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
