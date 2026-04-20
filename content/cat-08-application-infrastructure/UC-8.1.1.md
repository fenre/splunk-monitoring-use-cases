---
id: "8.1.1"
title: "HTTP Error Rate Monitoring"
criticality: "critical"
splunkPillar: "Security"
---

# UC-8.1.1 · HTTP Error Rate Monitoring

## Description

Rising error rates signal application issues, backend failures, or attacks. Rapid detection reduces user impact and MTTR.

## Value

Rising error rates signal application issues, backend failures, or attacks. Rapid detection reduces user impact and MTTR.

## Implementation

Install appropriate web server TA. Forward access logs via UF. Enable response time logging in web server config. Create tiered alerts: >5% error rate (warning), >10% (critical). Split 4xx from 5xx for different response.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_apache`, `TA-nginx`, IIS via Windows TA.
• Ensure the following data sources are available: Web server access logs (Apache combined, NGINX combined, IIS W3C).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Install appropriate web server TA. Forward access logs via UF. Enable response time logging in web server config. Create tiered alerts: >5% error rate (warning), >10% (critical). Split 4xx from 5xx for different response.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="access_combined"
| eval error=if(status>=400,1,0)
| timechart span=5m sum(error) as errors, count as total
| eval error_rate=round(errors/total*100,2)
| where error_rate > 5
```

Understanding this SPL

**HTTP Error Rate Monitoring** — Rising error rates signal application issues, backend failures, or attacks. Rapid detection reduces user impact and MTTR.

Documented **Data sources**: Web server access logs (Apache combined, NGINX combined, IIS W3C). **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`, IIS via Windows TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: access_combined. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="access_combined". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `eval` defines or adjusts **error** — often to normalize units, derive a ratio, or prepare for thresholds.
• `timechart` plots the metric over time using **span=5m** buckets — ideal for trending and alerting on this use case.
• `eval` defines or adjusts **error_rate** — often to normalize units, derive a ratio, or prepare for thresholds.
• Filters the current rows with `where error_rate > 5` — typically the threshold or rule expression for this monitoring goal.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```

Understanding this CIM / accelerated SPL

**HTTP Error Rate Monitoring** — Rising error rates signal application issues, backend failures, or attacks. Rapid detection reduces user impact and MTTR.

Documented **Data sources**: Web server access logs (Apache combined, NGINX combined, IIS W3C). **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`, IIS via Windows TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Timechart (line) for 5xx rate % and a second series for 4xx rate % to show trends; stacked column for 4xx vs 5xx counts when triaging the class mix; single-value panel for current 5xx % (the SLA-facing metric); horizontal bar chart for top URIs by 5xx count to guide developer investigation.

## SPL

```spl
index=web sourcetype="access_combined"
| eval error=if(status>=400,1,0)
| timechart span=5m sum(error) as errors, count as total
| eval error_rate=round(errors/total*100,2)
| where error_rate > 5
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```

## Visualization

Timechart (line) for 5xx rate % and a second series for 4xx rate % to show trends; stacked column for 4xx vs 5xx counts when triaging the class mix; single-value panel for current 5xx % (the SLA-facing metric); horizontal bar chart for top URIs by 5xx count to guide developer investigation.

## Known False Positives

Client errors (4xx) from bots or invalid requests; consider separate thresholds for 4xx vs 5xx.

## References

- [Splunk Add-on for Apache](https://splunkbase.splunk.com/app/3186)
- [Splunk Add-on for NGINX](https://splunkbase.splunk.com/app/3258)
- [Web CIM](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
