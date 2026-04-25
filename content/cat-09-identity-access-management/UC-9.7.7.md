<!-- AUTO-GENERATED from UC-9.7.7.json — DO NOT EDIT -->

---
id: "9.7.7"
title: "Identity Provider Availability Trending"
criticality: "high"
splunkPillar: "Security"
---

# UC-9.7.7 · Identity Provider Availability Trending

## Description

Identity provider outages block all applications that rely on them; weekly or monthly uptime trends show whether your vendor or network path is degrading over a quarter. That supports SLA discussions, architecture decisions, and communication to the business before users flood the service desk.

## Value

Identity provider outages block all applications that rely on them; weekly or monthly uptime trends show whether your vendor or network path is degrading over a quarter. That supports SLA discussions, architecture decisions, and communication to the business before users flood the service desk.

## Implementation

Point synthetic checks at the same endpoints your users hit for interactive login; run probes at least every few minutes from locations that match your user base. Tag each series with IdP name for clarity. Treat `weekly_uptime_pct` drops below your internal SLO as incidents even if vendor status pages are green. Combine with IdP `system` / `health` API logs if ingested for root-cause context.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: Splunk Synthetic Monitoring, Splunk Observability Cloud Synthetics, or custom `curl`-based scripted input; vendor status is optional enrichment only.
• Ensure the following data sources are available: `sourcetype=synthetics:url_probe` or `http:response` (fields `http_status`, `url`, `target_name`); map probes to IdP login URLs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Point synthetic checks at the same endpoints your users hit for interactive login; run probes at least every few minutes from locations that match your user base. Tag each series with IdP name for clarity. Treat `weekly_uptime_pct` drops below your internal SLO as incidents even if vendor status pages are green. Combine with IdP `system` / `health` API logs if ingested for root-cause context.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=synthetics sourcetype=synthetics:url_probe earliest=-90d@d url IN ("https://login.microsoftonline.com/","https://*.okta.com/oauth2/","https://accounts.google.com/")
| bin _time span=1d
| stats count(eval(http_status<500)) as successes, count as probes by _time, url
| eval daily_uptime_pct=round(100*successes/probes,3)
| bin _time span=7d aligntime=@w0
| stats avg(daily_uptime_pct) as weekly_uptime_pct by _time, url
| sort _time
| trendline sma4(weekly_uptime_pct) as uptime_sma
| predict weekly_uptime_pct as uptime_forecast algorithm=LLP future_timespan=4
```

Understanding this SPL

**Identity Provider Availability Trending** — Identity provider outages block all applications that rely on them; weekly or monthly uptime trends show whether your vendor or network path is degrading over a quarter. That supports SLA discussions, architecture decisions, and communication to the business before users flood the service desk.

Documented **Data sources**: `sourcetype=synthetics:url_probe` or `http:response` (fields `http_status`, `url`, `target_name`); map probes to IdP login URLs. **App/TA** (typical add-on context): Splunk Synthetic Monitoring, Splunk Observability Cloud Synthetics, or custom `curl`-based scripted input; vendor status is optional enrichment only. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: synthetics; **sourcetype**: synthetics:url_probe. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=synthetics, sourcetype=synthetics:url_probe, time bounds. Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, url** so each row reflects one combination of those dimensions.
• `eval` defines or adjusts **daily_uptime_pct** — often to normalize units, derive a ratio, or prepare for thresholds.
• Discretizes time or numeric ranges with `bin`/`bucket`.
• `stats` rolls up events into metrics; results are split **by _time, url** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Pipeline stage (see **Identity Provider Availability Trending**): trendline sma4(weekly_uptime_pct) as uptime_sma
• Pipeline stage (see **Identity Provider Availability Trending**): predict weekly_uptime_pct as uptime_forecast algorithm=LLP future_timespan=4


Step 3 — Validate
Compare Splunk results with the Okta admin console and System Log for the same users, outcomes, and time window, then adjust thresholds to normal org traffic.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Line chart of weekly_uptime_pct by IdP; SLA threshold band; optional forecast.

## SPL

```spl
index=synthetics sourcetype=synthetics:url_probe earliest=-90d@d url IN ("https://login.microsoftonline.com/","https://*.okta.com/oauth2/","https://accounts.google.com/")
| bin _time span=1d
| stats count(eval(http_status<500)) as successes, count as probes by _time, url
| eval daily_uptime_pct=round(100*successes/probes,3)
| bin _time span=7d aligntime=@w0
| stats avg(daily_uptime_pct) as weekly_uptime_pct by _time, url
| sort _time
| trendline sma4(weekly_uptime_pct) as uptime_sma
| predict weekly_uptime_pct as uptime_forecast algorithm=LLP future_timespan=4
```

## Visualization

Line chart of weekly_uptime_pct by IdP; SLA threshold band; optional forecast.

## References

- [Splunk Lantern — use case library](https://lantern.splunk.com/)
