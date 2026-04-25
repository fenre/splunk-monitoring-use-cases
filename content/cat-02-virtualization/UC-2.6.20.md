<!-- AUTO-GENERATED from UC-2.6.20.json — DO NOT EDIT -->

---
id: "2.6.20"
title: "Browser Performance per Web Application"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-2.6.20 · Browser Performance per Web Application

## Description

Many Citrix-delivered workloads are browser-based (SaaS applications, internal portals). uberAgent's browser extensions measure page load time, network latency, and rendering performance per website/URL. This reveals whether slow web application performance is due to the Citrix session, the network, or the web application itself — a critical distinction for troubleshooting.

## Value

Many Citrix-delivered workloads are browser-based (SaaS applications, internal portals). uberAgent's browser extensions measure page load time, network latency, and rendering performance per website/URL. This reveals whether slow web application performance is due to the Citrix session, the network, or the web application itself — a critical distinction for troubleshooting.

## Implementation

Deploy the uberAgent browser extension via Group Policy or Citrix Studio. The extension collects W3C Navigation Timing API data per page load. Alert when key internal web applications (intranet, CRM, EHR) exceed acceptable page load thresholds. Segment by Citrix delivery group vs physical endpoint to compare performance.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: uberAgent UXM (Splunkbase 1448) + browser extension (Chrome, Edge, Firefox).
• Ensure the following data sources are available: `sourcetype="uberAgent:Application:BrowserWebRequests2"`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Deploy the uberAgent browser extension via Group Policy or Citrix Studio. The extension collects W3C Navigation Timing API data per page load. Alert when key internal web applications (intranet, CRM, EHR) exceed acceptable page load thresholds. Segment by Citrix delivery group vs physical endpoint to compare performance.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=uberagent sourcetype="uberAgent:Application:BrowserWebRequests2" earliest=-24h
| stats avg(PageLoadTotalDurationMs) as avg_load_ms perc95(PageLoadTotalDurationMs) as p95_load_ms count as page_loads dc(User) as users by Host
| eval avg_load_sec=round(avg_load_ms/1000,1), p95_load_sec=round(p95_load_ms/1000,1)
| where p95_load_sec > 5
| sort -p95_load_sec
| table Host, page_loads, users, avg_load_sec, p95_load_sec
```

Understanding this SPL

**Browser Performance per Web Application** — Many Citrix-delivered workloads are browser-based (SaaS applications, internal portals). uberAgent's browser extensions measure page load time, network latency, and rendering performance per website/URL. This reveals whether slow web application performance is due to the Citrix session, the network, or the web application itself — a critical distinction for troubleshooting.

Documented **Data sources**: `sourcetype="uberAgent:Application:BrowserWebRequests2"`. **App/TA** (typical add-on context): uberAgent UXM (Splunkbase 1448) + browser extension (Chrome, Edge, Firefox). The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: uberagent; **sourcetype**: uberAgent:Application:BrowserWebRequests2. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=uberagent, sourcetype="uberAgent:Application:BrowserWebRequests2", time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by Host** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **avg_load_sec** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where p95_load_sec > 5` — typically the threshold or rule expression for this monitoring goal.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Browser Performance per Web Application**): table Host, page_loads, users, avg_load_sec, p95_load_sec

Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (slowest websites), Line chart (page load trending), Bar chart (comparison by browser).

## SPL

```spl
index=uberagent sourcetype="uberAgent:Application:BrowserWebRequests2" earliest=-24h
| stats avg(PageLoadTotalDurationMs) as avg_load_ms perc95(PageLoadTotalDurationMs) as p95_load_ms count as page_loads dc(User) as users by Host
| eval avg_load_sec=round(avg_load_ms/1000,1), p95_load_sec=round(p95_load_ms/1000,1)
| where p95_load_sec > 5
| sort -p95_load_sec
| table Host, page_loads, users, avg_load_sec, p95_load_sec
```

## Visualization

Table (slowest websites), Line chart (page load trending), Bar chart (comparison by browser).

## References

- [uberAgent UXM](https://splunkbase.splunk.com/app/1448)
