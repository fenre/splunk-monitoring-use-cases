---
id: "8.1.4"
title: "Top Error URIs"
criticality: "medium"
splunkPillar: "Observability"
---

# UC-8.1.4 · Top Error URIs

## Description

Identifies the most problematic endpoints for targeted developer attention. Reduces noise by focusing on high-impact errors.

## Value

Identifies the most problematic endpoints for targeted developer attention. Reduces noise by focusing on high-impact errors.

## Implementation

Parse URI from access logs (ensure proper field extraction). Group by URI and status code. Create daily/weekly report of top error endpoints. Track error trends per URI over time to detect regressions.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: `Splunk_TA_apache`, `TA-nginx`.
• Ensure the following data sources are available: Access logs.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Parse URI from access logs (ensure proper field extraction). Group by URI and status code. Create daily/weekly report of top error endpoints. Track error trends per URI over time to detect regressions.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=web sourcetype="access_combined" status>=400
| stats count by uri_path, status
| sort -count
| head 20
```

Understanding this SPL

**Top Error URIs** — Identifies the most problematic endpoints for targeted developer attention. Reduces noise by focusing on high-impact errors.

Documented **Data sources**: Access logs. **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: web; **sourcetype**: access_combined. If that sourcetype is not mentioned in Data sources, double-check parsing or update the documentation to match the feed you actually ingest.

**Pipeline walkthrough**

• Scopes the data: index=web, sourcetype="access_combined". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• `stats` rolls up events into metrics; results are split **by uri_path, status** so each row reflects one combination of those dimensions (useful for per-host, per-user, or per-entity comparisons for this use case).
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.
• Limits the number of rows with `head`.

Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  where Web.status>=400
  by Web.src Web.uri_path Web.status span=5m
| sort -count
```

Understanding this CIM / accelerated SPL

**Top Error URIs** — Identifies the most problematic endpoints for targeted developer attention. Reduces noise by focusing on high-impact errors.

Documented **Data sources**: Access logs. **App/TA** (typical add-on context): `Splunk_TA_apache`, `TA-nginx`. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

This **CIM or accelerated** block uses normalized field names and/or `tstats` over data models. Enable **acceleration** on the referenced models (and correct CIM knowledge objects) or the search may return nothing.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for data model `Web.Web` — enable acceleration for that model.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.

Enable Data Model Acceleration (and metric indexes for `mstats`) for the models or datasets referenced above; otherwise `tstats`/`mstats` may return no results from summaries.


Step 3 — Validate
Confirm that events are present in the index and that the search returns expected results. Compare with known good/bad scenarios if applicable. Verify field extractions and index permissions.

Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Table (URI, status, count), Bar chart (top 20 error URIs), Treemap (errors by URI path).

## SPL

```spl
index=web sourcetype="access_combined" status>=400
| stats count by uri_path, status
| sort -count
| head 20
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

Table (URI, status, count), Bar chart (top 20 error URIs), Treemap (errors by URI path).

## References

- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
