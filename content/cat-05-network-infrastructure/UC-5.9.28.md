<!-- AUTO-GENERATED from UC-5.9.28.json — DO NOT EDIT -->

---
id: "5.9.28"
title: "Geographic Workforce Performance Comparison"
status: "verified"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-5.9.28 · Geographic Workforce Performance Comparison

> **Criticality:** Medium &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance, Capacity &middot; **Wave:** Run &middot; **Status:** Verified

*We compare how well the internet works for employees in different parts of the world, so we know which offices or countries need better network infrastructure.*

---

## Description

Compares network performance experienced by the workforce across geographic regions — country-level and optionally region/city-level — to identify locations with consistently poor connectivity. Provides evidence for infrastructure investment decisions (adding VPN concentrators, SD-WAN edges, or ISP contracts in underperforming regions).

## Value

Global organizations often have anecdotal complaints from specific offices or regions — "India is always slow," "the Brazil team drops calls." This UC replaces anecdotes with data. If the India workforce consistently shows 30% lower network scores than the US workforce, that's a quantifiable gap that justifies adding a VPN concentrator in Mumbai, upgrading the ISP contract, or deploying a local SD-WAN edge. Conversely, if the data shows India's network scores are actually comparable to the US, the problem is elsewhere (application architecture, server location) and the team can investigate accordingly. The geographic view also detects regional ISP outages or degradation that only affects a subset of the workforce — a narrower signal than the global Internet Insights events (UC-5.9.18).

## Implementation

Uses the same Endpoint Agent data stream as UC-5.9.24. Aggregates by geographic attributes to compare regions. For finer granularity, use `thousandeyes.source.agent.geo.region.iso_code` or `thousandeyes.source.agent.location`.

## Detailed Implementation

### Prerequisites
- All prerequisites from UC-5.9.24 apply.
- **Geographically distributed workforce.** This UC provides value when Endpoint Agents are deployed across multiple countries/regions.

### Step 1 — Configure data collection
Same as UC-5.9.24.

Verify geographic distribution:
```spl
index=thousandeyes_metrics thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| stats dc(thousandeyes.source.agent.name) as endpoints by thousandeyes.source.agent.geo.country.iso_code
| sort -endpoints
```

### Step 2 — Create the search
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency avg(network.loss) as avg_loss dc(thousandeyes.source.agent.name) as endpoints by thousandeyes.source.agent.geo.country.iso_code
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```

**Region-level detail** (within a country):
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" thousandeyes.source.agent.geo.country.iso_code="US" earliest=-7d
| stats avg(network.score) as avg_score dc(thousandeyes.source.agent.name) as endpoints by thousandeyes.source.agent.geo.region.iso_code
| where endpoints >= 3
| sort avg_score
```

**Region comparison with ISP detail:**
```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| stats avg(network.score) as avg_score dc(thousandeyes.source.agent.name) as endpoints by thousandeyes.source.agent.geo.country.iso_code, thousandeyes.source.agent.network.org
| where endpoints >= 3
| sort thousandeyes.source.agent.geo.country.iso_code, avg_score
```
This reveals whether a country's poor performance is ISP-specific or universal.

**Scheduling:** Weekly report: cron `0 8 * * 1` (Monday 8 AM), time range `-7d to now`.

### Step 3 — Validate
(a) Verify geographic attributes are populated. If `geo.country.iso_code` is empty for many agents, the GeoIP lookup may not be working — check the Endpoint Agent's internet connectivity for geo-resolution.
(b) Cross-reference country endpoint counts with your HR/people data to ensure representative coverage.

### Step 4 — Operationalize
**Monthly executive report** ("Global Digital Experience Report"):
- Map visualization: global network health by country.
- Trend: which regions improved or degraded month-over-month.
- Action items: investment recommendations for worst-performing regions.

**Runbook** (owner: global IT / network architecture):
1. Consistently underperforming region → evaluate infrastructure investments:
   a. Add VPN concentrator or SD-WAN edge in the region.
   b. Negotiate ISP contracts with better-performing local providers.
   c. Deploy CDN edge nodes for frequently accessed applications.
2. Sudden regional degradation → check for ISP outages (correlate with UC-5.9.18 Internet Insights events).
3. Specific ISP in a region underperforming → recommend affected users switch ISPs or provide cellular backup.

### Step 5 — Troubleshooting
- **All endpoints show the same country** — If all Endpoint Agents resolve to one country, GeoIP data may be reflecting the VPN egress point rather than the user's actual location. Check whether always-on VPN is masking the user's true location.
- See UC-5.9.24 Step 5 for general endpoint troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.domain="endpoint" target.type="gateway" earliest=-7d
| stats avg(network.score) as avg_score avg(network.latency) as avg_latency avg(network.loss) as avg_loss dc(thousandeyes.source.agent.name) as endpoints by thousandeyes.source.agent.geo.country.iso_code
| eval avg_latency_ms=round(avg_latency*1000,1)
| sort avg_score
```

## Visualization

(1) Choropleth map: countries colour-coded by average network score. (2) Bar chart: average score by country, sorted worst-first. (3) Table: country, region, endpoints, avg score, avg latency, avg loss. (4) Timechart: average score by country over 7 days — shows daily patterns and regional outages.

## Known False Positives

**Low endpoint count in a region.** If only 2 endpoints report from a country, a single bad connection skews the entire country average. Require a minimum endpoint count (e.g., ≥ 5) before treating the data as representative.

**Time zone differences.** Comparing scores across time zones during the same clock time is misleading — 2 PM in San Francisco is midnight in Singapore. Compare during each region's business hours, or use a 24-hour average.

**Infrastructure differences.** Office workers (enterprise-grade networks) vs remote workers (residential ISPs) may dominate a region's average. Segment by connection type and network.org (ISP) within each region for accurate comparison.

**Endpoint Agent version differences.** Different agent versions across regions may produce slightly different metric quality. Ensure consistent agent versions.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes OTel v2 — Geographic attributes](https://docs.thousandeyes.com/product-documentation/integration-guides/opentelemetry/data-model/data-model-v2/metrics)
