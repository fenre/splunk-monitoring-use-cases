<!-- AUTO-GENERATED from UC-5.13.75.json — DO NOT EDIT -->

---
id: "5.13.75"
title: "ITSI Service Modeling for Catalyst Center"
status: "verified"
criticality: "high"
splunkPillar: "IT Operations"
---

# UC-5.13.75 · ITSI Service Modeling for Catalyst Center

> **Criticality:** High &middot; **Difficulty:** Expert &middot; **Pillar:** IT Operations &middot; **Type:** Availability, Performance &middot; **Wave:** Run &middot; **Status:** Verified

*We build a service-health model in Splunk ITSI that treats the entire network as a set of interconnected services — campus sites, wireless, security, compliance — and shows the health of each on a visual map. When something breaks, the model shows which service is affected and which devices are contributing, replacing dozens of individual alerts with one intelligent view.*

---

## Description

Creates an ITSI service model for Catalyst Center infrastructure with KPIs derived from device health, client health, network health, and issue data, enabling service-centric monitoring and correlation.

## Value

ITSI service modeling transforms per-device/per-sourcetype monitoring into business-service health, enabling correlation across all Catalyst Center data streams and integration with IT service management.

## Implementation

Create an ITSI service for Catalyst Center with the following KPI base searches:

1. **Device Health KPI:** `index=catalyst sourcetype="cisco:dnac:devicehealth" | stats avg(overallHealth) as device_health count(eval(overallHealth<50)) as unhealthy_devices`
2. **Client Health KPI:** `index=catalyst sourcetype="cisco:dnac:clienthealth" | stats avg(scoreDetail{}.scoreCategory.value) as client_health`
3. **Network Health KPI:** `index=catalyst sourcetype="cisco:dnac:networkhealth" | stats latest(healthScore) as network_health`
4. **Issue Volume KPI:** `index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED" | stats count as critical_issues`
5. **Compliance KPI:** `index=catalyst sourcetype="cisco:dnac:compliance" complianceStatus="NON_COMPLIANT" | stats count as non_compliant_devices`

Configure entity types: Network Device (matched on `deviceName`), Site (matched on `siteId`).

Set thresholds: Green (device_health>75, critical_issues=0), Yellow (device_health 50-75 OR critical_issues 1-3), Red (device_health<50 OR critical_issues>3).

## Detailed Implementation

### Prerequisites
- Splunk IT Service Intelligence (ITSI) must be licensed and installed on your Splunk deployment. ITSI is a premium product (SA-ITOA) — this UC is only applicable if ITSI is part of your platform.
- All crawl-tier Catalyst Center UCs must be operational (UC-5.13.1, .9, .16, .21, .28, .34, .45, .51) — they provide the KPI base searches for the ITSI service model.
- Catalyst Center device inventory must be imported as ITSI entities (see Step 1).
- Understanding of ITSI concepts: Services, KPIs, Entities, Glass Tables, Notable Events, Aggregation Policies.

### Step 1 — Import Catalyst Center devices as ITSI entities
Create an entity import search in ITSI:
```spl
index=catalyst sourcetype="cisco:dnac:device"
| dedup hostname
| table hostname, platformId, softwareVersion, managementIpAddress, siteId, deviceFamily
```

Configure entity mapping:
| ITSI Field | Source Field |
|------------|-------------|
| Title | hostname |
| Identifier | hostname, managementIpAddress |
| Informational | platformId, softwareVersion, siteId, deviceFamily |
| Entity type | network_device |

Schedule the entity import daily so new devices are automatically imported.

### Step 2 — Build the ITSI service hierarchy
```
Network Infrastructure (top-level service)
├── Campus Site: HQ (per-site service)
│   ├── Core & Distribution (device group KPIs)
│   ├── Access Layer (device group KPIs)
│   ├── Wireless Controllers (device group KPIs)
│   └── Client Experience (client health KPIs)
├── Campus Site: Branch-NYC
│   └── (same structure)
└── Cross-Product (optional)
    ├── ISE Authentication Health
    ├── ThousandEyes Path Quality
    └── SD-WAN WAN Health
```

Create services manually in ITSI or via the REST API. Each service has KPIs sourced from the corresponding Catalyst Center UC:

**KPI definitions:**

| KPI Name | Source UC | Base Search | Threshold Type |
|----------|---------|------------|----------------|
| Device Health (avg) | UC-5.13.1 | `index=catalyst sourcetype="cisco:dnac:devicehealth" \| stats avg(overallHealth) as avg_health by siteId` | Adaptive (stdev) |
| Unreachable Devices | UC-5.13.6 | `index=catalyst sourcetype="cisco:dnac:devicehealth" reachabilityHealth="Unreachable" \| stats dc(deviceName) as unreachable` | Static (critical > 0) |
| Client Health (avg) | UC-5.13.9 | Client health percentage from clienthealth summary | Adaptive |
| Active P1/P2 Issues | UC-5.13.23 | `index=catalyst sourcetype="cisco:dnac:issue" (priority="P1" OR priority="P2") status!="RESOLVED" \| stats dc(issueId) as p1p2` | Static (warning > 0, critical > 3) |
| Compliance Rate | UC-5.13.28 | Compliance percentage from compliance feed | Static (warning < 95, critical < 80) |
| CRITICAL PSIRTs | UC-5.13.34 | Advisory count with deviceCount > 0 | Static (warning > 0) |

For per-site services, add entity filters: `siteId = <site-specific-uuid>`.

### Step 3 — Configure KPI thresholds
Use **adaptive thresholds** for health scores (device health, client health, network health) — ITSI learns the normal operating range and alerts on deviations. This is superior to the fixed-threshold approach in UC-5.13.3/UC-5.13.18 because it adapts to each site's unique baseline.

Use **static thresholds** for count-based KPIs (unreachable devices, P1 issues, compliance rate) — these have clear good/bad boundaries that don't need adaptation.

Threshold configuration per KPI:
- Device Health (avg): adaptive, training period 7 days, sensitivity medium
- Unreachable Devices: static, normal=0, warning=0, critical>0
- Client Health: adaptive, training period 7 days, sensitivity medium
- Active P1/P2: static, normal=0, warning>0, critical>3
- Compliance Rate: static, normal>95, warning 80-95, critical<80
- CRITICAL PSIRTs: static, normal=0, warning>0, critical>0

### Step 4 — Build the Glass Table
Create a campus network topology Glass Table:
- **Top section**: overall network health score as a large gauge (from UC-5.13.16 KPI)
- **Middle section**: site bubbles arranged geographically, sized by device count, coloured by the site-level service health score (green/yellow/red)
- **Bottom section**: device list for the selected site, showing per-device health with indicators
- **Sidebar**: compliance rate, PSIRT count, active P1/P2 count as single-value tiles

The Glass Table provides the executive visualisation that UC-5.13.73 (Multi-Domain Dashboard) provides in standard Splunk dashboards — but with ITSI's service-aware colour coding and drill-down capabilities.

### Step 5 — Configure Notable Events and Episode Rules
ITSI Notable Events replace individual Splunk alerts for Catalyst Center UCs. Configure aggregation policies:

- **Group by site**: aggregate all KPI violations from the same `siteId` into one episode. This prevents alert fatigue when a single site failure generates 5 KPI violations simultaneously.
- **Severity mapping**: episode severity = highest individual KPI severity. A site with one critical KPI and four normal KPIs produces a critical episode.
- **Auto-close**: episodes close when all contributing KPIs return to normal for 30 minutes.

Notable event actions:
- ServiceNow integration: auto-create an incident for critical episodes
- PagerDuty: page the on-call engineer for critical episodes at core/distribution sites
- Slack: post all episodes to `#network-ops`

Validate:
(a) Verify entities import correctly: ITSI > Configuration > Entities > search for a known device hostname. It should appear with `platformId`, `softwareVersion`, and `siteId` as informational fields.

(b) Verify KPIs compute: ITSI > Services > [your service] > KPIs. Each KPI should show a current value and historical trend. Null values indicate the base search isn't returning results — check the SPL.

(c) Verify threshold detection: manually degrade a test device (if possible) and confirm the KPI transitions from normal to warning/critical.

(d) Verify episode grouping: trigger two KPI violations at the same site. They should aggregate into one episode, not two separate alerts.

Troubleshooting:

- **Entity import shows 0 entities** — the device inventory search returned no results. Check `index=catalyst sourcetype="cisco:dnac:device"` for events.

- **KPI shows null** — the base search SPL may have a syntax error or the data doesn't match the expected fields. Test the base search in Splunk Search first.

- **Service health is always grey** — KPI thresholds aren't configured. Set thresholds per KPI in ITSI > Services > [service] > Thresholds.

- **Too many notable events** — episode aggregation isn't configured. Set up aggregation policies to group KPIs by site.

- **Glass Table doesn't update** — the underlying KPI search interval may be too long. Set KPI search frequency to 5–15 minutes for real-time Glass Table updates.

- **Adaptive thresholds too sensitive** — extend the training period from 7 to 14 days, or reduce sensitivity from medium to low.

- **Want to model dependencies** — ITSI service dependencies allow you to model that "Client Experience depends on Wireless Controllers depends on Core Switches." Configure these so a core switch failure cascades the health impact to dependent services.

- **Performance** — each KPI runs a scheduled search. With 20 sites × 6 KPIs = 120 searches running every 5 minutes, verify search head capacity. Use `tstats` and accelerated data models where possible to reduce search cost.

## SPL

```spl
| from datamodel:"ITSI_KPI_Summary" | where service_name="*Catalyst Center*" | stats latest(kpi_urgency) as urgency latest(alert_level) as alert_level by service_name, kpiid, itsi_kpi_id | sort -urgency
```

## Visualization

ITSI Service Analyzer deep dive; glass table with KPI tiles; Episode Review for correlated episodes; optional deep link to Splunk dashboards for raw SPL drilldown.

## Known False Positives

**ITSI KPI flickering at a threshold boundary triggering frequent episodes.** When a KPI value oscillates around a threshold boundary (e.g., CPU at 79-81% with an 80% threshold), ITSI repeatedly opens and closes episodes. This creates noise without indicating a real problem. Distinguish by checking whether the KPI value is within 5% of the threshold and whether episodes are opening and closing within minutes. Suppress by configuring KPI threshold hysteresis (e.g., alert at 80%, clear at 75%) or using adaptive thresholds.

**Catalyst Center API poll timing creating artificial KPI gaps.** If the TA polls at 900-second intervals but the ITSI KPI is evaluated at 300-second intervals, there will be gaps where no data is available, potentially showing the KPI as unknown or N/A. Distinguish by checking whether KPI gaps align with the TA poll schedule. Suppress by aligning the KPI calculation window with the TA poll interval or using `| fillnull` to carry forward the last known value.

**Service dependency tree amplifying a single KPI failure to multiple service alerts.** In a hierarchical service model, a single failing KPI in a child service can propagate to parent services, generating alerts at every level. Distinguish by identifying the root cause KPI — the lowest-level service with a critical KPI is the true source. Suppress by configuring ITSI to identify root cause services and alert only on the root cause, not on every affected parent.

**Entity discovery adding new devices that lack historical KPI baselines.** When Catalyst Center discovers new devices, the corresponding ITSI entities have no historical data for baseline comparison. KPIs may show anomalous values until sufficient history is collected. Distinguish by checking whether the entity was recently discovered (entity creation time within the last 7 days). Suppress by applying a 7-day burn-in period for new entities before including them in adaptive threshold calculations.

## References

- [Splunkbase app 7538](https://splunkbase.splunk.com/app/7538)
- [Catalyst Center API docs](https://developer.cisco.com/docs/catalyst-center/)
- [Catalyst Center Intent API Reference — Cisco DevNet](https://developer.cisco.com/docs/catalyst-center/#!api-reference)
