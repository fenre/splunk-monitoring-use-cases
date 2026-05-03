<!-- AUTO-GENERATED from UC-5.9.43.json — DO NOT EDIT -->

---
id: "5.9.43"
title: "SaaS Application Response Time Comparison"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.43 · SaaS Application Response Time Comparison

> **Criticality:** High &middot; **Difficulty:** Intermediate &middot; **Pillar:** Observability &middot; **Type:** Performance &middot; **Wave:** Walk &middot; **Status:** Verified

*We test how fast each of our cloud applications (like email, CRM, HR systems) responds from different offices around the world, so we know which app is causing problems and can talk to the vendor with real data.*

---

## Description

Compares response times across critical SaaS applications from multiple geographic vantage points. Identifies which SaaS applications are performing well and which are slow from specific locations — enabling data-driven discussions with SaaS vendors about SLA compliance and regional performance disparities.

## Value

Organizations typically depend on 10–30 SaaS applications. When "everything is slow," the help desk needs to know WHICH application is slow and from WHERE. This UC provides the answer: if Salesforce is fast from New York but slow from Singapore, the issue is either the network path from Singapore or Salesforce's infrastructure in the APAC region. This data is also critical for SaaS vendor management — providing evidence for SLA discussions when a vendor's performance doesn't meet contracted levels.

## Implementation

Create HTTP Server tests for each critical SaaS application endpoint from multiple agent locations. Name tests consistently (e.g., "SaaS-Salesforce-Login", "SaaS-O365-Outlook").

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **HTTP Server tests configured for each critical SaaS application.** Navigate to **Cloud & Enterprise Agents → Test Settings → Add New Test → Web → HTTP Server** for each SaaS endpoint. Naming convention is critical for this UC: use `SaaS-<AppName>-<Endpoint>` (e.g., `SaaS-O365-Outlook`, `SaaS-Salesforce-Login`, `SaaS-ServiceNow-API`). This enables SPL to filter and group SaaS tests easily.
  - **Target URLs:** Use specific SaaS endpoints, not just the landing page. Examples:
    - Microsoft 365: `https://outlook.office365.com/owa/` (webmail), `https://login.microsoftonline.com/` (auth), `https://<tenant>.sharepoint.com/_api/web` (SharePoint API).
    - Salesforce: `https://login.salesforce.com/`, `https://<instance>.salesforce.com/services/data/v58.0/` (API).
    - ServiceNow: `https://<instance>.service-now.com/api/now/table/incident` (API).
    - Google Workspace: `https://mail.google.com/`, `https://drive.google.com/`.
  - **Agents:** Use Cloud Agents from regions where your users are located. Enterprise Agents test the path from your network (through SASE/proxy if applicable).
  - **Interval:** 5 minutes per SaaS test. Many SaaS providers rate-limit or flag frequent automated requests — 1-minute intervals may trigger blocking.
- **SaaS vendor status page URLs documented.** For each monitored SaaS app, bookmark the vendor's status page: status.office365.com, status.salesforce.com, status.service-now.com, etc. When ThousandEyes shows degradation, check the vendor status page for known issues.
- **Splunk role:** `srchIndexesAllowed` must include `thousandeyes_metrics`.

### Step 1 — Configure data collection
SaaS-targeted HTTP Server test metrics flow through the same Tests Stream — Metrics OTel input configured in UC-5.9.1. No separate input is needed.

Verify SaaS test data is present:
```spl
index=thousandeyes_metrics sourcetype="cisco:thousandeyes:metric" thousandeyes.test.type="http-server" (thousandeyes.test.name="*SaaS*" OR thousandeyes.test.name="*O365*" OR thousandeyes.test.name="*Salesforce*" OR thousandeyes.test.name="*ServiceNow*") earliest=-1h
| stats count dc(thousandeyes.source.agent.name) as agents by thousandeyes.test.name
| sort thousandeyes.test.name
```
Each SaaS test should show data from all assigned agents.

**SaaS monitoring vs general HTTP monitoring — key differences:**
- You do NOT control the server. Performance issues require vendor engagement, not internal remediation.
- SaaS endpoints frequently use CDNs, Anycast DNS, and geo-distributed infrastructure. Performance varies by agent location.
- SaaS vendors may throttle or block automated testing. Monitor for HTTP 429 (Too Many Requests) or HTTP 403 (Forbidden) responses.
- SaaS SLAs typically guarantee 99.9% availability but rarely specify performance thresholds. ThousandEyes data provides the performance evidence you need for SLA discussions.

### Step 2 — Create the search and alert
**SaaS response time per region (primary view):**
```spl
`stream_index` thousandeyes.test.type="http-server" (thousandeyes.test.name="*O365*" OR thousandeyes.test.name="*Salesforce*" OR thousandeyes.test.name="*ServiceNow*" OR thousandeyes.test.name="*SaaS*")
| stats avg(http.client.request.duration) as avg_ttfb avg(http.server.request.availability) as avg_avail by thousandeyes.test.name, thousandeyes.source.agent.location
| eval avg_ttfb_ms=round(avg_ttfb*1000,1)
| sort thousandeyes.test.name, -avg_ttfb_ms
```

**Understanding this SPL**

The test name filter `*O365*" OR *Salesforce*" OR *SaaS*"` selects all SaaS-related tests based on naming convention. If you use a different naming scheme, adjust accordingly (or use ThousandEyes tags).

`avg(http.client.request.duration) as avg_ttfb` — Time to First Byte for the SaaS endpoint. This measures how fast the SaaS vendor responds from each agent's location. Units: seconds (OTel v2). Multiply by 1000 for ms.

`avg(http.server.request.availability) as avg_avail` — availability percentage. 100% means the SaaS endpoint responded successfully every round.

`by thousandeyes.source.agent.location` — splits by agent geographic location. This reveals whether a SaaS app is slow globally (vendor issue) or only from specific regions (routing/CDN issue).

**Normalized comparison (all SaaS apps side by side):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="SaaS-*" earliest=-24h
| rex field=thousandeyes.test.name "SaaS-(?<saas_app>[^-]+)"
| stats avg(http.client.request.duration) as avg_ttfb avg(http.server.request.availability) as avg_avail by saas_app
| eval avg_ttfb_ms=round(avg_ttfb*1000,1), avg_avail_pct=round(avg_avail,2)
| sort avg_ttfb_ms
```
This extracts the SaaS app name from the test name and provides a single row per app. Useful for executive dashboards: "Which SaaS is slowest right now?"

**SaaS vendor SLA tracking (monthly availability calculation):**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="SaaS-*" earliest=-30d
| rex field=thousandeyes.test.name "SaaS-(?<saas_app>[^-]+)"
| stats avg(http.server.request.availability) as monthly_availability count as total_measurements by saas_app
| eval downtime_min=round((100-monthly_availability)/100 * 30 * 24 * 60, 0)
| eval sla_met=if(monthly_availability >= 99.9, "Yes", "No")
| table saas_app, monthly_availability, downtime_min, sla_met, total_measurements
```

**SaaS performance trending:**
```spl
`stream_index` thousandeyes.test.type="http-server" thousandeyes.test.name="SaaS-*" earliest=-7d
| rex field=thousandeyes.test.name "SaaS-(?<saas_app>[^-]+)"
| timechart span=4h avg(http.client.request.duration) as avg_ttfb_s by saas_app
```

**Scheduling:** cron `*/15 * * * *`, time range `-30m to now`. Alert on availability < 100% or TTFB > 2 seconds. Throttle by `thousandeyes.test.name` for 2 hours.

### Step 3 — Validate
(a) **Manual browser comparison.** Open each SaaS application in your browser and note the perceived load time. Compare with ThousandEyes-reported TTFB. The browser experience includes rendering time (which TTFB doesn't), so the perceived load will be slower than TTFB.

(b) **Vendor status page cross-reference.** If ThousandEyes shows degradation, check the SaaS vendor's status page. If the vendor reports a known issue, ThousandEyes data confirms the impact on YOUR users (with specific latency and availability numbers per region).

(c) **Baseline establishment.** Run the normalized comparison over 7 days to establish per-SaaS baselines. SaaS response times vary by application: O365 Outlook may average 150 ms TTFB, while Salesforce API may average 400 ms. Set per-app thresholds based on actual baselines, not a one-size-fits-all value.

(d) **Rate limit check.** Verify your tests aren't being rate-limited: `| search http.response.status_code=429 | stats count by thousandeyes.test.name`. If any test shows 429 responses, reduce the test frequency or whitelist the agent IPs with the SaaS vendor.

(e) **Agent coverage.** Verify agents are deployed in all regions where you have SaaS users. A SaaS app may perform well from US agents but poorly from APAC agents due to routing to a distant data center.

### Step 4 — Operationalize
**Dashboard** ("SaaS Application Health" — designed for IT operations / service desk):
- Row 1 — Scoreboard: one tile per SaaS app showing availability % and TTFB. Green = available and fast, yellow = available but slow, red = failures. This is the "weather report" for your SaaS portfolio.
- Row 2 — Per-region comparison: for each SaaS app, show TTFB per agent location. Heatmap format: rows = SaaS apps, columns = regions, cells = TTFB colour-coded.
- Row 3 — Trending: SaaS TTFB over 7 days at 4-hour granularity. Shows temporal patterns (business-hours congestion, weekend maintenance windows).
- Row 4 — Monthly SLA table: SaaS app | monthly availability | downtime minutes | SLA met (Yes/No). Use for monthly vendor review meetings.

**Alerting:**
- Availability < 100% for ANY SaaS app → low-urgency Slack notification to `#it-ops`. Include app name, affected regions, and vendor status page URL.
- Availability < 100% from ALL agents for a SaaS app → high-urgency notification. The SaaS app is globally down. Post to internal status page.
- TTFB > 2× baseline → low-urgency notification. The SaaS app is significantly slower than normal.

**Runbook** (owner: IT operations / vendor management):
1. **SaaS app slow from all locations.** Vendor issue. (a) Check vendor status page. (b) File a support ticket with ThousandEyes evidence: include TTFB values, affected regions, and timeline. (c) Post to internal status page: "[SaaS app] experiencing degraded performance. Vendor notified. ETA: [pending vendor response]."
2. **SaaS app slow from specific locations.** Routing issue. (a) Check if the SaaS vendor uses Anycast DNS — the slow agents may be routed to a distant data center. (b) Check if agents go through SASE/proxy (UC-5.9.30) — the proxy may be adding latency. (c) Check DNS resolution at the slow agents — they may resolve to a different SaaS endpoint.
3. **SaaS app availability < 100%.** (a) Check `error.type` for the cause (timeout, connection_refused, ssl_error). (b) If HTTP 403 → the SaaS vendor may be blocking ThousandEyes agents. Contact vendor to whitelist. (c) If timeout → the SaaS endpoint may be overloaded or the network path is broken.
4. **Monthly SLA review.** Use the monthly SLA table in the dashboard. For any SaaS app with availability < 99.9%, prepare an SLA credit request with ThousandEyes evidence. Include: availability %, downtime minutes, affected time windows, and sample ThousandEyes permalinks.

### Step 5 — Troubleshooting

- **SaaS tests always show 0% availability** — The SaaS vendor may be blocking ThousandEyes agent IPs. Check `error.type` for 403/429 responses. Contact the SaaS vendor to whitelist ThousandEyes IP ranges.

- **TTFB seems unrealistically low for a SaaS app (< 20 ms)** — The test may be hitting a CDN edge or DNS-level health check page that responds instantly. This doesn't reflect actual application performance. Target a URL that exercises the application (e.g., a login page or API endpoint), not just a static landing page.

- **SaaS vendor status page shows no issues but ThousandEyes shows degradation** — The vendor status page is often delayed or only reports major outages. Your ThousandEyes data may detect degradation before the vendor acknowledges it. File a support ticket with evidence.

- **All common troubleshooting** — See UC-5.9.34 Step 5 for HTTP test issues, and UC-5.9.1 Step 5 for general app troubleshooting.

## SPL

```spl
`stream_index` thousandeyes.test.type="http-server" (thousandeyes.test.name="*O365*" OR thousandeyes.test.name="*Salesforce*" OR thousandeyes.test.name="*ServiceNow*" OR thousandeyes.test.name="*SaaS*")
| stats avg(http.client.request.duration) as avg_ttfb avg(http.server.request.availability) as avg_avail by thousandeyes.test.name, thousandeyes.source.agent.location
| eval avg_ttfb_ms=round(avg_ttfb*1000,1)
| sort thousandeyes.test.name, -avg_ttfb_ms
```

## Visualization

(1) Heatmap: SaaS application × agent location, colour by TTFB. (2) Bar chart: TTFB per SaaS application. (3) Table: SaaS comparison with availability and TTFB. (4) Timechart: SaaS response time trending.

## Known False Positives

**SaaS vendor scheduled maintenance.** SaaS providers perform maintenance that may increase response times. Check vendor status pages.

**Login/auth endpoints vs app endpoints.** SaaS login pages may respond differently than authenticated application pages. Ensure tests target representative endpoints.

**Test URL changes.** SaaS vendors may change endpoint URLs. Update tests when SaaS providers announce URL changes.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [ThousandEyes SaaS monitoring](https://www.thousandeyes.com/solutions/saas-monitoring)
