<!-- AUTO-GENERATED from UC-5.3.10.json — DO NOT EDIT -->

---
id: "5.3.10"
title: "Backend Server Error Code Distribution (F5 BIG-IP)"
criticality: "high"
splunkPillar: "Observability"
---

# UC-5.3.10 · Backend Server Error Code Distribution (F5 BIG-IP)

## Description

Understanding which backends return 5xx errors helps isolate faulty application instances vs. systemic issues.

## Value

Understanding which backends return 5xx errors helps isolate faulty application instances vs. systemic issues.

## Implementation

Enable HTTP response logging on the LB. Track 5xx rates per backend member. Alert when a single member's error rate exceeds the pool average by 3x. Auto-disable unhealthy members.

## Detailed Implementation

Prerequisites
• Install and configure the required add-on or app: F5 TA (`Splunk_TA_f5-bigip`), NGINX TA.
• Ensure the following data sources are available: `sourcetype=f5:bigip:ltm:http`, `sourcetype=nginx:plus:api`.
• For app installation, inputs.conf, and Splunk directory layout, see the Implementation guide: docs/implementation-guide.md

Step 1 — Configure data collection
Enable HTTP response logging on the LB. Track 5xx rates per backend member. Alert when a single member's error rate exceeds the pool average by 3x. Auto-disable unhealthy members.

Step 2 — Create the search and alert
Run the following SPL in Search (then save as report or alert; adjust time range and threshold as needed):

```spl
index=network sourcetype="f5:bigip:ltm:http"
| where response_code >= 500
| stats count by pool_member, response_code, virtual_server
| sort -count
```

Understanding this SPL

**Backend Server Error Code Distribution (F5 BIG-IP)** — Understanding which backends return 5xx errors helps isolate faulty application instances vs. systemic issues.

Documented **Data sources**: `sourcetype=f5:bigip:ltm:http`, `sourcetype=nginx:plus:api`. **App/TA** (typical add-on context): F5 TA (`Splunk_TA_f5-bigip`), NGINX TA. The SPL below should target the same indexes and sourcetypes you configured for that feed—rename `index=` / `sourcetype=` if your deployment differs.

The first pipeline stage scopes events using **index**: network; **sourcetype**: f5:bigip:ltm:http. That sourcetype matches what this use case lists under Data sources.

**Pipeline walkthrough**

• Scopes the data: index=network, sourcetype="f5:bigip:ltm:http". Cross-check against **Data sources** above so indexes and sourcetypes match your ingestion.
• Filters the current rows with `where response_code >= 500` — typically the threshold or rule expression for this monitoring goal.
• `stats` rolls up events into metrics; results are split **by pool_member, response_code, virtual_server** so each row reflects one combination of those dimensions.
• Orders rows with `sort` — combine with `head`/`tail` for top-N patterns.




Optional CIM / accelerated variant (same use case, normalized fields via Common Information Model):

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

Understanding this CIM / accelerated SPL

This block uses `tstats` on the Web data model. Enable data model acceleration for the same dataset in Settings → Data models before you rely on summaries.

**Pipeline walkthrough**

• Uses `tstats` against accelerated summaries for the Web model — enable acceleration and confirm CIM tags on your source data.
• Order and filter as needed for your environment (index-time filters, allowlists, and buckets).

Enable Data Model Acceleration for the model referenced above; otherwise `tstats` may return no results from summaries.



Step 3 — Validate
On the F5 and on the back-end application, confirm the same time window, URL, and five-hundred class responses in Splunk match a known repro.
Step 4 — Operationalize
Add the search to a dashboard or set up alert actions (email, webhook, PagerDuty, etc.) as required. Document the use case in your runbook and assign an owner. Consider visualizations: Bar chart (errors by backend), Table (member, error code, count), Timechart.

## SPL

```spl
index=network sourcetype="f5:bigip:ltm:http"
| where response_code >= 500
| stats count by pool_member, response_code, virtual_server
| sort -count
```

## CIM SPL

```spl
| tstats `summariesonly` count
  from datamodel=Web.Web
  by Web.status Web.url Web.http_method Web.dest span=1h
| sort -count
```

## Visualization

Bar chart (errors by backend), Table (member, error code, count), Timechart.

## References

- [Splunk_TA_f5-bigip](https://splunkbase.splunk.com/app/2680)
- [CIM: Web](https://docs.splunk.com/Documentation/CIM/latest/User/Web)
