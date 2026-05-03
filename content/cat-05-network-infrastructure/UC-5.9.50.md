<!-- AUTO-GENERATED from UC-5.9.50.json — DO NOT EDIT -->

---
id: "5.9.50"
title: "ThousandEyes ITSI Service Health"
status: "verified"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.9.50 · ThousandEyes ITSI Service Health

> **Criticality:** High &middot; **Difficulty:** Advanced &middot; **Pillar:** Observability &middot; **Type:** Performance, Availability &middot; **Wave:** Run &middot; **Status:** Verified

*We plug our network monitoring data into a bigger system that shows the health of entire business services — so instead of seeing 50 separate network metrics, the team sees one health score for 'Customer Portal' that combines network, application, and server health into a single view.*

---

## Description

Integrates ThousandEyes network performance metrics into Splunk ITSI services and KPIs, providing a service-level health view that aggregates individual ThousandEyes test results into business-meaningful service health scores. This enables ThousandEyes data to participate in ITSI's service dependency trees, glass tables, and episode analytics.

## Value

ITSI provides service-level monitoring that individual ThousandEyes tests cannot. A service like "Customer Portal" depends on: network connectivity (ThousandEyes), application health (APM), server health (infrastructure monitoring), and database performance (DB monitoring). By feeding ThousandEyes data into ITSI, the network health component appears alongside all other health indicators in a unified service health score. When the "Customer Portal" health score drops, ITSI can immediately show that the network component (from ThousandEyes) is the degraded contributor — enabling faster root cause identification.

## Implementation

The `ta_cisco_thousandeyes` app includes ITSI integration content. Configure ITSI services with ThousandEyes KPIs using the built-in KPI base searches. Map ThousandEyes tests to ITSI services based on business context.

## Detailed Implementation

### Prerequisites
- All common prerequisites from UC-5.9.1 apply (app installed, OAuth authenticated, HEC configured, Tests Stream — Metrics input enabled).
- **Splunk ITSI installed and licensed.** ITSI (IT Service Intelligence) is a premium Splunk product, licensed separately. Version 4.17+ is recommended for full OTel metric compatibility. Install from Splunkbase: [ITSI (Splunkbase 1841)](https://splunkbase.splunk.com/app/1841).
- **ITSI fundamentals understood.** Key ITSI concepts for this UC:
  - **Service:** A logical grouping representing a business application (e.g., "Customer Portal"). Each service has a health score derived from its KPIs.
  - **KPI (Key Performance Indicator):** A metric that contributes to the service's health score. Each KPI has a base search, thresholds, and a weight.
  - **Entity:** A real-world object that a service depends on (server, test, agent). Entities are used to filter KPI base searches so each service only includes relevant data.
  - **Glass Table:** A visual representation of services with real-time health indicators on a custom background (topology diagram, floor plan, etc.).
  - **Episode Analytics:** ITSI's correlation engine that groups related alerts into episodes for faster triage.
- **ThousandEyes ITSI content pack (optional).** The `ta_cisco_thousandeyes` may include optional ITSI content (KPI base searches, service templates). Check **ITSI → Configuration → Content Packs → Imported** for ThousandEyes content. If available, it provides pre-built KPI templates. If not available, this UC guides you through manual KPI creation.
- **Service model designed.** Before configuring ITSI, map your business services to ThousandEyes tests:
  - "Customer Portal" → HTTP Server test (UC-5.9.34), Page Load test (UC-5.9.37), Agent-to-Server test (UC-5.9.1), DNS test (UC-5.9.5).
  - "Internal ERP" → HTTP Server test, Agent-to-Server test.
  - Each business service should include ThousandEyes KPIs AND application/infrastructure KPIs (from APM, server monitoring, etc.) for a complete health picture.
- **Splunk role:** `itoa_admin` or `itoa_user` role for ITSI administration.

### Step 1 — Configure ITSI integration
**1a. Create ITSI entities from ThousandEyes tests.**
ITSI entities represent the individual components being monitored. For ThousandEyes, each test is an entity.

Navigate to **ITSI → Configuration → Entity Management → Create Entity** (or use CSV import for bulk):
- **Entity title:** Use the ThousandEyes test name (e.g., `SaaS-O365-Outlook`).
- **Entity key fields:** `thousandeyes.test.name` = the test name.
- **Entity informational fields:** Add `thousandeyes.test.type`, `server.address`, and any other relevant attributes.
- **Entity aliases:** Map `host` → `thousandeyes.test.name` so ITSI can match KPI data to entities.

For bulk entity creation, export a CSV from ThousandEyes test settings and import via **ITSI → Configuration → Entity Management → Import from Search**:
```spl
`stream_index` earliest=-1h
| stats dc(thousandeyes.source.agent.name) as agents by thousandeyes.test.name, thousandeyes.test.type, server.address
| rename thousandeyes.test.name as title, thousandeyes.test.type as test_type, server.address as target
| eval host=title
```

**1b. Create ITSI services.**
Navigate to **ITSI → Configuration → Services → Create New Service**:
- **Service name:** The business application name (e.g., "Customer Portal").
- **Service description:** Brief description of what this service represents.
- **Entity rules:** Filter entities to include only ThousandEyes tests relevant to this service. Example: `thousandeyes.test.name matches "*CustomerPortal*"`.

**1c. Add KPIs to each service.**
Each KPI uses a base search to retrieve ThousandEyes metric data and thresholds to determine health.

**Network Latency KPI:**
- Base search:
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_latency by thousandeyes.test.name
| eval avg_latency_ms=round(avg_latency*1000,1)
```
- KPI metric: `avg_latency_ms`
- Entity split field: `thousandeyes.test.name`
- Thresholds (adaptive or static):
  - Normal: < 50 ms. The network path is healthy.
  - Low: < 100 ms. Slightly elevated but acceptable.
  - Medium: < 200 ms. Noticeable degradation for interactive applications.
  - High: < 500 ms. Significant degradation. Real-time applications (VoIP, video) will be impacted.
  - Critical: ≥ 500 ms. Network path is severely degraded.
- Search frequency: 5 minutes.
- Calculation window: 15 minutes.

**HTTP Availability KPI:**
- Base search:
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_avail by thousandeyes.test.name
```
- KPI metric: `avg_avail`
- Thresholds:
  - Normal: > 99.9%. Fully available.
  - Low: > 99%. Minor availability dips.
  - Medium: > 95%. Noticeable unavailability.
  - High: > 90%. Significant outage.
  - Critical: ≤ 90%. Major outage.

**HTTP Response Time (TTFB) KPI:**
- Base search:
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.client.request.duration) as avg_ttfb by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb*1000,1)
```
- KPI metric: `avg_ttfb_ms`
- Thresholds: Normal < 300 ms, Low < 500 ms, Medium < 1000 ms, High < 3000 ms, Critical ≥ 3000 ms.

**Page Load Duration KPI (for Page Load tests):**
- Base search:
```spl
`stream_index` thousandeyes.test.type="page-load"
| stats avg(web.page_load.duration) as avg_load by thousandeyes.test.name
| eval avg_load_s=round(avg_load,2)
```
- KPI metric: `avg_load_s`
- Thresholds: Normal < 3 s, Low < 5 s, Medium < 8 s, High < 15 s, Critical ≥ 15 s.

**DNS Resolution KPI (for DNS tests):**
- Base search:
```spl
`stream_index` thousandeyes.test.type="dns-server"
| stats avg(dns.lookup.duration) as avg_dns by thousandeyes.test.name
| eval avg_dns_ms=round(avg_dns*1000,1)
```
- KPI metric: `avg_dns_ms`
- Thresholds: Normal < 50 ms, Low < 100 ms, Medium < 200 ms, High < 500 ms, Critical ≥ 500 ms.

**1d. Configure KPI weighting.**
Set the relative importance of each KPI to the overall service health score:
- HTTP Availability: weight 40% (availability is the most important indicator).
- HTTP TTFB: weight 25%.
- Network Latency: weight 20%.
- Page Load Duration: weight 10%.
- DNS Resolution: weight 5%.
Adjust based on your service's characteristics. An API-only service may not need Page Load Duration.

### Step 2 — Create KPI base searches
The KPI base searches above are created within ITSI's KPI configuration UI. You can also create standalone KPI base searches for reuse across multiple services.

Navigate to **ITSI → Configuration → KPI Base Searches → Create New KPI Base Search**:

**ThousandEyes Network Health (reusable base search):**
```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.test.name
| eval avg_latency_ms=round(avg_latency*1000,1), avg_loss_pct=round(avg_loss,2), avg_jitter_ms=round(avg_jitter,1)
```
This single base search provides three metrics (latency, loss, jitter) that can be used by three separate KPIs, running only one search instead of three.

**ThousandEyes HTTP Health (reusable base search):**
```spl
`stream_index` thousandeyes.test.type="http-server"
| stats avg(http.server.request.availability) as avg_avail avg(http.client.request.duration) as avg_ttfb avg(http.server.throughput) as avg_throughput by thousandeyes.test.name
| eval avg_ttfb_ms=round(avg_ttfb*1000,1), avg_throughput_mbps=round(avg_throughput*8/1000000,2)
```

### Step 3 — Validate
(a) **Verify ITSI services show health scores.** Navigate to **ITSI → Service Analyzer**. Each ThousandEyes-fed service should show a health score (green/yellow/red). If a service shows gray (N/A), the KPI base searches aren't returning data.

(b) **Trigger a test alert.** Temporarily lower a KPI threshold to below the current value (e.g., set Network Latency critical threshold to 1 ms). Verify the service health score drops to critical. Reset the threshold after validation.

(c) **Verify entity mapping.** Go to **ITSI → Configuration → Entity Management**. Each entity should show recent KPI data. If entities show no data, the entity key field doesn't match the KPI base search output fields.

(d) **Verify KPI data flow.** For each KPI, click into the KPI detail view. The sparkline should show recent data points. If the sparkline is flat or empty, the base search frequency or calculation window may be misconfigured.

(e) **Cross-reference with raw ThousandEyes data.** Compare ITSI KPI values with raw Splunk searches (e.g., UC-5.9.1 SPL). The values should match within rounding differences.

### Step 4 — Operationalize
**Glass Tables** (the primary visual for executive and NOC audiences):
Build ITSI Glass Tables that show your service topology with ThousandEyes health integrated:
- Upload a network topology diagram or architecture diagram as the Glass Table background.
- Place service health indicators on each business application.
- Add KPI widgets showing ThousandEyes network latency, availability, and response time adjacent to each service.
- Link to drilldown dashboards for each ThousandEyes UC.

Example Glass Table layout:
- Center: Business application services (Customer Portal, ERP, Email) with health score icons.
- Left: Network infrastructure (ISP, WAN, SASE) with ThousandEyes latency/loss KPIs.
- Right: Cloud infrastructure (AWS, Azure, GCP) with ThousandEyes cross-cloud KPIs.
- Bottom: Global map with regional health scores.

**Episode Analytics** (automated incident correlation):
Configure ITSI to group ThousandEyes-related notable events with application events:
- Create a correlation search that fires when ThousandEyes KPI health drops to High or Critical.
- Configure episode rules to group ThousandEyes notable events with application notable events that occur within 5 minutes of each other and affect the same service.
- This enables automatic correlation: "Customer Portal latency increased" + "Customer Portal error rate increased" = single episode, not two separate alerts.

**Service dependency tree:**
Model dependencies between services. Example:
- "Customer Portal" depends on "Network (Site A to Cloud)", "DNS (public)", "CDN (Cloudflare)".
- If "Network (Site A to Cloud)" degrades, "Customer Portal" health automatically reflects the dependency impact.

**Runbook** (owner: NOC / SRE team):
1. **ITSI service health drops — ThousandEyes KPI is the contributor.** (a) Identify which ThousandEyes KPI is degraded (latency? availability? response time?). (b) Drill into the specific UC for that metric: UC-5.9.1 for latency, UC-5.9.34 for HTTP availability, UC-5.9.35 for TTFB, UC-5.9.38 for page load. (c) Follow that UC's runbook.
2. **ITSI service health drops — ThousandEyes KPIs are all healthy.** The issue is NOT in the network or external connectivity. Investigate application components: APM traces, server CPU/memory, database performance.
3. **Multiple services affected simultaneously.** Likely a shared infrastructure issue: (a) Check shared network paths (UC-5.9.9). (b) Check DNS (UC-5.9.5). (c) Check ISP (UC-5.9.11). A shared dependency degradation will cause correlated health drops.
4. **ITSI KPIs showing N/A.** (a) The KPI base search isn't returning data. Copy the base search to the Splunk search bar and run manually. (b) Check that the ThousandEyes data pipeline is healthy (UC-5.9.49). (c) Verify ITSI entity mapping matches the data.

### Step 5 — Troubleshooting

- **KPIs show N/A (no health score)** — Most common issue. Causes: (a) KPI base search returns 0 results — verify the SPL runs successfully in the search bar. (b) Entity split field doesn't match — the `by` field in the base search must match the entity key field exactly. (c) Calculation window is too short — if the base search window is 5 minutes but ThousandEyes tests run every 10 minutes, some intervals will have no data. Increase the window to 2× the test interval.

- **Entity mapping not working** — ITSI matches entities to KPI data using entity alias fields. Ensure the entity's `host` alias maps to the field produced by the KPI base search (typically `thousandeyes.test.name`). Check: **Entity → Aliases → host** should equal the ThousandEyes test name exactly (case-sensitive).

- **KPI data stale (sparkline stops updating)** — (a) Increase KPI base search frequency to match or exceed ThousandEyes test frequency. If tests run every 2 minutes, the KPI search should run at least every 5 minutes. (b) Check ITSI search head performance — overloaded search heads skip KPI searches.

- **Health score doesn't reflect reality (always green or always red)** — (a) Thresholds may be misconfigured. Review each KPI's threshold values. (b) KPI weighting may be skewed — one KPI with 90% weight dominates. (c) Use adaptive thresholds instead of static for more accurate health scoring.

- **Glass Table not updating** — Glass Tables refresh on a timer. Set refresh to 60 seconds for real-time monitoring. Also verify that the user's role has permission to view the ITSI services linked to the Glass Table.

- **All common troubleshooting** — See UC-5.9.1 Step 5 for general app troubleshooting. For ITSI-specific issues, see ITSI documentation: **Configuration → Troubleshooting**.

## SPL

```spl
`stream_index` thousandeyes.test.type="agent-to-server"
| stats avg(network.latency) as avg_latency avg(network.loss) as avg_loss avg(network.jitter) as avg_jitter by thousandeyes.test.name
| eval avg_latency_ms=round(avg_latency*1000,1)
| eval health=case(avg_latency_ms<50 AND avg_loss<0.5, "Normal", avg_latency_ms<100 AND avg_loss<1, "Warning", 1=1, "Critical")
| table thousandeyes.test.name, avg_latency_ms, avg_loss, avg_jitter, health
```

## Visualization

(1) ITSI Glass Table: service health with ThousandEyes network KPIs. (2) ITSI Service Analyzer: deep-dive into ThousandEyes-fed KPIs. (3) ITSI Notable Events: ThousandEyes-triggered notable events correlated with other data sources.

## Known False Positives

**ITSI threshold misconfiguration.** If ITSI KPI thresholds are set too aggressively, ThousandEyes-fed KPIs may show "Critical" for normal network fluctuations. Use ITSI's adaptive thresholding or calibrate thresholds based on UC-5.9.1 baseline data.

**KPI data lag.** If the KPI base search schedule doesn't align with ThousandEyes data arrival, KPIs may show stale data. Ensure KPI search frequency matches or exceeds test frequency.

**Entity mapping issues.** If ITSI entities don't correctly map to ThousandEyes agents or tests, KPI calculations may include or exclude wrong data.

## References

- [Cisco ThousandEyes App for Splunk (Splunkbase 7719)](https://splunkbase.splunk.com/app/7719)
- [Splunk ITSI documentation](https://docs.splunk.com/Documentation/ITSI)
- [ThousandEyes ITSI integration guide](https://docs.thousandeyes.com/product-documentation/integration-guides/custom-built-integrations/splunk-app)
