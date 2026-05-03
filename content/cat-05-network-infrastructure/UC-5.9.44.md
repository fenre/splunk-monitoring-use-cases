<!-- AUTO-GENERATED from UC-5.9.44.json — DO NOT EDIT -->

---
id: "5.9.44"
title: "Multi-Region SaaS Availability"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.44 · Multi-Region SaaS Availability

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We test that our cloud applications work from every part of the world where we have employees, because an app that works fine in New York might be down in Tokyo — and the vendor's status page won't tell us that.*

---

## Description

Monitors SaaS application availability from multiple geographic regions to detect regional outages that global averages would mask. A SaaS application can be 100% available from the US but completely down from the EU due to GDPR data residency routing, regional DNS failures, or CDN edge issues.

## Value

SaaS vendor status pages typically show global availability. If Salesforce reports 99.9% uptime globally, but your Singapore users experience 95% availability due to an APAC PoP issue, the vendor's global number hides your regional pain. Multi-region testing provides the evidence to escalate with the vendor: "Our tests from Singapore show 95% availability while US tests show 100%." This data is essential for organizations with SLAs that specify regional availability requirements.

## Implementation

Same HTTP Server tests as UC-5.9.43, with Cloud Agents distributed across all business-critical regions.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.43 apply (SaaS HTTP Server tests configured with `SaaS-<AppName>` naming convention, Cloud Agents from multiple regions).
- **Cloud Agents in at least 3 geographic regions.** This UC specifically measures regional availability disparities. You need agents in:
  - **Americas:** New York, Washington DC, Dallas, Los Angeles, São Paulo, Toronto (minimum 4).
  - **EMEA:** London, Frankfurt, Amsterdam, Paris, Stockholm (minimum 3).
  - **APAC:** Tokyo, Singapore, Sydney, Mumbai, Hong Kong (minimum 3).
  More agents = higher geographic resolution. ThousandEyes offers 200+ Cloud Agent locations.
- **Regional availability baselines.** Some SaaS providers have regional deployments (e.g., Microsoft 365 has tenants in specific geographies). An APAC user of a US-hosted SaaS tenant may experience higher latency but should NOT experience lower availability. If availability varies by region, it indicates routing, CDN, or provider infrastructure issues.
- **SaaS vendor regional status pages bookmarked.** Many vendors publish per-region status: Microsoft 365 Service Health Dashboard (per-region), AWS Health Dashboard, Google Workspace Status Dashboard. These help distinguish vendor-side regional issues from network-side issues.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
SaaS test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify regional agent coverage for SaaS tests:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="http-server" thousandeyes.test.name="*SaaS*" earliest=-1h
| stats dc(thousandeyes.source.agent.name) as agents values(thousandeyes.source.agent.location) as locations by thousandeyes.test.name
| sort thousandeyes.test.name
```
Each SaaS test should show agents from multiple countries/locations. If all agents are in the same region, this UC provides no regional comparison value.

**Why regional availability monitoring is different from overall availability (UC-5.9.43):**
UC-5.9.43 monitors overall SaaS health across all locations. This UC specifically looks for regional disparities — cases where a SaaS app is available in one region but degraded or down in another. This is a common pattern: SaaS providers have multi-region infrastructure, and a regional outage may only affect users in that geography. The vendor's global status page may show "Operational" while your APAC users are impacted.

### Step 2 — Create the search and alert
**Regional availability per SaaS app:**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*SaaS*" earliest=-4h
| eval region=case(match(thousandeyes.source.agent.location, "(?i)(new york|washington|dallas|los angeles|chicago|toronto|sao paulo|miami|seattle|denver|montreal|phoenix|atlanta)"), "Americas", match(thousandeyes.source.agent.location, "(?i)(london|frankfurt|amsterdam|paris|stockholm|dublin|oslo|madrid|zurich|milan|warsaw|brussels|bucharest)"), "EMEA", match(thousandeyes.source.agent.location, "(?i)(tokyo|singapore|sydney|mumbai|hong kong|seoul|jakarta|bangkok|melbourne|osaka|taipei)"), "APAC", 1=1, "Other")
| stats avg(http.server.request.availability) as avg_avail avg(http.client.request.duration) as avg_ttfb dc(thousandeyes.source.agent.name) as agent_count by thousandeyes.test.name, region
| eval avg_avail_pct=round(avg_avail,2), avg_ttfb_ms=round(avg_ttfb*1000,1)
| sort thousandeyes.test.name, region
```

**Understanding this SPL**

The `case()` statement maps agent locations to broad geographic regions. ThousandEyes Cloud Agents report their city-level location in `thousandeyes.source.agent.location`. The regex matches common city names to their region. Adjust the patterns based on your actual agent locations.

`avg(http.server.request.availability) as avg_avail` — availability percentage per region. If Americas shows 100% and APAC shows 95%, APAC users are experiencing outages that Americas users are not.

`dc(thousandeyes.source.agent.name) as agent_count` — shows how many agents contribute to each region's measurement. A region with only 1 agent may show misleading results (that agent could be the problem, not the SaaS app).

**Regional disparity detection (alert on uneven availability):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*SaaS*" earliest=-4h
| eval region=case(match(thousandeyes.source.agent.location, "(?i)(new york|washington|dallas|los angeles|chicago|toronto|sao paulo)"), "Americas", match(thousandeyes.source.agent.location, "(?i)(london|frankfurt|amsterdam|paris|stockholm|dublin|oslo)"), "EMEA", match(thousandeyes.source.agent.location, "(?i)(tokyo|singapore|sydney|mumbai|hong kong|seoul)"), "APAC", 1=1, "Other")
| stats avg(http.server.request.availability) as avg_avail by thousandeyes.test.name, region
| eventstats max(avg_avail) as best_region_avail min(avg_avail) as worst_region_avail by thousandeyes.test.name
| eval disparity=round(best_region_avail - worst_region_avail, 2)
| where disparity > 5
| table thousandeyes.test.name, region, avg_avail, best_region_avail, worst_region_avail, disparity
| sort -disparity
```
A disparity > 5% means one region is experiencing significantly worse availability than others. This is the core detection for this UC.

**Regional TTFB comparison (performance disparity):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*SaaS*" earliest=-4h
| eval region=case(match(thousandeyes.source.agent.location, "(?i)(new york|washington|dallas|los angeles|chicago|toronto|sao paulo)"), "Americas", match(thousandeyes.source.agent.location, "(?i)(london|frankfurt|amsterdam|paris|stockholm|dublin|oslo)"), "EMEA", match(thousandeyes.source.agent.location, "(?i)(tokyo|singapore|sydney|mumbai|hong kong|seoul)"), "APAC", 1=1, "Other")
| rex field=thousandeyes.test.name "SaaS-(?<saas_app>[^-]+)"
| stats avg(http.client.request.duration) as avg_ttfb p95(http.client.request.duration) as p95_ttfb by saas_app, region
| eval avg_ms=round(avg_ttfb*1000,1), p95_ms=round(p95_ttfb*1000,1)
| xyseries saas_app region avg_ms
```
This creates a matrix: rows = SaaS apps, columns = regions, values = average TTFB in ms. Reveals which SaaS apps perform poorly in which regions.

**Regional availability trending (detect emerging regional issues):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*SaaS*" earliest=-7d
| eval region=case(match(thousandeyes.source.agent.location, "(?i)(new york|washington|dallas|los angeles|chicago|toronto|sao paulo)"), "Americas", match(thousandeyes.source.agent.location, "(?i)(london|frankfurt|amsterdam|paris|stockholm|dublin|oslo)"), "EMEA", match(thousandeyes.source.agent.location, "(?i)(tokyo|singapore|sydney|mumbai|hong kong|seoul)"), "APAC", 1=1, "Other")
| timechart span=1h avg(http.server.request.availability) as avg_avail by region
```

**Scheduling:** cron `*/10 * * * *`, time range `-15m to now`. Alert when `disparity > 5` (regional availability gap exceeds 5%). Throttle by `thousandeyes.test.name` for 1 hour.

### Step 3 — Validate
(a) **Multi-region browser test.** Access the SaaS application from different geographic locations using VPN endpoints or browser-based geo-testing tools (e.g., GeoPeeker, Uptrends). Compare perceived availability and performance with ThousandEyes data.

(b) **Vendor regional status page cross-reference.** If ThousandEyes shows a regional availability drop, check the SaaS vendor's regional status page. Microsoft 365 → Service Health Dashboard → filter by region. Salesforce → trust.salesforce.com → filter by instance (NA, EU, AP).

(c) **Agent count validation.** A region with only 1 agent may show a false disparity if that single agent has a network issue. Ensure at least 2–3 agents per region for reliable disparity detection.

(d) **Consistent regional mapping.** Verify the `case()` regex correctly maps all your Cloud Agents to regions. Run: `| stats dc(thousandeyes.source.agent.name) by region` to check distribution. If most agents land in "Other", adjust the regex patterns.

(e) **Disparity threshold tuning.** Start with 5% disparity threshold. After 2 weeks, review alert volume. If too noisy, increase to 10%. If you're missing real regional outages, decrease to 3%.

### Step 4 — Operationalize
**Dashboard** ("SaaS Regional Availability" — designed for IT operations / service desk):
- Row 1 — Regional availability heatmap: SaaS app × region, colour-coded by availability. Green = 100%, yellow = 95–99%, red = < 95%. At a glance, shows which SaaS apps have regional issues.
- Row 2 — Regional TTFB comparison matrix: SaaS app × region with avg TTFB values. Reveals performance disparities even when availability is 100%.
- Row 3 — Regional availability trending: timechart with one line per region. Shows whether regional issues are transient or persistent.
- Row 4 — Active disparity alerts: table of SaaS apps with > 5% regional availability disparity, showing best region, worst region, and gap.

**Alerting (tiered):**
- Availability disparity > 5% for any SaaS app → low-urgency Slack notification to `#it-ops`. Include app name, best region, worst region, and gap.
- Availability < 95% from ALL agents in a single region → medium-urgency. An entire region is impacted.
- Availability < 95% from ALL regions for a SaaS app → high-urgency. Global SaaS outage. Post to internal status page immediately.

**Runbook** (owner: IT operations / vendor management):
1. **Regional availability drop.** (a) Check SaaS vendor's regional status page. (b) Check if the issue is limited to a specific ISP — if only agents in one ISP show the problem, it may be a peering issue, not a SaaS issue. (c) If vendor confirms a regional issue, post to internal status page with ETA.
2. **All regions affected — global SaaS outage.** (a) Confirm via vendor status page and social media (Twitter/X, Reddit). (b) Post to internal status page: "[SaaS app] experiencing global outage. Vendor status: [link]. ETA: [pending]." (c) If business-critical, activate contingency plan (offline workflows, backup systems).
3. **One region consistently underperforming.** (a) Check if your SaaS tenant is hosted in a different region — data may travel cross-continent for users in the underperforming region. (b) Request the SaaS vendor to evaluate routing optimization. (c) Consider deploying a SASE/proxy in the underperforming region to optimize the path.
4. **Disparity detected but vendor reports no issues.** (a) The issue may be in the network path, not the SaaS infrastructure. Use path visualization (UC-5.9.9) from the affected region's agents. (b) If agents go through SASE/proxy, the proxy may be adding latency or dropping requests for that region.

### Step 5 — Troubleshooting

- **All agents land in "Other" region** — The `case()` regex doesn't match your Cloud Agent locations. Run `| stats values(thousandeyes.source.agent.location) as locations` to see exact location strings, then update the regex patterns.

- **Disparity always shows 0** — Either all agents are in the same region (no geographic diversity), or the SaaS app truly performs identically everywhere (unlikely). Check agent distribution.

- **False disparity from single-agent regions** — If one region has only 1 agent and that agent has local connectivity issues, it falsely shows a regional problem. Require minimum 2 agents per region (`where agent_count >= 2`) before computing disparity.

- **SaaS app shows 100% availability but is functionally broken** — ThousandEyes HTTP Server tests check that the server responds with a 2xx/3xx status code. A SaaS app may return a 200 status with a login page or error page. For deeper validation, use Page Load or Transaction tests.

- **All common troubleshooting** — See UC-5.9.43 Step 5 for SaaS monitoring issues, UC-5.9.34 Step 5 for HTTP test issues, and UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="*SaaS*" earliest=-24h
| stats avg(http.server.request.availability) as avg_avail by thousandeyes.test.name, thousandeyes.source.agent.geo.country.iso_code
| where avg_avail < 100
| sort avg_avail
```

## Visualization

(1) Map: SaaS availability by agent location. (2) Table: regions with < 100% availability. (3) Timechart: availability by region.

## Known False Positives

**Regional agent connectivity issues.** If the ThousandEyes Cloud Agent in a region has local connectivity issues, it may appear that the SaaS application is unavailable from that region when the issue is actually with the test agent itself. Cross-reference with UC-5.9.22 (Local Agent Issue Monitoring).

**Geo-based access restrictions.** Some SaaS applications restrict access by geographic region (GDPR, export controls). Test failures from restricted regions are expected.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — HTTP metrics](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
