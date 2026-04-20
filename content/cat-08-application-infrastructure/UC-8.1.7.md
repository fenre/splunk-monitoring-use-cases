---
id: "8.1.7"
title: "Bot and Crawler Detection"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.7 · Bot and Crawler Detection

## Description

Bot traffic inflates metrics and consumes resources. Identification enables accurate capacity planning and bot management policies.

## Value

Bot traffic inflates metrics and consumes resources. Identification enables accurate capacity planning and bot management policies.

## Implementation

Parse User-Agent from access logs. Maintain a lookup of known bot signatures. Classify traffic as bot vs human. Track bot traffic percentage over time. Alert on unknown bots or suspicious crawling patterns.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_apache`, `TA-nginx`.
• Ensure the following data sources are available: Access logs (User-Agent field).
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse User-Agent from access logs. Maintain a lookup of known bot signatures. Classify traffic as bot vs human. Track bot traffic percentage over time. Alert on unknown bots or suspicious crawling patterns.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="access_combined"
| rex field=useragent "(?<bot_name>Googlebot|Bingbot|baiduspider|bot|crawler|spider)"
| eval is_bot=if(isnotnull(bot_name),"bot","human")
| stats count by is_bot
| eval pct=round(count/sum(count)*100,1)
```

Understanding this SPL

**Bot and Crawler Detection** — Bot traffic inflates metrics and consumes resources. Identification enables accurate capacity planning and bot management policies.

Documented **Data sources**: Access logs (User-Agent field). **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: access_combined. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="access_combined". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Extracts fields with `rex` (regular expression).
• `eval` defines or adjusts **is_bot** — often to normalize units, derive a ratio, or prepare for thresholds.
• `stats` rolls up events into metrics; results are split **by is_bot** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• `eval` defines or adjusts **pct** — often to normalize units, derive a ratio, or prepare for thresholds.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.http_user_agent Web.src span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

**Bot and Crawler Detection** — Bot traffic inflates metrics and consumes resources. Identification enables accurate capacity planning and bot management policies.

Documented **Data sources**: Access logs (User-Agent field). **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Pie chart (bot vs human traffic), Bar chart (top bots by request count), Line chart (bot traffic trend).

## SPL

```spl
index=web sourcetype="access_combined"
| rex field=useragent "(?<bot_name>Googlebot|Bingbot|baiduspider|bot|crawler|spider)"
| eval is_bot=if(isnotnull(bot_name),"bot","human")
| stats count by is_bot
| eval pct=round(count/sum(count)*100,1)
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.http_user_agent Web.src span=1h
| sort -count
```

## Visualization

Pie chart (bot vs human traffic), Bar chart (top bots by request count), Line chart (bot traffic trend).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
